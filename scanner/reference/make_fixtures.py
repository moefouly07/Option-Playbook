"""
Generate SYNTHETIC golden fixtures for SCANNER-V1.1.

These are not market data. Dates are in the year 2099 on purpose so no one
mistakes them for real prices. Each symbol is engineered to hit one specific
rule path. The committed CSV files are the source of truth; this script only
documents how they were produced.

Usage (from repository root):
    python3 scanner/reference/make_fixtures.py
"""
from __future__ import annotations

import csv
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scanner_rules as sr  # noqa: E402

OUT = HERE.parent / "tests" / "fixtures"
N = 90

# Designed intent. The test suite checks the reference implementation
# against THIS table, not just against its own previous output.
INTENDED = {
    "SPY": sr.BENCHMARK_ONLY,
    "QQQ": sr.WATCH,
    "BRKC": sr.CONFIRMED_SETUP,     # clean 20-day breakout, moderate extension
    "BRKE": sr.RESEARCH_PASS,       # breakout capped by EXTENDED (2-3 ATR)
    "BRKX": sr.WATCH,               # breakout blocked by OVEREXTENDED (>3 ATR)
    "PULC": sr.CONFIRMED_SETUP,     # pullback to SMA20 zone with reversal
    "TWIN": sr.CONFIRMED_SETUP,     # near-copy of PULC -> dropped for correlation
    "PULR": sr.RESEARCH_PASS,       # pullback structure, no reversal
    "PULN": sr.WATCH,               # pullback structure, RS not positive
    "DOWN": sr.WATCH,               # downtrend, no setup
    "CHEAP": sr.REJECT,             # price below 10
    "THIN": sr.REJECT,              # dollar volume below 50M
    "SHORT": sr.INSUFFICIENT_DATA,  # fewer than 70 completed bars
    "STALE": sr.INSUFFICIENT_DATA,  # last bar date differs from benchmark
}
INTENDED_SHORTLIST = ["BRKC", "PULC", "BRKE"]


def weekdays(n: int, end: date = date(2099, 6, 30)) -> list[str]:
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return out[::-1]


DATES = weekdays(N)


def path(start: float, drifts: list[float], vol: float, seed: int) -> list[float]:
    rng = random.Random(seed)
    closes, c = [], start
    for d in drifts:
        c *= 1.0 + d + rng.gauss(0.0, vol)
        closes.append(c)
    return closes


def bars_from_closes(closes, seed, base_vol=5_000_000, wick=0.004):
    rng = random.Random(seed + 1000)
    out, prev = [], closes[0] * 0.998
    for i, c in enumerate(closes):
        o = prev * (1.0 + rng.gauss(0.0, 0.002))
        hi = max(o, c) * (1.0 + abs(rng.gauss(0.0, wick)))
        lo = min(o, c) * (1.0 - abs(rng.gauss(0.0, wick)))
        v = base_vol * (1.0 + 0.15 * rng.uniform(-1, 1))
        out.append([DATES[i], o, hi, lo, c, v])
        prev = c
    return out


def set_last(rows, o=None, h=None, l=None, c=None, v_mult=None, idx=-1):
    r = rows[idx]
    if o is not None: r[1] = o
    if c is not None: r[4] = c
    if h is not None: r[2] = h
    if l is not None: r[3] = l
    r[2] = max(r[2], r[1], r[4])
    r[3] = min(r[3], r[1], r[4])
    if v_mult is not None:
        base = sum(x[5] for x in rows[idx - 20:idx]) / 20
        r[5] = base * v_mult


