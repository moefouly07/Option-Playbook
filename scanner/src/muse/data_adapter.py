# Canonical repository copy. Base: Muse T1c export (data_adapter.py, sha256 88adb59b41aa3d40...),
# decoded byte-exact and reviewed. Review fixes applied per DECISION_LOG D-021.
"""SCANNER-V1.1 data adapter (Muse workspace copy).

Fetches market data ONLY through the read-only alpaca-market-data skill
CLI (subprocess). The CLI owns authentication via a runtime credential
surrogate; this module never sees, stores, or logs any credential.

Data rules enforced here (SCANNER-V1.1 spec section 3):
- Daily classification input: completed consolidated SIP daily bars only.
  The in-progress session is dropped using an NYSE rule-based calendar
  plus the CLI's per-bar completeness flag.
- Intraday: SIP 5-minute bars requested with end = now - 20 minutes;
  extended-hours bars are removed (regular session only).
- IEX and SIP volume are never mixed: bars are requested with feed=sip
  only, and no quote volume is ever merged into bar data.
- All dates returned are America/New_York session dates.

No order, trading, position, or account endpoints exist anywhere in this
module. It only reads bars through the skill CLI's allowlisted GET paths.
"""

from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from zoneinfo import ZoneInfo

try:
    ET = ZoneInfo("America/New_York")
except Exception as _exc:  # e.g. Windows Python without the tzdata package
    raise SystemExit("America/New_York time-zone data not found. "
                     "On Windows run: pip install tzdata") from _exc

# The skill CLI lives outside the repository (Muse workspace skill).
# A path override is allowed for portability; it is not a credential.
SKILL_CLI = Path(os.environ.get(
    "ALPACA_SKILL_CLI",
    str(Path.home() / "workspace" / "skills" / "alpaca-market-data"
        / "bin" / "alpaca_quotes.py")))

# Pre-registered history window (SCANNER_V1_1_SPEC.md section 3, D-021):
# Wilder ATR/RSI depend on how much history seeds them, so the window is
# fixed. Changing it is a new scanner version.
DAILY_REQUEST_BARS = 130
INTRADAY_REQUEST_BARS = 200    # one RTH session is 78 bars; headroom included
ADJUSTMENT = "split"
RTH_START = time(9, 30)


class AdapterError(RuntimeError):
    """Raised when the data layer cannot produce trustworthy bars."""


# ------------------------------------------------------------- NYSE calendar
# Rule-based NYSE calendar: fixed/floating holidays with weekend
# observance, plus 13:00 early closes. Ad-hoc closures (weather, national
# mourning) are NOT modeled and must be caught by the run's calendar_check
# notes and the vendor session data.


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    d = date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + timedelta(days=offset + 7 * (n - 1))


