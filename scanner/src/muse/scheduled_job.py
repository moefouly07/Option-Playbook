"""SCANNER-V1.1 scheduled job (spec section 13, D-022).

One command per scheduled task, run from a fresh checkout:

  python3 scanner/src/muse/scheduled_job.py --mode official|watch|outcomes|weekly \
      --state ~/workspace/market-scanner/state \
      --accepted-spec-sha S --accepted-impl-ref R

It prints exactly ONE JSON line on stdout:

  {"send": true|false, "status": "...", "title": "...", "body": "..."}

The scheduler posts title and body verbatim when send is true and posts
nothing when send is false. The scheduler itself has no holiday calendar and
no failure alerts, so this job owns both:

- time window per mode (protects against DST or timezone misfires)
- NYSE trading-day check
- every gate (spec, clean tree, implementation manifest)
- a message on every official run, on every failure, on watch state changes
- HALT after 2 consecutive failures: a state/HALT file stops further work
  until a human deletes it

Research only. Messages never contain trade instructions.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import data_adapter as adapter  # noqa: E402
import outcome_tools as outcomes  # noqa: E402
import pipeline_gates as gates  # noqa: E402

REPO = gates.REPO_ROOT
RUNNER = REPO / "scanner" / "src" / "muse" / "run_scan_v11.py"
OUTCOME_TOOL = REPO / "scanner" / "src" / "muse" / "outcome_tools.py"

HALT_AFTER = 2
MIN_FINALIZED_FOR_STATS = 30
CANDIDATE_LABELS = ("CONFIRMED_SETUP", "RESEARCH_PASS")
TITLE_MAX = 120

WINDOWS = {
    "official": lambda t: time(10, 25) <= t.time() < time(11, 30),
    "watch": lambda t: 11 <= t.hour <= 15 and 25 <= t.minute < 50,
    "outcomes": lambda t: time(16, 20) <= t.time() < time(18, 0),
    "weekly": lambda t: t.weekday() == 5,
}


class JobFailure(RuntimeError):
    pass


def out(send: bool, status: str, title: str, body: str = "") -> dict:
    return {"send": send, "status": status, "title": title[:TITLE_MAX], "body": body}


# ------------------------------------------------------------------ state


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def record(state: Path, health: dict, now: datetime, mode: str, status: str,
           detail: str = "") -> None:
    hist = health.setdefault("history", [])
    hist.append({"time": now.isoformat(timespec="seconds"), "mode": mode,
                 "status": status, "detail": detail[:200]})
    health["history"] = hist[-200:]
    health.setdefault("last", {})[mode] = now.isoformat(timespec="seconds")
    save_json(state / "health.json", health)


# ---------------------------------------------------------------- helpers


def run(cmd: List[str], timeout: int = 900) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def tail(text: str, n: int = 300) -> str:
    return adapter._redact(text.strip())[-n:]


def fmt(x, spec: str = ".2f") -> str:
    return "n/a" if x is None else format(x, spec)


def runner_cmd(args, today: str, out_path: Path, log: Path) -> List[str]:
    return [sys.executable, str(RUNNER), "--run-type", "LIVE", "--as-of", today,
            "--accepted-spec-sha", args.accepted_spec_sha,
            "--accepted-impl-ref", args.accepted_impl_ref,
            "--out", str(out_path), "--outcome-log", str(log)]


# ------------------------------------------------------------------ modes


def official(args, state: Path, now: datetime) -> dict:
    today = now.date().isoformat()
    rep_path = state / "reports" / today / "official.json"
    rep_path.parent.mkdir(parents=True, exist_ok=True)
    rc, _, err = run(runner_cmd(args, today, rep_path, state / "outcome_log_live.csv"))
    if rc != 0:
        raise JobFailure(f"runner exit {rc}: {tail(err)}")
    rep = json.loads(rep_path.read_text(encoding="utf-8"))
    sel = rep["selection"]
    by = {r["symbol"]: r for r in rep["results"]}
    head = (f"CANDIDATES: {', '.join(sel['shortlist'])}" if sel["shortlist"]
            else "NO CANDIDATES")
    lines = ["SCANNER-V1.1 LIVE - research only, not trade signals.",
             f"Daily data: session {rep['latest_completed_daily_bar_date']}; "
             f"scan {now.strftime('%H:%M')} ET; intraday SIP delayed >= 20 min."]
    for sym in sel["shortlist"]:
        r, m = by[sym], by[sym]["metrics"]
        lines.append(f"{sym} {r['label']} {r['setup']} pivot {fmt(r['pivot'])} "
                     f"inval {fmt(r['invalidation'])} RS20 {fmt(m.get('rs20_pp'), '+.2f')} "
                     f"RVOL {fmt(m.get('rvol20'))} ext {fmt(m.get('ext_atr'))} "
                     f"| now {r['intraday_status']} @ {fmt(r.get('scan_time_price'))}")
    confirmed = [r["symbol"] for r in rep["results"] if r["label"] == "CONFIRMED_SETUP"]
    lines.append("Confirmed setups: " + (", ".join(confirmed) if confirmed else "none"))
    reg = rep["regime"]
    b50 = reg.get("watchlist_breadth_above_sma50")
    lines.append(f"Regime (recorded only): {reg['label']}, watchlist breadth > SMA50 "
                 f"{fmt(None if b50 is None else b50 * 100, '.0f')}%")
    extra = len(rep["data_quality"]) - 3
    if extra > 0:
        lines.append(f"Data-quality notes: {extra} (see report)")
    lines.append(f"Outcome log: +{rep['outcome_log_rows_written']} rows")
    lines.append(f"spec {rep['spec_commit_sha'][:7]} | impl {rep['implementation_ref'][7:15]}")
    save_json(state / "watch_state.json",
              {"date": today, "shortlist": sel["shortlist"],
               "status": {s: by[s]["intraday_status"] for s in sel["shortlist"]}})
    return out(True, "OK", f"SCANNER {today} - {head}", "\n".join(lines))


def watch(args, state: Path, now: datetime) -> dict:
    today = now.date().isoformat()
    if now.time() >= adapter.session_close_time(now.date()):
        return out(False, "SKIPPED_AFTER_CLOSE", "")
    ws = load_json(state / "watch_state.json", {})
    if ws.get("date") != today:
        if ws.get("no_official_alerted") == today:
            return out(False, "NO_OFFICIAL", "")
        ws["no_official_alerted"] = today
        save_json(state / "watch_state.json", ws)
        return out(True, "NO_OFFICIAL", f"SCANNER {today} - no official report today",
                   "The 10:30 ET official run has not produced a report today, "
                   "so intraday watch has nothing to compare. Check the schedule.")
    rep_path = state / "reports" / today / f"watch_{now.strftime('%H%M')}.json"
    rc, _, err = run(runner_cmd(args, today, rep_path, state / "outcome_log_live.csv"))
    if rc != 0:
        raise JobFailure(f"runner exit {rc}: {tail(err)}")
    rep = json.loads(rep_path.read_text(encoding="utf-8"))
    if rep["selection"]["shortlist"] != ws["shortlist"]:
        raise JobFailure("determinism violation: shortlist changed intraday "
                         f"({ws['shortlist']} -> {rep['selection']['shortlist']})")
    by = {r["symbol"]: r for r in rep["results"]}
    changes = []
    for sym in ws["shortlist"]:
        old, new = ws["status"].get(sym), by[sym]["intraday_status"]
        if new != old:
            changes.append(f"{sym}: {old} -> {new} @ {fmt(by[sym].get('scan_time_price'))} "
                           f"(pivot {fmt(by[sym]['pivot'])}, inval {fmt(by[sym]['invalidation'])})")
            ws["status"][sym] = new
    save_json(state / "watch_state.json", ws)
    if not changes:
        return out(False, "OK_NO_CHANGE", "")
    return out(True, "STATE_CHANGE",
               f"SCANNER {today} {now.strftime('%H:%M')} ET - state change",
               "\n".join(changes + ["Recorded only; SIP data delayed >= 20 min; "
                                    "not a trade signal."]))


def outcomes_mode(args, state: Path, now: datetime) -> dict:
    log = state / "outcome_log_live.csv"
    if not log.is_file():
        return out(False, "NO_LOG", "")
    rc, so, err = run([sys.executable, str(OUTCOME_TOOL), "update", "--log", str(log),
                       "--accepted-spec-sha", args.accepted_spec_sha,
                       "--accepted-impl-ref", args.accepted_impl_ref])
    if rc != 0:
        raise JobFailure(f"outcome update exit {rc}: {tail(err)}")
    res = json.loads(so.strip().splitlines()[-1])
    if res.get("conflicts"):
        return out(True, "OUTCOME_CONFLICTS",
                   f"SCANNER outcomes {now.date()} - {len(res['conflicts'])} vendor conflicts",
                   "\n".join(res["conflicts"][:20] + ["Original values kept."]))
    return out(False, "OK", "")


def _ret(row: Dict[str, str], k: int) -> Optional[float]:
    try:
        return float(row[f"close_p{k}"]) / float(row["scan_time_price"]) - 1.0
    except (ValueError, ZeroDivisionError, KeyError):
        return None


def weekly(args, state: Path, now: datetime, health: dict) -> dict:
    since = now - timedelta(days=7)
    days = []
    for d in sorted((state / "reports").glob("*")):
        try:
            if datetime.fromisoformat(d.name).date() >= since.date():
                days.append(d)
        except ValueError:
            continue
    officials = [d for d in days if (d / "official.json").is_file()]
    events = [e for e in health.get("history", [])
              if datetime.fromisoformat(e["time"]) >= since]
    fails = [e for e in events if e["status"] in ("FAILED", "HALTED")]
    lines = ["SCANNER-V1.1 weekly summary - research only.",
             f"Official reports in the last 7 days: {len(officials)}; "
             f"failures: {len(fails)}; last runs: "
             + ", ".join(f"{k} {v[5:16]}" for k, v in sorted(health.get("last", {}).items()))]
    shortlists = []
    for d in officials:
        rep = load_json(d / "official.json", {})
        sl = rep.get("selection", {}).get("shortlist", [])
        shortlists.append(f"{d.name}: {', '.join(sl) if sl else 'none'}")
    if shortlists:
        lines.append("Shortlists: " + "; ".join(shortlists))
    log = state / "outcome_log_live.csv"
    rows = outcomes.read_log(log)[1] if log.is_file() else []
    cand = [r for r in rows if r["label"] in CANDIDATE_LABELS]
    final = [r for r in cand if r["close_p10"] and r["invalidation_close_session"]
             and r["scan_time_price"]]
    lines.append(f"Outcome log: {len(rows)} rows; candidate rows {len(cand)}; "
                 f"finalized candidate rows {len(final)}.")
    if len(final) < MIN_FINALIZED_FOR_STATS:
        lines.append(f"Performance statistics withheld until "
                     f"{MIN_FINALIZED_FOR_STATS} finalized candidate rows "
                     f"({len(final)}/{MIN_FINALIZED_FOR_STATS}).")
    else:
        base = [r for r in rows if r["label"] == "WATCH" and r["close_p10"]
                and r["scan_time_price"]]
        for name, grp in (("candidates", final), ("WATCH baseline", base)):
            for k in (5, 10):
                vals = [v for v in (_ret(r, k) for r in grp) if v is not None]
                if vals:
                    lines.append(f"{name} +{k}: n {len(vals)}, mean "
                                 f"{statistics.mean(vals) * 100:+.2f}%, median "
                                 f"{statistics.median(vals) * 100:+.2f}%")
        inval = sum(1 for r in final if r["invalidation_close_session"] not in ("NONE", "NA"))
        lines.append(f"Candidates closing below invalidation within 10 sessions: "
                     f"{inval}/{len(final)}. Descriptive only; no edge is claimed.")
    return out(True, "WEEKLY", f"SCANNER weekly {now.date()}", "\n".join(lines))


# ------------------------------------------------------------------- main


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="SCANNER-V1.1 scheduled job")
    ap.add_argument("--mode", required=True, choices=list(WINDOWS))
    ap.add_argument("--state", required=True)
    ap.add_argument("--accepted-spec-sha", required=True)
    ap.add_argument("--accepted-impl-ref", required=True)
    args = ap.parse_args(argv)

    state = Path(args.state).expanduser()
    state.mkdir(parents=True, exist_ok=True)
    now, simulated = gates.now_et(adapter.ET, adapter.SKILL_CLI)
    health = load_json(state / "health.json", {"consecutive_failures": 0})
    mode = args.mode

    def emit(result: dict) -> int:
        if simulated and result["send"]:
            result["body"] = (result["body"] + "\n[SIMULATED CLOCK]").strip()
        print(json.dumps(result))
        return 0

    halt = state / "HALT"
    if halt.is_file():
        reason = halt.read_text(encoding="utf-8").strip()
        send = mode in ("official", "weekly")
        record(state, health, now, mode, "HALTED_SKIP", reason)
        return emit(out(send, "HALTED", "SCANNER HALTED - human action needed",
                        f"{reason}\nFix the cause, then delete {halt} to resume."))

    if not WINDOWS[mode](now):
        record(state, health, now, mode, "SKIPPED_WINDOW", now.isoformat())
        return emit(out(True, "SKIPPED_WINDOW",
                        f"SCANNER {mode} fired outside its ET window",
                        f"Fired at {now.isoformat(timespec='minutes')}; nothing ran. "
                        "Check the schedule timezone (DST)."))

    if mode != "weekly" and not adapter.is_trading_day(now.date()):
        record(state, health, now, mode, "MARKET_CLOSED")
        # weekends are silent; a weekday holiday gets one official message
        return emit(out(mode == "official" and now.weekday() < 5, "MARKET_CLOSED",
                        f"SCANNER {now.date()} - market closed today", "No scan."))

    try:
        gates.check_all(args.accepted_spec_sha, args.accepted_impl_ref)
        if mode == "official":
            result = official(args, state, now)
        elif mode == "watch":
            result = watch(args, state, now)
        elif mode == "outcomes":
            result = outcomes_mode(args, state, now)
        else:
            result = weekly(args, state, now, health)
    except (gates.GateError, JobFailure, outcomes.OutcomeLogError,
            adapter.AdapterError, subprocess.TimeoutExpired, ValueError, KeyError) as exc:
        health["consecutive_failures"] = health.get("consecutive_failures", 0) + 1
        n = health["consecutive_failures"]
        detail = f"{mode}: {type(exc).__name__}: {adapter._redact(str(exc))[:300]}"
        if n >= HALT_AFTER:
            halt.write_text(f"Halted at {now.isoformat(timespec='seconds')} after "
                            f"{n} consecutive failures. Last: {detail}\n", encoding="utf-8")
            record(state, health, now, mode, "HALTED", detail)
            return emit(out(True, "HALTED",
                            f"SCANNER HALTED after {n} consecutive failures",
                            f"{detail}\nDelete {halt} after fixing the cause."))
        record(state, health, now, mode, "FAILED", detail)
        return emit(out(True, "FAILED", f"SCANNER FAILED ({mode})", detail))

    health["consecutive_failures"] = 0
    record(state, health, now, mode, result["status"])
    return emit(result)


if __name__ == "__main__":
    sys.exit(main())
