"""
End-to-end simulation of the SCANNER-V1.1 pipeline (T1c and T7 gates).

Runs the committed entry points in a throw-away local clone against a FAKE
skill CLI that serves synthetic fixture bars, with a simulated clock that is
honoured only because the CLI lives in scanner/tests/. No network, no vendor
data, no effect on the real repository. From the repository root:

    python scanner/tests/pipeline_sim/run_pipeline_sim.py

The working-tree scanner/ directory is copied into the clone and committed
there, so this works both before and after files are committed.
Exit 0 = every scenario behaved as required.
"""
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
AS_OF = "2026-10-09"
LIVE_NOW = "2026-10-12T11:31:41-04:00"

CLOSED_2026 = ["2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25",
               "2026-06-19", "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25"]
OPEN_2026 = ["2026-10-12", "2026-11-11", "2026-11-27", "2026-12-24", "2026-07-02"]
EARLY_2026 = ["2026-11-27", "2026-12-24"]


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, check=True).stdout.strip()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="scanner_sim_"))
    repo = tmp / "repo"
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    try:
        subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(ROOT), str(repo)],
                       check=True)
        shutil.rmtree(repo / "scanner")
        shutil.copytree(ROOT / "scanner", repo / "scanner",
                        ignore=shutil.ignore_patterns("__pycache__", "runs"))
        git(repo, "add", "-A")
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=sim", "-c",
                        "user.email=sim@local", "commit", "-q", "--allow-empty",
                        "-m", "sim snapshot"], check=True)

        muse = repo / "scanner" / "src" / "muse"
        runner, job, otool = muse / "run_scan_v11.py", muse / "scheduled_job.py", muse / "outcome_tools.py"
        adapter = load_module(muse / "data_adapter.py", "sim_adapter")
        gates = load_module(muse / "pipeline_gates.py", "sim_gates")
        tool = load_module(repo / "scanner/tools/implementation_ref.py", "sim_ref")
        ref_rules = load_module(repo / "scanner/reference/scanner_rules.py", "sim_ref_rules")
        os.environ["FAKE_REPO"] = str(repo)
        fake = load_module(HERE / "fake_skill_cli.py", "sim_fake")

        bad = [d for d in CLOSED_2026 if adapter.is_trading_day(date.fromisoformat(d))]
        bad += [d for d in OPEN_2026 if not adapter.is_trading_day(date.fromisoformat(d))]
        bad += [d for d in EARLY_2026 if not adapter.is_early_close(date.fromisoformat(d))]
        check("S0 NYSE 2026 calendar", not bad, ", ".join(bad))

        lines = sorted(f"{p}  {tool.file_sha256(repo / p)}\n" for p in gates.PIPELINE_FILES)
        impl_ref = "sha256:" + hashlib.sha256("".join(lines).encode()).hexdigest()
        spec_sha = git(repo, "log", "-1", "--format=%H", "--", *gates.SPEC_FILES)
        fake_cli = repo / "scanner" / "tests" / "pipeline_sim" / "fake_skill_cli.py"
        base_env = dict(os.environ, ALPACA_SKILL_CLI=str(fake_cli), FAKE_REPO=str(repo))

        def env(scenario="normal", now=None):
            e = dict(base_env, FAKE_SCENARIO=scenario)
            e.pop("SCANNER_SIM_NOW", None)
            if now:
                e["SCANNER_SIM_NOW"] = now
            return e

        def scan(*, scenario="normal", spec=None, impl=None, run_type="IN_SAMPLE_REPLAY",
                 as_of=AS_OF, out="report.json", log="log.csv", now=None):
            o = tmp / out
            o.unlink(missing_ok=True)
            cmd = [sys.executable, str(runner), "--run-type", run_type, "--as-of", as_of,
                   "--accepted-spec-sha", spec or spec_sha,
                   "--accepted-impl-ref", impl or impl_ref,
                   "--out", str(o), "--outcome-log", str(tmp / log)]
            p = subprocess.run(cmd, capture_output=True, text=True, env=env(scenario, now), cwd=repo)
            rep = json.loads(o.read_text()) if p.returncode == 0 and o.is_file() else None
            return p.returncode, p.stderr, rep

        def sched(mode, now, state, spec=None):
            cmd = [sys.executable, str(job), "--mode", mode, "--state", str(tmp / state),
                   "--accepted-spec-sha", spec or spec_sha, "--accepted-impl-ref", impl_ref]
            p = subprocess.run(cmd, capture_output=True, text=True, env=env(now=now), cwd=repo)
            try:
                return json.loads(p.stdout.strip().splitlines()[-1]), p.stderr
            except Exception:
                return {"status": "CRASH", "send": None, "title": "", "body": ""}, p.stderr

        def otools(cmd, log, now):
            p = subprocess.run([sys.executable, str(otool), cmd, "--log", str(tmp / log),
                                "--accepted-spec-sha", spec_sha, "--accepted-impl-ref", impl_ref],
                               capture_output=True, text=True, env=env(now=now), cwd=repo)
            try:
                return p.returncode, json.loads(p.stdout.strip().splitlines()[-1]), p.stderr
            except Exception:
                return p.returncode, {}, p.stderr

        def rows(log):
            if not (tmp / log).is_file():
                return []
            with open(tmp / log, newline="") as f:
                return list(csv.DictReader(f))

        # ---------------- replay (T1c scenarios)
        p = subprocess.run([sys.executable, str(fake_cli), "--symbols",
                            ",".join(fake.MAP), "--feed", "sip", "--timeframe", "1Day",
                            "--bars", "130", "--end", AS_OF],
                           capture_output=True, text=True, env=env(), check=True)
        data = json.loads(p.stdout)["symbols"]
        bars = {s: [ref_rules.Bar(b["t_et"][:10], float(b["o"]), float(b["h"]),
                                  float(b["l"]), float(b["c"]), float(b["v"]))
                    for b in node["bars"]] for s, node in data.items()}
        ref_res = [ref_rules.classify(s, bars[s], bars["SPY"]) for s in bars]
        exp_labels = {r.symbol: r.label for r in ref_res}
        exp_short = ref_rules.select(ref_res, bars)["shortlist"]

        code, err, rep = scan()
        got = {r["symbol"]: r["label"] for r in rep["results"]} if rep else {}
        check("S1 replay runs, labels == reference", code == 0 and got == exp_labels,
              f"exit {code} {err.strip()[-160:]}")
        check("S1 shortlist == reference", rep is not None and rep["selection"]["shortlist"] == exp_short,
              str(rep and rep["selection"]["shortlist"]))
        check("S1 report fields", rep is not None and rep["implementation_ref"] == impl_ref
              and rep["spec_commit_sha"] == spec_sha and rep["outcome_log_rows_written"] == 21
              and len(rep["implementation_files"]) == len(gates.PIPELINE_FILES), "")
        code, err, rep = scan()
        check("S2 repeat run appends nothing", code == 0 and rep["outcome_log_rows_written"] == 0
              and len(rows("log.csv")) == 21, "")
        code, err, _ = scan(spec="0" * 40)
        check("S3 wrong spec SHA refused", code == 2, err.strip()[-120:])
        code, err, _ = scan(impl="sha256:" + "0" * 64)
        check("S4 wrong implementation_ref refused", code == 2, err.strip()[-120:])
        code, err, _ = scan(scenario="stale_all", log="l3.csv")
        check("S5 stale SPY refused", code == 2 and "stale" in err, err.strip()[-120:])
        code, err, rep = scan(scenario="stale_one", log="l4.csv")
        mu = rep and next(r for r in rep["results"] if r["symbol"] == "MU")
        check("S6 stale MU -> INSUFFICIENT_DATA + noted", code == 0 and mu["label"] == "INSUFFICIENT_DATA"
              and any(x.startswith("MU:") for x in rep["data_quality"]), err.strip()[-120:])
        code, err, rep = scan(scenario="dup_date", log="l5.csv")
        aapl = rep and next(r for r in rep["results"] if r["symbol"] == "AAPL")
        check("S7 duplicate date -> excluded + noted", code == 0 and aapl["label"] == "INSUFFICIENT_DATA"
              and any(x.startswith("AAPL: excluded") for x in rep["data_quality"]), err.strip()[-120:])
        code, err, _ = scan(run_type="LIVE", as_of="2026-10-09", log="l6.csv", now=LIVE_NOW)
        check("S8 LIVE with past --as-of refused", code == 2, err.strip()[-120:])

        # ---------------- LIVE with simulated clock (D-022)
        code, err, live = scan(run_type="LIVE", as_of="2026-10-12", log="live.csv",
                               out="live.json", now=LIVE_NOW)
        lab = {r["symbol"]: r["label"] for r in live["results"]} if live else {}
        check("S11 LIVE labels identical to replay", code == 0 and lab == exp_labels
              and live["latest_completed_daily_bar_date"] == AS_OF, err.strip()[-160:])
        bars_et = {r.get("scan_time_bar_et") for r in live["results"]} if live else set()
        check("S12 scan_time_price for all 21, last bar provably complete (KI-003)",
              live is not None and all(r["scan_time_price"] is not None for r in live["results"])
              and bars_et == {"2026-10-12T11:05:00-04:00"}, str(bars_et))
        lr = rows("live.csv")
        shutil.copy(tmp / "live.csv", tmp / "lag.csv")
        check("S13 live outcome rows carry scan_time_price", len(lr) == 21
              and all(r["scan_time_price"] for r in lr), "")
        code, err, _ = scan(run_type="LIVE", as_of="2026-10-10", log="l7.csv",
                            now="2026-10-10T11:00:00-04:00")
        check("S14 LIVE on a non-trading day refused (KI-002)", code == 2 and "trading day" in err,
              err.strip()[-120:])
        legacy = ("run_type,scan_started_at_et,latest_completed_daily_bar_date,symbol,label,setup,"
                  "pivot,invalidation,reference_close,close_p1,close_p5,close_p10,invalidation_hit_first\n"
                  "LIVE,2026-10-12T11:31:41-04:00,2026-10-09,AAPL,CONFIRMED_SETUP,BREAKOUT_20D,1,1,1,,,,\n"
                  "LIVE,2026-10-12T11:31:41-04:00,2026-10-09,MSFT,CONFIRMED_SETUP,PULLBACK_TO_SMA20,1,1,1,,,,\n")
        (tmp / "legacy.csv").write_text(legacy)
        code, err, _ = scan(run_type="LIVE", as_of="2026-10-12", log="legacy.csv",
                            out="x.json", now=LIVE_NOW)
        check("S15 legacy header refused cleanly (KI-001)", code == 2 and "migrate" in err,
              err.strip()[-120:])
        code, res, err = otools("migrate", "legacy.csv", LIVE_NOW)
        mig = rows("legacy.csv")
        live_px = {r["symbol"]: r["scan_time_price"] for r in live["results"]} if live else {}
        check("S16 migrate backfills scan_time_price deterministically",
              code == 0 and res.get("backfilled") == 2 and
              all(float(r["scan_time_price"]) == live_px[r["symbol"]] for r in mig), err.strip()[-120:])

        # ---------------- data-plan model and fill lag (D-023, KI-004)
        p = subprocess.run([sys.executable, str(fake_cli), "--symbols", "SPY", "--feed", "sip",
                            "--timeframe", "1Day", "--bars", "5", "--end", "2026-10-12"],
                           capture_output=True, text=True, env=env(now="2026-10-12T16:31:00-04:00"))
        check("S28 plan model refuses a same-day daily request", p.returncode != 0 and "403" in p.stdout,
              p.stdout[:120])
        code, res, err = otools("update", "lag.csv", "2026-10-12T16:31:00-04:00")
        check("S29 same-evening update succeeds and fills no close yet",
              code == 0 and all(r["close_p1"] == "" for r in rows("lag.csv")), f"{res} {err.strip()[-160:]}")
        code, res, err = otools("update", "lag.csv", "2026-10-13T09:15:00-04:00")
        lag = {r["symbol"]: r for r in rows("lag.csv")}
        aapl_1012 = {b["date"].isoformat(): b["c"] for b in fake.series("AAPL")}["2026-10-12"]
        check("S30 next-morning update fills day T close", code == 0 and lag["AAPL"]["close_p1"] != ""
              and float(lag["AAPL"]["close_p1"]) == aapl_1012, f"{res} {err.strip()[-160:]}")
        code, err, rep = scan(run_type="LIVE", as_of="2026-10-12", log="l11.csv", out="after.json",
                              now="2026-10-12T16:31:00-04:00")
        lab = {r["symbol"]: r["label"] for r in rep["results"]} if rep else {}
        check("S31 LIVE after the close uses the latest fetchable session", code == 0
              and rep["latest_completed_daily_bar_date"] == AS_OF and lab == exp_labels, err.strip()[-160:])

        # ---------------- outcome update
        code, res, err = otools("update", "live.csv", "2026-10-27T17:00:00-04:00")
        up = {r["symbol"]: r for r in rows("live.csv")}
        full = {s: {b["date"].isoformat(): b["c"] for b in fake.series(s)} for s in ("AAPL", "SPY")}
        try:
            ok_closes = (float(up["AAPL"]["close_p1"]) == full["AAPL"]["2026-10-12"]
                         and float(up["AAPL"]["close_p5"]) == full["AAPL"]["2026-10-16"]
                         and float(up["AAPL"]["close_p10"]) == full["AAPL"]["2026-10-23"])
        except ValueError:
            ok_closes = False
        ics = {r["invalidation_close_session"] for r in up.values()}
        check("S17 outcome update fills p1/p5/p10 by session count", code == 0 and ok_closes,
              f"{res} {err.strip()[-300:]}")
        check("S18 invalidation_close_session in {1..10, NONE, NA}, SPY NA",
              ics <= {str(i) for i in range(1, 11)} | {"NONE", "NA"}
              and up["SPY"]["invalidation_close_session"] == "NA", str(ics))
        code, res2, err = otools("update", "live.csv", "2026-10-27T17:00:00-04:00")
        check("S19 second update fills nothing", code == 0 and res2.get("filled") == 0
              and not res2.get("conflicts"), str(res2))
        txt = (tmp / "live.csv").read_text()
        (tmp / "live.csv").write_text(txt.replace(up["AAPL"]["close_p1"], "1.0", 1))
        code, res3, err = otools("update", "live.csv", "2026-10-27T17:00:00-04:00")
        check("S20 vendor disagreement reported, original kept", code == 0
              and len(res3.get("conflicts", [])) == 1 and rows("live.csv")[8]["close_p1"] == "1.0",
              str(res3)[:160])

        # ---------------- scheduled job (D-022, spec section 13)
        o, _ = sched("official", "2026-10-12T10:31:00-04:00", "st")
        check("S21 official run messages and logs", o["status"] == "OK" and o["send"] is True
              and "2026-10-12" in o["title"] and len(rows("st/outcome_log_live.csv")) == 21,
              f"{o['status']} {o['title']} {o['body'][:200]}")
        w, _ = sched("watch", "2026-10-12T11:31:00-04:00", "st")
        check("S22 watch runs, no new log rows", w["status"] in ("OK_NO_CHANGE", "STATE_CHANGE")
              and len(rows("st/outcome_log_live.csv")) == 21, w["status"])
        o, _ = sched("official", "2026-10-12T09:00:00-04:00", "st")
        check("S23 outside ET window -> alert, nothing run", o["status"] == "SKIPPED_WINDOW"
              and o["send"] is True, o["status"])
        o, _ = sched("official", "2026-11-26T10:31:00-05:00", "st")
        w, _ = sched("watch", "2026-11-26T11:31:00-05:00", "st")
        check("S24 holiday: official says closed, watch silent", o["status"] == "MARKET_CLOSED"
              and o["send"] is True and w["status"] == "MARKET_CLOSED" and w["send"] is False,
              f"{o['status']} {w['status']}")
        oc, _ = sched("outcomes", "2026-10-28T09:15:00-04:00", "st")
        st_rows = rows("st/outcome_log_live.csv")
        check("S25 outcomes job fills the log silently", oc["status"] == "OK" and oc["send"] is False
              and bool(st_rows) and all(r["close_p10"] for r in st_rows), f"{oc['status']} {oc['body'][:200]}")
        wk, _ = sched("weekly", "2026-10-17T10:00:00-04:00", "st")
        check("S26 weekly summary withholds statistics below 30 rows", wk["status"] == "WEEKLY"
              and "withheld" in wk["body"], wk["status"])
        f1, _ = sched("official", "2026-10-13T10:31:00-04:00", "st2", spec="0" * 40)
        f2, _ = sched("official", "2026-10-14T10:31:00-04:00", "st2", spec="0" * 40)
        f3, _ = sched("official", "2026-10-15T10:31:00-04:00", "st2")
        check("S27 two failures -> HALT; halted runs stay halted",
              f1["status"] == "FAILED" and f2["status"] == "HALTED" and f3["status"] == "HALTED"
              and (tmp / "st2" / "HALT").is_file(), f"{f1['status']} {f2['status']} {f3['status']}")

        (repo / "NOTES.md").write_text("unrelated\n")
        git(repo, "add", "NOTES.md")
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=sim", "-c", "user.email=sim@local",
                        "commit", "-q", "-m", "unrelated"], check=True)
        code, err, _ = scan(log="l9.csv")
        check("S9 unrelated commit does not block", code == 0, err.strip()[-120:])
        rules = muse / "scanner_v11.py"
        rules.write_text(rules.read_text().replace('"zone_atr_mult": 0.5', '"zone_atr_mult": 0.9'))
        code, err, _ = scan(log="l10.csv")
        check("S10 uncommitted rule change refused", code == 2, err.strip()[-120:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {'' if ok else detail}")
    failed = sum(not ok for _, ok, _ in results)
    print(f"{len(results) - failed}/{len(results)} scenarios passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
