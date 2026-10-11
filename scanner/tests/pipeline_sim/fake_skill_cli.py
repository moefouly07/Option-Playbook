"""
Fake read-only alpaca-market-data skill CLI for the pipeline simulation.

Serves the SYNTHETIC golden-fixture bars re-dated onto real NYSE sessions
ending at --end, in the same JSON shape the real CLI returns. Never touches
the network. Scenarios (env FAKE_SCENARIO):
  normal          every symbol complete through --end
  stale_all       every symbol is missing the --end session
  stale_one       only MU is missing the --end session
  dup_date        AAPL has a duplicated session date
"""
import argparse
import csv
import json
import os
import sys
from datetime import date
from pathlib import Path

REPO = Path(os.environ["FAKE_REPO"])
sys.path.insert(0, str(REPO / "scanner" / "src" / "muse"))
import data_adapter as A  # noqa: E402  (calendar only)

FIX = REPO / "scanner" / "tests" / "fixtures" / "bars"
MAP = {
    "SPY": "SPY", "QQQ": "QQQ", "IWM": "DOWN", "SMH": "BRKE", "XLK": "BRKX",
    "XLF": "CHEAP", "XLE": "PULR", "XLI": "XLI", "AAPL": "BRKC", "MSFT": "PULC",
    "NVDA": "GAPF", "AMZN": "PULN", "GOOGL": "ZERO", "META": "PULV",
    "TSLA": "BRKS", "AMD": "BRKO", "MU": "THIN", "AVGO": "DOWN", "MRVL": "PULR",
    "PLTR": "BRKE", "QCOM": "BARS60",
}


def sessions(n, end):
    out, d = [], end
    while len(out) < n:
        if A.is_trading_day(d):
            out.append(d)
        d = A.previous_trading_day(d)
    return out[::-1]


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
        if a.timeframe != "1Day":
            out["symbols"][sym] = {"bars": []}
            continue
        rows = list(csv.DictReader(open(FIX / f"{MAP[sym]}.csv")))
        ds = sessions(len(rows), date.fromisoformat(a.end[:10]))
        bars = [{"t_et": f"{d.isoformat()}T00:00:00-04:00", "o": r["open"],
                 "h": r["high"], "l": r["low"], "c": r["close"],
                 "v": r["volume"], "complete": True} for d, r in zip(ds, rows)]
        if scenario == "stale_all" or (scenario == "stale_one" and sym == "MU"):
            bars = bars[:-1]
        if scenario == "dup_date" and sym == "AAPL":
            bars[-5]["t_et"] = bars[-6]["t_et"]
        out["symbols"][sym] = {"bars": bars[-a.bars:]}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
