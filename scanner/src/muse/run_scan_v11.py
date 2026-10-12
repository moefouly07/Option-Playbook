# Canonical repository copy. Base: Muse T1c export (run_scan_v11.py, sha256 7016fa88ed7a4004...),
# decoded byte-exact and reviewed. Review fixes applied per DECISION_LOG D-021;
# shared gates, outcome module, KI-001/002/003 and scan_time_price per D-022;
# latest available session per D-023 (KI-004).
"""SCANNER-V1.1 single entry point (Muse workspace copy).

Usage (from the repository root):

    python scanner/src/muse/run_scan_v11.py \
        --run-type LIVE|IN_SAMPLE_REPLAY \
        --as-of YYYY-MM-DD \
        --accepted-spec-sha <last commit that changed the spec or schema> \
        --accepted-impl-ref sha256:<accepted implementation manifest>

Behaviour (refusals happen before any market data is fetched):
- spec_commit_sha is the last commit that changed SCANNER_V1_1_SPEC.md or
  OUTPUT_SCHEMA.json (git log -1 -- <files>), so unrelated commits such as
  acceptance-log updates do not move it. The run REFUSES if it differs
  from --accepted-spec-sha.
- The run REFUSES if any tracked file under scanner/ has uncommitted
  changes, or if the implementation manifest (D-019) differs from
  --accepted-impl-ref.
- A LIVE run REFUSES on a non-trading day (KI-002).
- In LIVE runs every symbol gets scan_time_price: the close of the last
  complete SIP 5-minute bar ending at or before scan time - 20 min.
- After fetching, the run REFUSES if SPY's latest completed bar is not the
  expected session (stale or missing vendor data, or an unmodeled market
  closure). Other symbols with stale or malformed bars become
  INSUFFICIENT_DATA and are named in data_quality.
- Classification, ranking, selection, correlation, and regime come ONLY
  from scanner_v11.py (the committed SCANNER-V1.1 rules engine).
  Market data comes only from data_adapter.py (read-only skill CLI).
- Emits a JSON report that is validated against
  scanner/OUTPUT_SCHEMA.json before it is written. A report that fails
  validation is not written.
- implementation_files / implementation_ref follow D-019: sha256 of
  every executed file (UTF-8, LF) and the manifest hash computed the
  same way as scanner/tools/implementation_ref.py.
- No raw vendor bars are written anywhere. No credentials are read,
  stored, or printed. No order, trading, position, or account endpoint
  is referenced.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import data_adapter as adapter  # noqa: E402
import outcome_tools as outcomes  # noqa: E402
import pipeline_gates as gates  # noqa: E402
import scanner_v11 as v11  # noqa: E402

ET = adapter.ET
REPO_ROOT = HERE.parents[2]  # scanner/src/muse/<this file> -> repo root

UNIVERSE = ["SPY", "QQQ", "IWM", "SMH", "XLK", "XLF", "XLE", "XLI",
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
            "AMD", "MU", "AVGO", "MRVL", "PLTR", "QCOM"]
UNIVERSE_SOURCE = "fixed pilot watchlist (scanner/SCANNER_V1_1_SPEC.md)"

CALENDAR_SOURCE = ("NYSE rule-based calendar (data_adapter.py): holidays "
                   "and 13:00 early closes; ad-hoc closures not modeled")


class Refusal(RuntimeError):
    """The run must not proceed; nothing was fetched or written."""


# --------------------------------------------------------- schema validation
# Minimal validator covering exactly the JSON-Schema keywords used by
# scanner/OUTPUT_SCHEMA.json (type incl. unions, required, properties,
# items, minItems, maxItems, const, enum, pattern, not). `format` is an
# annotation in JSON Schema and is not enforced.


def _type_ok(value, t: str) -> bool:
    if t == "object":
        return isinstance(value, dict)
    if t == "array":
        return isinstance(value, list)
    if t == "string":
        return isinstance(value, str)
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if t == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == "boolean":
        return isinstance(value, bool)
    if t == "null":
        return value is None
    return True


def validate(instance, schema, path: str = "$",
             errors: Optional[List[str]] = None) -> List[str]:
    if errors is None:
        errors = []
    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_type_ok(instance, tt) for tt in types):
            errors.append(f"{path}: expected type {t}, "
                          f"got {type(instance).__name__}")
            return errors
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, "
                      f"got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum {schema['enum']}")
    if "pattern" in schema and isinstance(instance, str):
        if not re.search(schema["pattern"], instance):
            errors.append(f"{path}: {instance!r} fails pattern "
                          f"{schema['pattern']}")
    if "not" in schema:
        probe: List[str] = []
        validate(instance, schema["not"], path, probe)
        if not probe:
            errors.append(f"{path}: matches a forbidden schema")
    if isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errors.append(f"{path}: missing required property '{req}'")
        for key, sub in schema.get("properties", {}).items():
            if key in instance:
                validate(instance[key], sub, f"{path}.{key}", errors)
    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: {len(instance)} items < "
                          f"minItems {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: {len(instance)} items > "
                          f"maxItems {schema['maxItems']}")
        items = schema.get("items")
        if isinstance(items, dict):
            for i, item in enumerate(instance):
                validate(item, items, f"{path}[{i}]", errors)
    return errors


# ------------------------------------------------------------ report builder


def market_session_label(now_et: datetime) -> str:
    d, t = now_et.date(), now_et.time()
    if not adapter.is_trading_day(d):
        return "CLOSED"
    if t < time(9, 30):
        return "PREMARKET"
    if t < adapter.session_close_time(d):
        return "EARLY_CLOSE_DAY" if adapter.is_early_close(d) else "REGULAR"
    if t < time(20, 0):
        return "AFTER_HOURS"
    return "CLOSED"


def intraday_status(last_close: Optional[float],
                    pivot: Optional[float],
                    invalidation: Optional[float]) -> str:
    if last_close is None or pivot is None or invalidation is None:
        return "NOT_AVAILABLE"
    if last_close > pivot:
        return "ABOVE_PIVOT"
    if last_close < invalidation:
        return "BELOW_INVALIDATION"
    return "BETWEEN_PIVOT_AND_INVALIDATION"


def assemble_report(run_type: str, as_of: date, latest_completed: date,
                    now_et: datetime, bars_by_symbol: Dict[str, List[dict]],
                    impl_files: list, impl_ref: str, spec_sha: str) -> dict:
    bench = bars_by_symbol.get("SPY", [])
    results_objs = [v11.classify(sym, bars_by_symbol.get(sym, []), bench)
                    for sym in UNIVERSE]
    selection = v11.select(results_objs, bars_by_symbol)
    reg = v11.regime(bars_by_symbol)

    results = []
    for r in results_objs:
        entry = r.as_dict()
        entry["factor_tag"] = v11.FACTOR_TAGS.get(r.symbol, "unknown")
        entry["earnings"] = {
            "next_date": None,
            "source": None,
            "status": "EARNINGS_DATE_UNVERIFIED",
            "event_risk": False,
        }
        entry["intraday_status"] = None
        entry["scan_time_price"] = None
        entry["scan_time_bar_et"] = None
        entry["catalysts"] = []
        results.append(entry)

    labels = [r.label for r in results_objs]
    data_quality = [
        "daily bars: consolidated SIP, adjustment=split, completed only; "
        "in-progress session dropped by calendar + vendor completeness flag",
        "intraday bars: SIP 5-minute, end = now - 20 minutes, RTH only; "
        "recorded only",
        "no raw vendor bars are stored in this report",
    ]
    for sym in UNIVERSE:
        n = len(bars_by_symbol.get(sym, []))
        if n < int(v11.PARAMS["min_daily_bars"]):
            data_quality.append(
                f"{sym}: only {n} completed daily bars "
                f"(< {int(v11.PARAMS['min_daily_bars'])})")

    audit_notes = [
        f"spec_commit_sha={spec_sha}",
        "rules imported only from scanner_v11.py (SCANNER-V1.1); data "
        "only via data_adapter.py (read-only alpaca-market-data skill CLI)",
        "regime, RSI flag, catalysts, earnings proximity, intraday "
        "status are RECORDED ONLY and never change a label in V1.1",
        "catalysts: none collected by this pipeline; the recorded-only "
        "field is an empty list, not evidence of no news",
        "earnings: EARNINGS_DATE_UNVERIFIED for every symbol; this "
        "pipeline performs no primary-source earnings lookup",
        "options: OPTIONS_NOT_VERIFIED for every symbol",
    ]
    if run_type == "IN_SAMPLE_REPLAY":
        audit_notes.append(
            "IN_SAMPLE_REPLAY: the 2026-10-09 data is in-sample for "
            "V1.1 (D-009); this run is not evidence for V1.1")

    is_td = adapter.is_trading_day(as_of)
    cal_notes = (f"as_of {as_of.isoformat()} is "
                 f"{'a trading day' if is_td else 'NOT a trading day'}; "
                 f"latest completed daily session: "
                 f"{latest_completed.isoformat()}")
    if adapter.is_early_close(as_of):
        cal_notes += "; early close 13:00 ET"

    return {
        "spec_version": v11.SPEC_VERSION,
        "spec_commit_sha": spec_sha,
        "implementation_ref": impl_ref,
        "implementation_files": impl_files,
        "run_type": run_type,
        "scan_started_at_et": now_et.isoformat(timespec="seconds"),
        "market_session": market_session_label(now_et),
        "calendar_check": {
            "source": CALENDAR_SOURCE,
            "is_trading_day": is_td,
            "notes": cal_notes,
        },
        "latest_completed_daily_bar_date": latest_completed.isoformat(),
        "latest_completed_sip_5m_bar_et": None,
        "data_sources": {
            "daily_bars": adapter.daily_source_string(),
            "intraday_bars": adapter.intraday_source_string(),
            "quotes": adapter.quotes_source_string(),
        },
        "universe": {
            "universe_source": UNIVERSE_SOURCE,
            "universe_count": 21,
            "eligible_count": 20,
            "processed_count": len(results),
            "rejected_count": labels.count(v11.REJECT),
            "insufficient_count": labels.count(v11.INSUFFICIENT_DATA),
            "benchmark": "SPY",
        },
        "regime": reg,
        "results": results,
        "selection": selection,
        "options_status": "OPTIONS_NOT_VERIFIED",
        "outcome_log_rows_written": 0,
        "data_quality": data_quality,
        "audit_notes": audit_notes,
    }


# --------------------------------------------------------------------- main


def _scan_time_prices(report: dict, session, now_et: datetime) -> Optional[str]:
    """Fill scan_time_price for every symbol and intraday_status for the
    shortlist from the same complete SIP 5-minute bars (recorded only).
    Returns the latest bar start used (ET), or None."""
    shortlist = set(report["selection"]["shortlist"])
    latest: Optional[str] = None
    missing = []
    for entry in report["results"]:
        sym = entry["symbol"]
        try:
            bars5 = adapter.fetch_intraday_5m(sym, session, now_et)
        except adapter.AdapterError:
            bars5 = []
        if bars5:
            last = bars5[-1]
            entry["scan_time_price"] = last["close"]
            entry["scan_time_bar_et"] = last["t_et"]
            if latest is None or last["t_et"] > latest:
                latest = last["t_et"]
        else:
            missing.append(sym)
        if sym in shortlist:
            entry["intraday_status"] = (
                intraday_status(bars5[-1]["close"], entry["pivot"], entry["invalidation"])
                if bars5 else "NOT_AVAILABLE")
    if missing:
        report["data_quality"].append(
            "scan_time_price unavailable (no complete 5-minute bar yet or "
            "fetch failed): " + ", ".join(missing))
    return latest


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="SCANNER-V1.1 scan (research only; no execution)")
    ap.add_argument("--run-type", required=True,
                    choices=["LIVE", "IN_SAMPLE_REPLAY"])
    ap.add_argument("--as-of", required=True,
                    help="reference date YYYY-MM-DD (ET)")
    ap.add_argument("--accepted-spec-sha", required=True,
                    help="accepted spec commit SHA (last commit that changed "
                         "the spec or schema); the run refuses if it differs")
    ap.add_argument("--accepted-impl-ref", required=True,
                    help="accepted implementation manifest (sha256:...); "
                         "the run refuses if the code differs")
    ap.add_argument("--out", default=None,
                    help="write the JSON report here (default: stdout)")
    ap.add_argument("--outcome-log", default=None,
                    help="outcome log CSV path (default: scanner/runs/"
                         "outcome_log_live.csv or outcome_log_replay.csv; "
                         "scanner/runs/ is git-ignored)")
    args = ap.parse_args(argv)

    try:
        now_et, simulated = gates.now_et(ET, adapter.SKILL_CLI)
        try:
            as_of = date.fromisoformat(args.as_of)
        except ValueError:
            raise Refusal(f"--as-of is not a valid date: {args.as_of}")

        # --- spec, clean-tree and implementation gates: before any fetch
        try:
            actual_sha, impl_files, impl_ref = gates.check_all(
                args.accepted_spec_sha, args.accepted_impl_ref, REPO_ROOT)
        except gates.GateError as exc:
            raise Refusal(str(exc))

        # --- date/run-type gate
        if args.run_type == "LIVE":
            if as_of != now_et.date():
                raise Refusal(
                    f"LIVE runs require --as-of = today ET "
                    f"({now_et.date().isoformat()}), got {as_of}")
            if not adapter.is_trading_day(now_et.date()):
                raise Refusal(f"LIVE run refused: {now_et.date()} is not an "
                              "NYSE trading day (KI-002)")
            latest_completed = adapter.latest_available_session(now_et)
        else:  # IN_SAMPLE_REPLAY
            if as_of > now_et.date():
                raise Refusal("IN_SAMPLE_REPLAY --as-of is in the future")
            if not adapter.is_trading_day(as_of):
                raise Refusal(f"IN_SAMPLE_REPLAY --as-of {as_of} is not "
                              "an NYSE trading day")
            latest_completed = as_of

        # --- outcome log must be usable before anything is fetched (KI-001)
        default_log = ("outcome_log_live.csv" if args.run_type == "LIVE"
                       else "outcome_log_replay.csv")
        log_path = (Path(args.outcome_log) if args.outcome_log
                    else REPO_ROOT / "scanner" / "runs" / default_log)
        try:
            outcomes.check_header(log_path)
        except outcomes.OutcomeLogError as exc:
            raise Refusal(str(exc))

        # --- data (read-only skill CLI via data_adapter)
        try:
            bars_by_symbol = adapter.fetch_daily_bars(UNIVERSE,
                                                      latest_completed)
        except adapter.AdapterError as exc:
            raise Refusal(f"daily data fetch failed: {exc}")

        # --- data integrity and freshness gate
        integrity_notes: List[str] = []
        for sym in UNIVERSE:
            bars = bars_by_symbol.get(sym, [])
            issue = adapter.daily_bar_issue(bars)
            if issue:
                if sym == "SPY":
                    raise Refusal(f"SPY daily bars failed integrity check: {issue}")
                integrity_notes.append(f"{sym}: excluded, {issue}")
                bars_by_symbol[sym] = []
        spy = bars_by_symbol.get("SPY", [])
        expected = latest_completed.isoformat()
        if not spy or spy[-1]["date"] != expected:
            got = spy[-1]["date"] if spy else "no bars"
            raise Refusal(f"stale or missing data: SPY latest completed bar is "
                          f"{got}, expected {expected}")
        for sym in UNIVERSE:
            bars = bars_by_symbol.get(sym, [])
            if bars and bars[-1]["date"] != expected:
                integrity_notes.append(f"{sym}: latest completed bar "
                                       f"{bars[-1]['date']}, expected {expected}")

        report = assemble_report(args.run_type, as_of, latest_completed,
                                 now_et, bars_by_symbol,
                                 impl_files, impl_ref, actual_sha)
        report["data_quality"].extend(integrity_notes)
        if simulated:
            report["audit_notes"].append("SIMULATED CLOCK (pipeline_sim only)")

        # --- intraday (recorded only): LIVE uses today's session and fills
        # scan_time_price for every symbol; a replay records the shortlist's
        # status against the replayed session only.
        if args.run_type == "LIVE":
            report["latest_completed_sip_5m_bar_et"] = _scan_time_prices(
                report, now_et.date(), now_et)
        else:
            by_symbol = {r["symbol"]: r for r in report["results"]}
            latest_5m_ts: Optional[str] = None
            for sym in report["selection"]["shortlist"]:
                entry = by_symbol[sym]
                try:
                    bars5 = adapter.fetch_intraday_5m(sym, latest_completed, now_et)
                except adapter.AdapterError:
                    bars5 = []
                if bars5:
                    last = bars5[-1]
                    entry["intraday_status"] = intraday_status(
                        last["close"], entry["pivot"], entry["invalidation"])
                    if latest_5m_ts is None or last["t_et"] > latest_5m_ts:
                        latest_5m_ts = last["t_et"]
                else:
                    entry["intraday_status"] = "NOT_AVAILABLE"
            report["latest_completed_sip_5m_bar_et"] = latest_5m_ts

        # --- outcome rows are fixed before validation so the validated
        # document is exactly the document that gets written.
        try:
            new_rows = outcomes.rows_for_report(log_path, report)
        except outcomes.OutcomeLogError as exc:
            raise Refusal(str(exc))
        report["outcome_log_rows_written"] = len(new_rows)

        # --- schema gate: an invalid report is never written, and the
        # outcome log is only appended for a report that passed.
        schema_path = REPO_ROOT / "scanner" / "OUTPUT_SCHEMA.json"
        if not schema_path.is_file():
            raise Refusal(f"output schema not found at {schema_path}")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        errors = validate(report, schema)
        if errors:
            for e in errors[:20]:
                print(f"SCHEMA ERROR: {e}", file=sys.stderr)
            print("REFUSED: report failed schema validation; "
                  "nothing written.", file=sys.stderr)
            return 3

        written = outcomes.append(log_path, new_rows)
        if written != report["outcome_log_rows_written"]:
            print("ERROR: outcome log row count mismatch; report not "
                  "written.", file=sys.stderr)
            return 3

        text = json.dumps(report, indent=2, allow_nan=False)
        if args.out:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        sel = report["selection"]
        print(f"{report['run_type']} as_of={as_of} "
              f"latest_completed={latest_completed} "
              f"verdict={sel['verdict']} shortlist={sel['shortlist']} "
              f"spec_commit_sha={actual_sha}", file=sys.stderr)
        return 0
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
