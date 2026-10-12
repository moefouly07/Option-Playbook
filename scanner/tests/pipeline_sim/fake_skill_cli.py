"""
Fake read-only alpaca-market-data skill CLI for the pipeline simulation.

Serves the SYNTHETIC golden-fixture bars re-dated onto real NYSE sessions
ending at the anchor session 2026-10-09, followed by a deterministic
synthetic continuation, in the same JSON shape the real CLI returns. 5Min
requests get synthetic RTH and extended-hours bars, including a bar that
starts before but ends after the request end (to exercise KI-003). Never
touches the network. Scenarios (env FAKE_SCENARIO):
  normal          every symbol complete through --end
  stale_all       every symbol is missing the --end session
  stale_one       only MU is missing the --end session
  dup_date        AAPL has a duplicated session date
"""
import argparse
import csv
import json
import math
import os
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

REPO = Path(os.environ["FAKE_REPO"])
sys.path.insert(0, str(REPO / "scanner" / "src" / "muse"))
import data_adapter as A  # noqa: E402  (calendar only)

FIX = REPO / "scanner" / "tests" / "fixtures" / "bars"
ANCHOR = date(2026, 10, 9)
HORIZON = date(2026, 12, 31)
MAP = {
    "SPY": "SPY", "QQQ": "QQQ", "IWM": "DOWN", "SMH": "BRKE", "XLK": "BRKX",
    "XLF": "CHEAP", "XLE": "PULR", "XLI": "XLI", "AAPL": "BRKC", "MSFT": "PULC",
    "NVDA": "GAPF", "AMZN": "PULN", "GOOGL": "ZERO", "META": "PULV",
    "TSLA": "BRKS", "AMD": "BRKO", "MU": "THIN", "AVGO": "DOWN", "MRVL": "PULR",
    "PLTR": "BRKE", "QCOM": "BARS60",
}


def sessions_back(n, end):
    out, d = [], end
    while len(out) < n:
        if A.is_trading_day(d):
            out.append(d)
        d = A.previous_trading_day(d)
    return out[::-1]


def series(sym):
    """Full deterministic daily series: fixtures up to ANCHOR, then continuation."""
    rows = list(csv.DictReader(open(FIX / f"{MAP[sym]}.csv")))
    ds = sessions_back(len(rows), ANCHOR)
    bars = [{"date": d, "o": float(r["open"]), "h": float(r["high"]), "l": float(r["low"]),
             "c": float(r["close"]), "v": float(r["volume"])} for d, r in zip(ds, rows)]
    rng = random.Random(sum(map(ord, sym)))
    c, d, i = bars[-1]["c"], ANCHOR, 0
    while d < HORIZON:
        d += timedelta(days=1)
        if not A.is_trading_day(d):
            continue
        i += 1
        o = c * (1 + rng.gauss(0, 0.003))
        c = o * (1 + 0.01 * math.sin(i + len(sym)) + rng.gauss(0, 0.004))
        bars.append({"date": d, "o": o, "h": max(o, c) * 1.004, "l": min(o, c) * 0.996,
                     "c": c, "v": bars[-1]["v"]})
    return bars


def intraday(day_bar):
    """78 RTH 5-minute bars plus two extended-hours bars for one session."""
    d = day_bar["date"]
    close_t = A.session_close_time(d)
    n = (datetime.combine(d, close_t) - datetime.combine(d, time(9, 30))).seconds // 300
    out = [{"t": datetime.combine(d, time(8, 0), tzinfo=A.ET), "p": day_bar["o"]}]
    for k in range(n):
        frac = (k + 1) / n
        p = day_bar["o"] + (day_bar["c"] - day_bar["o"]) * frac
        out.append({"t": datetime.combine(d, time(9, 30), tzinfo=A.ET) + timedelta(minutes=5 * k),
                    "p": p})
    out.append({"t": datetime.combine(d, close_t, tzinfo=A.ET) + timedelta(minutes=5),
                "p": day_bar["c"]})
    return [{"t_et": b["t"].isoformat(), "o": b["p"], "h": b["p"] * 1.0005,
             "l": b["p"] * 0.9995, "c": b["p"], "v": 1000.0, "complete": True} for b in out]


def main():
    ap = argparse.ArgumentParser()
    for a in ("--symbols", "--feed", "--timeframe", "--end", "--start", "--adjustment"):
        ap.add_argument(a)
    ap.add_argument("--bars", type=int)
    a = ap.parse_args()
    if a.feed != "sip":
        print(json.dumps({"ok": False, "error": "non-SIP feed requested"}))
        return
    scenario = os.environ.get("FAKE_SCENARIO", "normal")
    out = {"ok": True, "symbols": {}}
    for sym in a.symbols.split(","):
        full = series(sym)
        if a.timeframe == "5Min":
            end_dt = datetime.fromisoformat(a.end)
            day = end_dt.astimezone(A.ET).date()
            day_bar = next((b for b in full if b["date"] == day), None)
            bars = [] if day_bar is None else [
                b for b in intraday(day_bar) if datetime.fromisoformat(b["t_et"]) <= end_dt]
            out["symbols"][sym] = {"bars": bars[-a.bars:]}
            continue
        end = date.fromisoformat(a.end[:10])
        sel = [b for b in full if b["date"] <= end]
        bars = [{"t_et": f"{b['date'].isoformat()}T00:00:00-04:00", "o": b["o"], "h": b["h"],
                 "l": b["l"], "c": b["c"], "v": b["v"], "complete": True} for b in sel]
        if scenario == "stale_all" or (scenario == "stale_one" and sym == "MU"):
            bars = bars[:-1]
        if scenario == "dup_date" and sym == "AAPL":
            bars[-5]["t_et"] = bars[-6]["t_et"]
        out["symbols"][sym] = {"bars": bars[-a.bars:]}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
