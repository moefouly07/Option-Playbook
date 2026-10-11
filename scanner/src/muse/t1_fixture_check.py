# Canonical repository copy of Muse's T1 fixture harness (test only, not a
# scan). Transcribed from the T1b chat export on 2026-10-11 with whitespace
# restored; logic unchanged. See D-019.
"""T1 step 2-4: run MY SCANNER-V1.1 implementation on the synthetic golden
fixtures and diff field-by-field against
scanner/tests/fixtures/expected_output.json.

Run from the repository root (Windows, macOS, Linux):
    python scanner/src/muse/t1_fixture_check.py

All paths are resolved relative to this file's location inside the repo
(scanner/src/muse/), so the working directory does not matter.
Exit 0 = all compared fields match. Exit 1 = any mismatch (FAIL).

No network, no credentials, no trading. Fixture CSVs are synthetic.
"""
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# scanner/src/muse/<this file> -> repository root
REPO_ROOT = HERE.parents[2]
FIX = REPO_ROOT / "scanner" / "tests" / "fixtures"
BARS = FIX / "bars"
EXPECTED_PATH = FIX / "expected_output.json"

if not FIX.is_dir():
    sys.exit(f"FAIL: fixtures directory not found at {FIX} "
             f"(repo root resolved to {REPO_ROOT})")

import scanner_v11 as v11  # noqa: E402

EXPECTED = json.load(open(EXPECTED_PATH, encoding="utf-8"))

REL_TOL = 1e-9


def load_bars(path: Path):
    bars = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            bars.append({
                "date": row["date"],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
    return bars


def close_enough(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=REL_TOL, abs_tol=0.0)
    return a == b


def main():
    symbols = sorted(p.stem for p in BARS.glob("*.csv"))
    bars_by_symbol = {s: load_bars(BARS / f"{s}.csv") for s in symbols}
    bench = bars_by_symbol["SPY"]

    results = [v11.classify(s, bars_by_symbol[s], bench) for s in symbols]
    mine = {r.symbol: r.as_dict() for r in results}
    sel = v11.select(results, bars_by_symbol)

    exp_results = {r["symbol"]: r for r in EXPECTED["results"]}

    diffs = []  # (symbol, field, expected, mine)
    scalar_fields = ["label", "setup", "triggered", "failed", "flags",
                     "reason", "pivot", "invalidation"]
    for sym in symbols:
        e, m = exp_results[sym], mine[sym]
        for f in scalar_fields:
            if not close_enough(e[f], m[f]):
                diffs.append((sym, f, e[f], m[f]))
        for k in e["metrics"]:
            if not close_enough(e["metrics"][k], m["metrics"].get(k)):
                diffs.append((sym, f"metrics.{k}", e["metrics"][k], m["metrics"].get(k)))
        for k in m["metrics"]:
            if k not in e["metrics"]:
                diffs.append((sym, f"metrics.{k}", "<absent>", m["metrics"][k]))

    # selection
    esel = EXPECTED["selection"]
    for f in ["verdict", "shortlist"]:
        if esel[f] != sel[f]:
            diffs.append(("<selection>", f, esel[f], sel[f]))
    if esel["skipped_for_correlation"] != sel["skipped_for_correlation"]:
        diffs.append(("<selection>", "skipped_for_correlation",
                      esel["skipped_for_correlation"], sel["skipped_for_correlation"]))
    ecl, mcl = esel["correlation_log"], sel["correlation_log"]
    if len(ecl) != len(mcl):
        diffs.append(("<selection>", "correlation_log.len", len(ecl), len(mcl)))
    else:
        for i, (e, m) in enumerate(zip(ecl, mcl)):
            for f in ["pair", "n", "first", "last", "method", "r"]:
                if not close_enough(e[f], m[f]):
                    diffs.append(("<selection>", f"correlation_log[{i}].{f}", e[f], m[f]))

    # regime (informational; not in the T1 field list)
    my_regime = v11.regime(bars_by_symbol)
    exp_regime = EXPECTED.get("regime", {})
    regime_diffs = [(k, exp_regime.get(k), my_regime.get(k))
                    for k in set(exp_regime) | set(my_regime)
                    if not close_enough(exp_regime.get(k), my_regime.get(k))]

    print("=" * 100)
    print("T1 FIXTURE DIFF TABLE — my implementation vs expected_output.json")
    print("=" * 100)
    print(f"{'symbol':<14}{'field':<34}{'expected':<26}{'mine'}")
    print("-" * 100)
    if not diffs:
        print("NO DIFFERENCES in compared fields.")
    for sym, field, e, m in diffs:
        print(f"{sym:<14}{field:<34}{str(e)[:25]:<26}{str(m)[:40]}")
    print("-" * 100)
    print(f"symbols compared: {len(symbols)} | field diffs: {len(diffs)}")
    if regime_diffs:
        print("regime (informational):")
        for k, e, m in regime_diffs:
            print(f"  {k}: expected={e} mine={m}")
    else:
        print("regime: identical")

    impl_path = HERE / "scanner_v11.py"
    impl_ref = hashlib.sha256(_lf_bytes(impl_path)).hexdigest()
    print(f"implementation_ref (sha256 of scanner_v11.py): {impl_ref}")

    exp_short = esel["shortlist"]
    print(f"expected shortlist: {exp_short} | mine: {sel['shortlist']}")
    print("RESULT:", "PASS" if not diffs else "FAIL")
    return 0 if not diffs else 1


def _lf_bytes(path: Path) -> bytes:
    """UTF-8 bytes with LF line endings (normalizes CRLF)."""
    return path.read_bytes().replace(b"\r\n", b"\n")


if __name__ == "__main__":
    sys.exit(main())