def build() -> dict[str, list[list]]:
    U: dict[str, list[list]] = {}

    U["SPY"] = bars_from_closes(path(500, [0.0005] * N, 0.006, 1), 1, 80_000_000)
    U["QQQ"] = bars_from_closes(path(420, [0.0004] * N, 0.008, 2), 2, 40_000_000)

    # BRKC: trend, 20-bar flat base, close just above base high on 2x volume
    dr = [0.003] * 60 + [0.0] * 29 + [0.0]
    rows = bars_from_closes(path(100, dr, 0.006, 3), 3)
    ph = max(r[2] for r in rows[-21:-1])
    set_last(rows, o=ph * 0.995, c=ph * 1.004, h=ph * 1.006, l=ph * 0.993, v_mult=2.2)
    U["BRKC"] = rows

    # BRKE: steadier advance -> extension 2-3 ATR at breakout
    dr = [0.002] * 60 + [0.004] * 30
    rows = bars_from_closes(path(80, dr, 0.006, 4), 4)
    ph = max(r[2] for r in rows[-21:-1])
    set_last(rows, o=ph * 0.997, c=ph * 1.010, h=ph * 1.011, l=ph * 0.995, v_mult=1.9)
    U["BRKE"] = rows

    # BRKX: very steep, low-noise run -> extension > 3 ATR
    dr = [0.002] * 60 + [0.012] * 30
    rows = bars_from_closes(path(60, dr, 0.003, 5), 5, wick=0.002)
    ph = max(r[2] for r in rows[-21:-1])
    set_last(rows, o=ph * 0.999, c=ph * 1.015, h=ph * 1.016, l=ph * 0.998, v_mult=2.0)
    U["BRKX"] = rows

    # PULC: uptrend, 6-bar dip into SMA20 zone, reversal bar
    dr = [0.004] * 80 + [-0.006] * 9 + [0.0]
    rows = bars_from_closes(path(150, dr, 0.005, 6), 6)
    closes = [r[4] for r in rows]
    s20 = sum(closes[-20:-1] + [closes[-2]]) / 20
    set_last(rows, o=s20 * 0.995, c=s20 * 1.012, h=s20 * 1.014, l=s20 * 0.993, v_mult=1.1)
    U["PULC"] = rows

    # TWIN: PULC scaled by a slowly decaying factor with tiny noise
    rng = random.Random(77)
    twin = []
    for i, r in enumerate(U["PULC"]):
        f = 0.6 * (1.0 - 0.0004 * i) * (1.0 + rng.gauss(0.0, 0.0015))
        twin.append([r[0], r[1] * f, r[2] * f, r[3] * f, r[4] * f, r[5] * 1.3])
    U["TWIN"] = twin

    # PULR: same shape as PULC (different seed) but last bar closes weak
    dr = [0.004] * 80 + [-0.006] * 9 + [0.0]
    rows = bars_from_closes(path(120, dr, 0.005, 8), 8)
    closes = [r[4] for r in rows]
    s20 = sum(closes[-20:]) / 20
    set_last(rows, o=s20 * 1.004, c=s20 * 0.997, h=s20 * 1.006, l=s20 * 0.993, v_mult=1.0)
    U["PULR"] = rows

    # PULN: strong earlier, flat-to-soft last ~25 bars -> RS20 <= 0
    dr = [0.0] * 20 + [0.008] * 50 + [-0.003] * 19 + [0.0]
    rows = bars_from_closes(path(90, dr, 0.004, 9), 9)
    closes = [r[4] for r in rows]
    s20 = sum(closes[-20:]) / 20
    set_last(rows, o=s20 * 0.997, c=s20 * 1.006, h=s20 * 1.008, l=s20 * 0.995, v_mult=1.0)
    U["PULN"] = rows

    U["DOWN"] = bars_from_closes(path(200, [-0.003] * N, 0.008, 10), 10)
    U["CHEAP"] = bars_from_closes(path(6, [0.002] * N, 0.01, 11), 11, 20_000_000)
    U["THIN"] = bars_from_closes(path(50, [0.002] * N, 0.01, 12), 12, 300_000)
    U["SHORT"] = bars_from_closes(path(70, [0.002] * N, 0.01, 13), 13)[-40:]
    U["STALE"] = bars_from_closes(path(70, [0.002] * N, 0.01, 14), 14)[:-1]
    return U


def write_csv(sym: str, rows) -> None:
    p = OUT / "bars" / f"{sym}.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["date", "open", "high", "low", "close", "volume"])
        for r in rows:
            w.writerow([r[0], f"{r[1]:.4f}", f"{r[2]:.4f}", f"{r[3]:.4f}",
                        f"{r[4]:.4f}", f"{int(round(r[5]))}"])


def load(sym: str) -> list[sr.Bar]:
    with (OUT / "bars" / f"{sym}.csv").open() as fh:
        return [sr.Bar(r["date"], float(r["open"]), float(r["high"]),
                       float(r["low"]), float(r["close"]), float(r["volume"]))
                for r in csv.DictReader(fh)]


def evaluate(symbols):
    bars = {s: load(s) for s in symbols}
    bench = bars[sr.BENCHMARK]
    results = [sr.classify(s, bars[s], bench) for s in symbols]
    selection = sr.select(results, bars)
    return bars, results, selection


def main() -> None:
    U = build()
    for sym, rows in U.items():
        write_csv(sym, rows)
    symbols = sorted(U)
    bars, results, selection = evaluate(symbols)

    bad = [(r.symbol, r.label, INTENDED[r.symbol], r.reason)
           for r in results if r.label != INTENDED[r.symbol]]
    if bad or selection["shortlist"] != INTENDED_SHORTLIST:
        for b in bad:
            print("MISMATCH", b)
        print("shortlist", selection["shortlist"])
        raise SystemExit("fixtures do not match designed intent; adjust generator")

    expected = {
        "spec_version": sr.SPEC_VERSION,
        "note": "SYNTHETIC fixtures. Not market data.",
        "benchmark": sr.BENCHMARK,
        "results": [r.as_dict() for r in results],
        "selection": selection,
        "regime": sr.regime(bars),
    }
    (OUT / "expected_output.json").write_text(json.dumps(expected, indent=2))
    print("ok:", len(results), "symbols; shortlist", selection["shortlist"])


if __name__ == "__main__":
    main()