def _last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        d = date(year, 12, 31)
    else:
        d = date(year, month + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _easter_sunday(year: int) -> date:
    # Anonymous Gregorian computus.
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _observed(d: date) -> date:
    """Weekend observance: Saturday -> Friday, Sunday -> Monday."""
    if d.weekday() == 5:
        return d - timedelta(days=1)
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def nyse_holidays(year: int) -> set:
    h = set()
    # New Year's Day (NYSE exception: a Saturday Jan 1 does NOT close the
    # preceding Friday).
    jan1 = date(year, 1, 1)
    if jan1.weekday() == 6:
        h.add(date(year, 1, 2))
    elif jan1.weekday() != 5:
        h.add(jan1)
    h.add(_nth_weekday(year, 1, 0, 3))    # Martin Luther King Jr. Day
    h.add(_nth_weekday(year, 2, 0, 3))    # Washington's Birthday
    h.add(_easter_sunday(year) - timedelta(days=2))  # Good Friday
    h.add(_last_weekday(year, 5, 0))      # Memorial Day
    if year >= 2022:
        h.add(_observed(date(year, 6, 19)))   # Juneteenth
    h.add(_observed(date(year, 7, 4)))        # Independence Day
    h.add(_nth_weekday(year, 9, 0, 1))        # Labor Day
    h.add(_nth_weekday(year, 11, 3, 4))      # Thanksgiving
    h.add(_observed(date(year, 12, 25)))      # Christmas
    return h


def is_trading_day(d: date) -> bool:
    return d.weekday() < 5 and d not in nyse_holidays(d.year)


def is_early_close(d: date) -> bool:
    if not is_trading_day(d):
        return False
    thanksgiving = _nth_weekday(d.year, 11, 3, 4)
    if d == thanksgiving + timedelta(days=1):
        return True                       # day after Thanksgiving
    if d == date(d.year, 12, 24):
        return True                       # Christmas Eve (when a session)
    if d == date(d.year, 7, 3):
        return True                       # day before Independence Day
    return False


def session_close_time(d: date) -> time:
    return time(13, 0) if is_early_close(d) else time(16, 0)


def previous_trading_day(d: date) -> date:
    d = d - timedelta(days=1)
    while not is_trading_day(d):
        d -= timedelta(days=1)
    return d


def latest_completed_session(now_et: datetime) -> date:
    """Latest session whose daily bar is complete at `now_et`."""
    today = now_et.date()
    if is_trading_day(today) and now_et.time() >= session_close_time(today):
        return today
    return previous_trading_day(today)


def latest_available_session(now_et: datetime) -> date:
    """Latest session whose daily bar may be requested and trusted at `now_et`.

    Always the trading day strictly before today's ET calendar date
    (KI-004, D-023). The market-data plan refuses consolidated SIP daily
    requests that end on the current calendar date, even after the close,
    and a same-day close can still be revised. So day T's daily bar is
    first used on day T + 1.
    """
    return previous_trading_day(now_et.date())


# ----------------------------------------------------------------- CLI calls


def _run_cli(args: List[str]) -> dict:
    if not SKILL_CLI.is_file():
        raise AdapterError(f"alpaca-market-data skill CLI not found at {SKILL_CLI}")
    cmd = [sys.executable, str(SKILL_CLI)] + args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    except subprocess.TimeoutExpired as exc:
        raise AdapterError("skill CLI timed out") from exc
    if proc.returncode != 0:
        detail = _redact((proc.stderr or proc.stdout or "").strip())[:300]
        raise AdapterError(f"skill CLI failed (exit {proc.returncode}): {detail}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AdapterError("skill CLI returned non-JSON output") from exc
    if not payload.get("ok", False):
        raise AdapterError(f"skill CLI reported not-ok: {_redact(str(payload))[:300]}")
    return payload


_TOKENISH = re.compile(r"[A-Za-z0-9_\-]{20,}")


def _redact(text: str) -> str:
    """Hide anything token-like before an error message can reach a log."""
    return _TOKENISH.sub("[REDACTED]", text)


def daily_bar_issue(bars: Sequence[dict]) -> Optional[str]:
    """Return a description of the first integrity problem, or None.

    Checks: strictly increasing unique session dates, finite prices,
    low <= min(open, close) <= max(open, close) <= high, volume >= 0.
    """
    prev = None
    for b in bars:
        d = b["date"]
        if prev is not None and d <= prev:
            return f"non-increasing or duplicate session date {d}"
        prev = d
        vals = (b["open"], b["high"], b["low"], b["close"], b["volume"])
        if not all(math.isfinite(v) for v in vals):
            return f"non-finite value on {d}"
        if not (b["low"] <= min(b["open"], b["close"])
                and max(b["open"], b["close"]) <= b["high"]):
            return f"inconsistent OHLC on {d}"
        if b["volume"] < 0:
            return f"negative volume on {d}"
    return None


def _session_bars(node: dict) -> List[dict]:
    """Convert CLI bar dicts to adapter bars with ET session dates."""
    out = []
    for b in node.get("bars", []):
        out.append({
            "date": b["t_et"][:10],
            "t_et": b["t_et"],
            "open": float(b["o"]),
            "high": float(b["h"]),
            "low": float(b["l"]),
            "close": float(b["c"]),
            "volume": float(b["v"]),
            "complete": bool(b.get("complete", False)),
        })
    out.sort(key=lambda x: x["date"] + x["t_et"])
    return out


def fetch_daily_bars(symbols: Sequence[str], end_session: date,
                     bars: int = DAILY_REQUEST_BARS) -> Dict[str, List[dict]]:
    """Completed consolidated SIP daily bars ending at `end_session`.

    Bars flagged incomplete by the vendor, and any bar dated after
    `end_session`, are dropped. Returned bars carry keys:
    date (ET session date), open, high, low, close, volume.
    """
    payload = _run_cli([
        "--symbols", ",".join(symbols),
        "--feed", "sip",
        "--timeframe", "1Day",
        "--bars", str(bars),
        "--end", end_session.isoformat(),
        "--adjustment", ADJUSTMENT,
    ])
    result: Dict[str, List[dict]] = {}
    for sym in symbols:
        node = payload.get("symbols", {}).get(sym)
        if node is None:
            raise AdapterError(f"skill CLI returned no data for {sym}")
        kept = []
        for b in _session_bars(node):
            if not b["complete"]:
                continue                      # in-progress session dropped
            if b["date"] > end_session.isoformat():
                continue
            kept.append({k: b[k] for k in
                         ("date", "open", "high", "low", "close", "volume")})
        result[sym] = kept
    return result


def fetch_intraday_5m(symbol: str, session_date: date,
                      now_et: datetime) -> List[dict]:
    """Completed RTH SIP 5-minute bars for one session.

    Requested with end = now - 20 minutes (spec section 3). For a session
    that is already fully in the past, the end is capped at that
    session's end of day: the value is identical in effect (every bar of
    the session precedes both), and it avoids the vendor's free-plan
    rejection of SIP queries whose end reaches into the current day.
    Extended-hours bars are removed; only [09:30, session close) bars on
    `session_date` are returned, each with its full ET timestamp. A bar is
    returned only if it is provably complete: its end (start + 5 minutes)
    is at or before the request end (KI-003, D-022).
    """
    end_et = now_et - timedelta(minutes=20)
    session_eod = datetime.combine(session_date, time(23, 59, 59),
                                   tzinfo=ET)
    if end_et > session_eod:
        end_et = session_eod
    start_et = datetime.combine(session_date, time(0, 0), tzinfo=ET)
    payload = _run_cli([
        "--symbols", symbol,
        "--feed", "sip",
        "--timeframe", "5Min",
        "--bars", str(INTRADAY_REQUEST_BARS),
        "--start", start_et.isoformat(),
        "--end", end_et.isoformat(),
        "--adjustment", ADJUSTMENT,
    ])
    node = payload.get("symbols", {}).get(symbol)
    if node is None:
        raise AdapterError(f"skill CLI returned no intraday data for {symbol}")
    close_t = session_close_time(session_date)
    out = []
    for b in _session_bars(node):
        if b["date"] != session_date.isoformat():
            continue
        start = datetime.fromisoformat(b["t_et"])
        if start.tzinfo is None:
            start = start.replace(tzinfo=ET)
        if not (RTH_START <= start.time() < close_t):   # extended hours dropped
            continue
        if start + timedelta(minutes=5) > end_et:       # not provably complete
            continue
        out.append(b)
    return out


def daily_source_string() -> str:
    return (f"alpaca sip 1Day adjustment={ADJUSTMENT} "
            f"bars={DAILY_REQUEST_BARS} via alpaca-market-data skill CLI "
            f"(read-only); completed bars only")


def intraday_source_string() -> str:
    return ("alpaca sip 5Min via alpaca-market-data skill CLI (read-only); "
            "end = now - 20 minutes; RTH only; recorded only, never "
            "used in classification")


def quotes_source_string() -> str:
    return ("not fetched by this pipeline; no quote data is used in any "
            "V1.1 calculation (IEX and SIP volume are never mixed)")
