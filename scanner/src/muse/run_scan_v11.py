# Canonical repository copy. Base: Muse T1c export (run_scan_v11.py, sha256 7016fa88ed7a4004...),
# decoded byte-exact and reviewed. Review fixes applied per DECISION_LOG D-021.
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
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import data_adapter as adapter  # noqa: E402
import scanner_v11 as v11  # noqa: E402

ET = adapter.ET
REPO_ROOT = HERE.parents[2]  # scanner/src/muse/<this file> -> repo root

UNIVERSE = ["SPY", "QQQ", "IWM", "SMH", "XLK", "XLF", "XLE", "XLI",
            "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
            "AMD", "MU", "AVGO", "MRVL", "PLTR", "QCOM"]
UNIVERSE_SOURCE = "fixed pilot watchlist (scanner/SCANNER_V1_1_SPEC.md)"

EXECUTED_FILES = [
    "scanner/src/muse/run_scan_v11.py",
    "scanner/src/muse/data_adapter.py",
    "scanner/src/muse/scanner_v11.py",
    "scanner/tools/implementation_ref.py",
]

SPEC_FILES = ["scanner/SCANNER_V1_1_SPEC.md", "scanner/OUTPUT_SCHEMA.json"]

CALENDAR_SOURCE = ("NYSE rule-based calendar (data_adapter.py): holidays "
                   "and 13:00 early closes; ad-hoc closures not modeled")


class Refusal(RuntimeError):
    """The run must not proceed; nothing was fetched or written."""


# ------------------------------------------------------------ spec SHA gate


def spec_commit_sha(repo_root: Path) -> Optional[str]:
    if not (repo_root / "scanner" / "SCANNER_V1_1_SPEC.md").is_file():
        return None
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "log", "-1", "--format=%H", "--",
             *SPEC_FILES],
            capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip().lower()
    return sha if re.fullmatch(r"[0-9a-f]{40}", sha) else None


def uncommitted_scanner_changes(repo_root: Path) -> Optional[List[str]]:
    """Tracked files under scanner/ with uncommitted changes (None = unknown)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain",
             "--untracked-files=no", "--", "scanner"],
            capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def sha_accepted(actual: str, accepted: str) -> bool:
    accepted = accepted.strip().lower()
    if len(accepted) < 7 or not re.fullmatch(r"[0-9a-f]+", accepted):
        return False
    return actual == accepted or actual.startswith(accepted)


# ------------------------------------------------------- implementation_ref


def _load_impl_ref_tool(repo_root: Path):
    path = repo_root / "scanner" / "tools" / "implementation_ref.py"
    spec = importlib.util.spec_from_file_location("implementation_ref", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def implementation_manifest(repo_root: Path):
    """(implementation_files, implementation_ref) per D-019."""
    tool = _load_impl_ref_tool(repo_root)
    entries, lines = [], []
    for rel in EXECUTED_FILES:
        h = tool.file_sha256(repo_root / rel)
        entries.append({"path": rel, "sha256": h})
        lines.append(f"{rel}  {h}\n")
    lines.sort()
    entries.sort(key=lambda e: e["path"])
    ref = "sha256:" + hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
    return entries, ref


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
                    impl_files: list, impl_ref: str) -> dict:
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
        f"spec_commit_sha={spec_commit_sha(REPO_ROOT)}",
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
        "spec_commit_sha": spec_commit_sha(REPO_ROOT),
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


OUTCOME_HEADER = ["run_type", "scan_started_at_et",
                  "latest_completed_daily_bar_date", "symbol", "label",
                  "setup", "pivot", "invalidation", "reference_close",
                  "close_p1", "close_p5", "close_p10",
                  "invalidation_hit_first"]


def outcome_rows_to_write(path: Path, report: dict) -> List[list]:
    """Rows for this run, minus any (session, symbol) already logged.

    One row per symbol per completed session: a repeated run on the same
    session (e.g. the T4b repeatability check) appends nothing.
    """
    seen = set()
    if path.is_file():
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                seen.add((row["latest_completed_daily_bar_date"], row["symbol"]))
    rows = []
    for r in report["results"]:
        key = (report["latest_completed_daily_bar_date"], r["symbol"])
        if key in seen:
            continue
        rows.append([report["run_type"], report["scan_started_at_et"],
                     report["latest_completed_daily_bar_date"], r["symbol"],
                     r["label"], r["setup"], r["pivot"], r["invalidation"],
                     r["metrics"].get("close"), "", "", "", ""])
    return rows


def append_outcome_log(path: Path, rows: List[list]) -> int:
    """Append outcome-log rows (spec section 11); create the file if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.is_file()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(OUTCOME_HEADER)
        for row in rows:
            w.writerow(row)
    return len(rows)


