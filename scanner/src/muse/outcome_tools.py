"""SCANNER-V1.1 outcome log (spec section 11, D-022).

One row per (completed daily session, symbol). Columns:

  run_type, scan_started_at_et, latest_completed_daily_bar_date, symbol,
  label, setup, pivot, invalidation, reference_close,
  scan_time_price, scan_time_bar_et,
  close_p1, close_p5, close_p10, invalidation_close_session

Definitions (pre-registered before any outcome was observed):
- scan_time_price: close of the last COMPLETE consolidated SIP 5-minute RTH
  bar whose end is at or before (scan_started_at_et - 20 min), same session
  as the scan. Blank when no such bar exists (e.g. a scan before 09:55 ET).
- close_pK: close of the K-th completed session whose close time is after
  scan_started_at_et (a 10:30 ET scan counts its own session as K = 1).
- invalidation_close_session: first K in 1..10 whose close is strictly below
  the row's invalidation; "NONE" once 10 sessions are observed without one;
  "NA" for rows without an invalidation level; blank while pending.
- Filled values are never overwritten. A later disagreement with vendor
  data is reported as a conflict and the original value is kept.

Commands (from the repository root; both run every gate first):
  python scanner/src/muse/outcome_tools.py update  --log PATH --accepted-spec-sha S --accepted-impl-ref R
  python scanner/src/muse/outcome_tools.py migrate --log PATH --accepted-spec-sha S --accepted-impl-ref R

Standard library only. Data only through data_adapter.py. No trading.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import data_adapter as adapter  # noqa: E402
import pipeline_gates as gates  # noqa: E402

OUTCOME_HEADER = ["run_type", "scan_started_at_et",
                  "latest_completed_daily_bar_date", "symbol", "label",
                  "setup", "pivot", "invalidation", "reference_close",
                  "scan_time_price", "scan_time_bar_et",
                  "close_p1", "close_p5", "close_p10",
                  "invalidation_close_session"]

LEGACY_HEADER_13 = ["run_type", "scan_started_at_et",
                    "latest_completed_daily_bar_date", "symbol", "label",
                    "setup", "pivot", "invalidation", "reference_close",
                    "close_p1", "close_p5", "close_p10",
                    "invalidation_hit_first"]

HORIZONS = (1, 5, 10)
MAX_SESSIONS = 10


class OutcomeLogError(RuntimeError):
    """The outcome log cannot be used safely; nothing was written."""


def _fmt(x) -> str:
    return "" if x is None else repr(float(x))


def read_log(path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], []
        rows = [dict(zip(header, r)) for r in reader if r]
    return header, rows


def check_header(path: Path) -> None:
    """Refuse cleanly (KI-001) if an existing log has an unexpected header."""
    if not path.is_file():
        return
    header, _ = read_log(path)
    if header == OUTCOME_HEADER:
        return
    if header == LEGACY_HEADER_13:
        raise OutcomeLogError(f"{path} uses the legacy 13-column header; run "
                              "outcome_tools.py migrate first")
    raise OutcomeLogError(f"{path} has an unexpected header; refusing to append")


def rows_for_report(path: Path, report: dict) -> List[list]:
    """Rows for this run, minus any (session, symbol) already logged."""
    check_header(path)
    seen = set()
    if path.is_file():
        for row in read_log(path)[1]:
            seen.add((row["latest_completed_daily_bar_date"], row["symbol"]))
    out = []
    session = report["latest_completed_daily_bar_date"]
    for r in report["results"]:
        if (session, r["symbol"]) in seen:
            continue
        out.append([report["run_type"], report["scan_started_at_et"], session,
                    r["symbol"], r["label"], r["setup"] or "",
                    _fmt(r["pivot"]), _fmt(r["invalidation"]),
                    _fmt(r["metrics"].get("close")),
                    _fmt(r.get("scan_time_price")), r.get("scan_time_bar_et") or "",
                    "", "", "", ""])
    return out


def append(path: Path, rows: List[list]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.is_file()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(OUTCOME_HEADER)
        for row in rows:
            w.writerow(row)
    return len(rows)


def _write_atomic(path: Path, header: List[str], rows: List[Dict[str, str]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow([r.get(k, "") for k in header])
    os.replace(tmp, path)


def scan_price_at(symbol: str, scan_started: datetime) -> Tuple[Optional[float], Optional[str]]:
    """scan_time_price and its bar start (ET) for a scan at scan_started."""
    bars = adapter.fetch_intraday_5m(symbol, scan_started.date(), scan_started)
    if not bars:
        return None, None
    return bars[-1]["close"], bars[-1]["t_et"]


def migrate(path: Path) -> Dict[str, int]:
    """Legacy 13-column log -> current header; backfill scan_time_price."""
    header, rows = read_log(path)
    if header == OUTCOME_HEADER:
        return {"migrated": 0, "backfilled": 0}
    if header != LEGACY_HEADER_13:
        raise OutcomeLogError(f"{path}: unknown header, cannot migrate")
    out, backfilled, cache = [], 0, {}
    for r in rows:
        if r.get("invalidation_hit_first", ""):
            raise OutcomeLogError("legacy invalidation_hit_first is filled; "
                                  "refusing to reinterpret it")
        new = {k: r.get(k, "") for k in OUTCOME_HEADER}
        new["scan_time_price"] = new["scan_time_bar_et"] = ""
        if r["run_type"] == "LIVE":
            key = (r["symbol"], r["scan_started_at_et"])
            if key not in cache:
                cache[key] = scan_price_at(r["symbol"],
                                           datetime.fromisoformat(r["scan_started_at_et"]))
            price, bar_et = cache[key]
            if price is not None:
                new["scan_time_price"], new["scan_time_bar_et"] = _fmt(price), bar_et
                backfilled += 1
        out.append(new)
    _write_atomic(path, OUTCOME_HEADER, out)
    return {"migrated": len(out), "backfilled": backfilled}


def closes_after(bars: List[dict], scan_started: datetime) -> List[float]:
    """Closes of completed sessions whose close time is after scan_started."""
    out = []
    for b in bars:
        d = date.fromisoformat(b["date"])
        close_dt = datetime.combine(d, adapter.session_close_time(d), tzinfo=adapter.ET)
        if close_dt > scan_started:
            out.append(b["close"])
    return out[:MAX_SESSIONS]


def compute_fields(row: Dict[str, str], closes: List[float]) -> Dict[str, str]:
    vals: Dict[str, str] = {}
    for k in HORIZONS:
        if len(closes) >= k:
            vals[f"close_p{k}"] = _fmt(closes[k - 1])
    inv = row.get("invalidation", "")
    if inv == "":
        vals["invalidation_close_session"] = "NA"
    else:
        level = float(inv)
        hit = next((i + 1 for i, c in enumerate(closes) if c < level), None)
        if hit is not None:
            vals["invalidation_close_session"] = str(hit)
        elif len(closes) >= MAX_SESSIONS:
            vals["invalidation_close_session"] = "NONE"
    return vals


def update(path: Path, now: datetime) -> Dict[str, object]:
    """Fill pending fields from completed daily bars; never overwrite."""
    header, rows = read_log(path)
    if header != OUTCOME_HEADER:
        raise OutcomeLogError(f"{path}: header is not current; migrate first")
    if not rows:
        return {"filled": 0, "conflicts": [], "pending_rows": 0}
    symbols = sorted({r["symbol"] for r in rows})
    end = adapter.latest_completed_session(now)
    bars = adapter.fetch_daily_bars(symbols, end)
    filled, conflicts, pending = 0, [], 0
    for r in rows:
        scan = datetime.fromisoformat(r["scan_started_at_et"])
        computed = compute_fields(r, closes_after(bars.get(r["symbol"], []), scan))
        for k, v in computed.items():
            if r.get(k, "") == "":
                r[k] = v
                filled += 1
            elif r[k] != v:
                conflicts.append(f"{r['latest_completed_daily_bar_date']} {r['symbol']} "
                                 f"{k}: kept {r[k]}, vendor now {v}")
        if r.get("close_p10", "") == "" or r.get("invalidation_close_session", "") == "":
            pending += 1
    _write_atomic(path, OUTCOME_HEADER, rows)
    return {"filled": filled, "conflicts": conflicts, "pending_rows": pending}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="SCANNER-V1.1 outcome log tools")
    ap.add_argument("command", choices=["update", "migrate"])
    ap.add_argument("--log", required=True)
    ap.add_argument("--accepted-spec-sha", required=True)
    ap.add_argument("--accepted-impl-ref", required=True)
    args = ap.parse_args(argv)
    try:
        gates.check_all(args.accepted_spec_sha, args.accepted_impl_ref)
        now, simulated = gates.now_et(adapter.ET, adapter.SKILL_CLI)
        path = Path(args.log)
        if not path.is_file():
            raise OutcomeLogError(f"{path} does not exist")
        result = migrate(path) if args.command == "migrate" else update(path, now)
        result["simulated_clock"] = simulated
        print(json.dumps(result))
        return 0
    except (gates.GateError, OutcomeLogError, adapter.AdapterError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