# --------------------------------------------------------------------- main


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
        now_et = datetime.now(ET)
        try:
            as_of = date.fromisoformat(args.as_of)
        except ValueError:
            raise Refusal(f"--as-of is not a valid date: {args.as_of}")

        # --- spec SHA gate: before any data is fetched
        actual_sha = spec_commit_sha(REPO_ROOT)
        if actual_sha is None:
            raise Refusal(
                "cannot read the spec commit SHA (no git checkout or no "
                f"scanner/SCANNER_V1_1_SPEC.md under {REPO_ROOT})")
        if not sha_accepted(actual_sha, args.accepted_spec_sha):
            raise Refusal(
                f"spec commit SHA mismatch: spec/schema last changed in "
                f"{actual_sha}, accepted is {args.accepted_spec_sha}. A spec "
                "change needs a new acceptance pass; refusing to run.")

        # --- clean-tree gate: the code that runs is the code that was committed
        dirty = uncommitted_scanner_changes(REPO_ROOT)
        if dirty is None:
            raise Refusal("cannot read git status for scanner/")
        if dirty:
            raise Refusal("uncommitted changes under scanner/: "
                          + "; ".join(dirty[:5]))

        # --- date/run-type gate
        if args.run_type == "LIVE":
            if as_of != now_et.date():
                raise Refusal(
                    f"LIVE runs require --as-of = today ET "
                    f"({now_et.date().isoformat()}), got {as_of}")
            latest_completed = adapter.latest_completed_session(now_et)
        else:  # IN_SAMPLE_REPLAY
            if as_of > now_et.date():
                raise Refusal("IN_SAMPLE_REPLAY --as-of is in the future")
            if not adapter.is_trading_day(as_of):
                raise Refusal(f"IN_SAMPLE_REPLAY --as-of {as_of} is not "
                              "an NYSE trading day")
            latest_completed = as_of

        impl_files, impl_ref = implementation_manifest(REPO_ROOT)
        if impl_ref != args.accepted_impl_ref.strip().lower():
            raise Refusal(f"implementation_ref mismatch: code is {impl_ref}, "
                          f"accepted is {args.accepted_impl_ref}")

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
                                 impl_files, impl_ref)
        report["data_quality"].extend(integrity_notes)

        # --- intraday status for shortlisted names (recorded only)
        if args.run_type == "LIVE" and adapter.is_trading_day(now_et.date()):
            intra_session = now_et.date()
        else:
            intra_session = latest_completed
        by_symbol = {r["symbol"]: r for r in report["results"]}
        latest_5m_ts: Optional[str] = None
        for sym in report["selection"]["shortlist"]:
            entry = by_symbol[sym]
            try:
                bars5 = adapter.fetch_intraday_5m(sym, intra_session, now_et)
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

        # --- outcome log row count is deterministic (one row per
        # result); set it before validation so the validated document
        # is exactly the document that gets written.
        default_log = ("outcome_log_live.csv" if args.run_type == "LIVE"
                       else "outcome_log_replay.csv")
        log_path = (Path(args.outcome_log) if args.outcome_log
                    else REPO_ROOT / "scanner" / "runs" / default_log)
        new_rows = outcome_rows_to_write(log_path, report)
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

        written = append_outcome_log(log_path, new_rows)
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
