"""
SCANNER-V1.1 reference implementation.

Purpose
-------
This file is the executable definition of the rules in
scanner/SCANNER_V1_1_SPEC.md. Any production implementation (for example
Muse's workspace code) must reproduce the labels and numbers this module
produces on scanner/tests/fixtures/ before its live output is trusted.

Constraints
-----------
- Python standard library only.
- Pure functions. No network, no files, no broker or trading code.
- Completed daily bars only. The caller must drop any in-progress bar.
- Parameters are PRE-REGISTERED. Changing any value is a new scanner
  version and requires a DECISION_LOG.md entry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Dict, List, Optional, Sequence

SPEC_VERSION = "SCANNER-V1.1"
BENCHMARK = "SPY"
BROAD_ETFS = ("SPY", "QQQ", "IWM")
SECTOR_ETFS = ("SMH", "XLK", "XLF", "XLE", "XLI")

PARAMS: Dict[str, float] = {
    "min_daily_bars": 70,
    "atr_len": 14,
    "rsi_len": 14,
    "sma_fast": 20,
    "sma_slow": 50,
    "rs_lookback": 20,
    "rvol_lookback": 20,
    "adv_lookback": 20,
    "breakout_lookback": 20,
    "pullback_touch_lookback": 3,
    "zone_atr_mult": 0.5,
    "breakout_min_rvol": 1.5,
    "pullback_min_rvol": 0.8,
    "min_range_pos": 0.5,
    "ext_flag_atr": 2.0,
    "ext_block_atr": 3.0,
    "rsi_overbought": 75.0,
    "min_price": 10.0,
    "min_adv_usd": 50_000_000.0,
    "corr_window": 60,
    "corr_min_overlap": 55,
    "corr_flag": 0.70,
    "max_candidates": 3,
}

# Labels (single enum used everywhere)
CONFIRMED_SETUP = "CONFIRMED_SETUP"
RESEARCH_PASS = "RESEARCH_PASS"
WATCH = "WATCH"
REJECT = "REJECT"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
BENCHMARK_ONLY = "BENCHMARK"

BREAKOUT = "BREAKOUT_20D"
PULLBACK = "PULLBACK_TO_SMA20"

TIER_ORDER = {CONFIRMED_SETUP: 0, RESEARCH_PASS: 1}
SETUP_ORDER = {BREAKOUT: 0, PULLBACK: 1}


@dataclass(frozen=True)
class Bar:
    date: str  # ISO YYYY-MM-DD, session date in America/New_York
    open: float
    high: float
    low: float
    close: float
    volume: float


# ---------------------------------------------------------------- indicators


def sma(values: Sequence[float], n: int) -> Optional[float]:
    if n <= 0 or len(values) < n:
        return None
    return sum(values[-n:]) / n


def true_ranges(bars: Sequence[Bar]) -> List[float]:
    """TR for bars[1:], each using the previous bar's close."""
    out = []
    for prev, cur in zip(bars[:-1], bars[1:]):
        out.append(max(cur.high - cur.low,
                       abs(cur.high - prev.close),
                       abs(cur.low - prev.close)))
    return out


def wilder_atr(bars: Sequence[Bar], n: int = 14) -> Optional[float]:
    """Wilder ATR: seed = simple mean of the first n TRs, then
    ATR_t = (ATR_{t-1} * (n - 1) + TR_t) / n. Needs n + 1 bars."""
    trs = true_ranges(bars)
    if len(trs) < n:
        return None
    atr = sum(trs[:n]) / n
    for tr in trs[n:]:
        atr = (atr * (n - 1) + tr) / n
    return atr


def wilder_rsi(closes: Sequence[float], n: int = 14) -> Optional[float]:
    """Wilder RSI. Seed averages = simple mean of first n gains/losses."""
    if len(closes) < n + 1:
        return None
    changes = [b - a for a, b in zip(closes[:-1], closes[1:])]
    gains = [max(c, 0.0) for c in changes]
    losses = [max(-c, 0.0) for c in changes]
    avg_g = sum(gains[:n]) / n
    avg_l = sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):
        avg_g = (avg_g * (n - 1) + g) / n
        avg_l = (avg_l * (n - 1) + l) / n
    if avg_l == 0.0:
        return 100.0 if avg_g > 0.0 else 50.0
    rs = avg_g / avg_l
    return 100.0 - 100.0 / (1.0 + rs)


def range_position(bar: Bar) -> Optional[float]:
    """(close - low) / (high - low). None when high == low."""
    span = bar.high - bar.low
    if span <= 0:
        return None
    return (bar.close - bar.low) / span


def rvol(bars: Sequence[Bar], k: int = 20) -> Optional[float]:
    """Latest completed daily volume / mean of the previous k volumes."""
    if len(bars) < k + 1:
        return None
    base = sum(b.volume for b in bars[-1 - k:-1]) / k
    if base <= 0:
        return None
    return bars[-1].volume / base


def adv_usd(bars: Sequence[Bar], k: int = 20) -> Optional[float]:
    if len(bars) < k:
        return None
    return sum(b.close * b.volume for b in bars[-k:]) / k


def relative_strength(sym: Sequence[Bar], bench: Sequence[Bar],
                      k: int = 20) -> Optional[float]:
    """k-day return of sym minus k-day return of bench, in percentage
    points, on date-aligned closes. None if the latest dates differ or
    there are fewer than k + 1 aligned dates.

    IMPORTANT: 0.0 is a valid value. Test with `is None`, never truthiness.
    """
    if not sym or not bench or sym[-1].date != bench[-1].date:
        return None
    bmap = {b.date: b.close for b in bench}
    pairs = [(b.close, bmap[b.date]) for b in sym if b.date in bmap]
    if len(pairs) < k + 1:
        return None
    s0, b0 = pairs[-1 - k]
    s1, b1 = pairs[-1]
    return ((s1 / s0 - 1.0) - (b1 / b0 - 1.0)) * 100.0


def _returns_by_date(bars: Sequence[Bar]) -> Dict[str, float]:
    """Simple returns on each series' OWN consecutive bars, keyed by the
    later bar's date. Joining happens afterwards, on returns."""
    return {cur.date: cur.close / prev.close - 1.0
            for prev, cur in zip(bars[:-1], bars[1:])}


def pearson(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    n = len(x)
    if n != len(y) or n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / sqrt(sxx * syy)


def correlation(a: Sequence[Bar], b: Sequence[Bar], window: int = 60,
                min_overlap: int = 55) -> Dict[str, object]:
    """Pearson correlation of daily simple returns.

    Method (must be reported with every value):
      1. returns computed per series on its own consecutive completed bars;
      2. inner join on return date;
      3. keep the last `window` joined dates;
      4. require at least `min_overlap` joined returns, else r = None.
    Prices are never correlated directly.
    """
    ra, rb = _returns_by_date(a), _returns_by_date(b)
    dates = sorted(set(ra) & set(rb))[-window:]
    out: Dict[str, object] = {"r": None, "n": len(dates),
                              "first": dates[0] if dates else None,
                              "last": dates[-1] if dates else None,
                              "method": "simple_returns_inner_join"}
    if len(dates) < min_overlap:
        return out
    out["r"] = pearson([ra[d] for d in dates], [rb[d] for d in dates])
    return out


# ------------------------------------------------------------ classification


@dataclass
class Result:
    symbol: str
    label: str
    setup: Optional[str] = None
    triggered: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    reason: str = ""
    metrics: Dict[str, Optional[float]] = field(default_factory=dict)
    pivot: Optional[float] = None
    invalidation: Optional[float] = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol, "label": self.label, "setup": self.setup,
            "triggered": self.triggered, "failed": self.failed,
            "flags": self.flags, "reason": self.reason,
            "metrics": self.metrics, "pivot": self.pivot,
            "invalidation": self.invalidation,
        }


def _check(res: Result, name: str, ok: bool) -> bool:
    (res.triggered if ok else res.failed).append(name)
    return ok


def classify(symbol: str, bars: Sequence[Bar], bench: Sequence[Bar],
             p: Dict[str, float] = PARAMS) -> Result:
    n_min = int(p["min_daily_bars"])
    if len(bars) < n_min:
        return Result(symbol, INSUFFICIENT_DATA,
                      reason=f"only {len(bars)} completed daily bars (< {n_min})")
    if symbol != BENCHMARK:
        if len(bench) < n_min:
            return Result(symbol, INSUFFICIENT_DATA,
                          reason="benchmark history insufficient")
        if bars[-1].date != bench[-1].date:
            return Result(symbol, INSUFFICIENT_DATA,
                          reason="latest bar date differs from benchmark")

    t, prev = bars[-1], bars[-2]
    closes = [b.close for b in bars]
    m: Dict[str, Optional[float]] = {}
    m["close"] = t.close
    m["sma20"] = sma(closes, int(p["sma_fast"]))
    m["sma50"] = sma(closes, int(p["sma_slow"]))
    m["atr14"] = wilder_atr(bars, int(p["atr_len"]))
    m["atr14_pct"] = (m["atr14"] / t.close * 100.0) if m["atr14"] else None
    m["rsi14"] = wilder_rsi(closes, int(p["rsi_len"]))
    m["rvol20"] = rvol(bars, int(p["rvol_lookback"]))
    m["adv20_usd"] = adv_usd(bars, int(p["adv_lookback"]))
    m["range_pos"] = range_position(t)
    m["rs20_pp"] = (0.0 if symbol == BENCHMARK
                    else relative_strength(bars, bench, int(p["rs_lookback"])))
    m["ext_atr"] = ((t.close - m["sma20"]) / m["atr14"]
                    if m["sma20"] is not None and m["atr14"] else None)

    res = Result(symbol, WATCH, metrics=m)

    if symbol == BENCHMARK:
        res.label = BENCHMARK_ONLY
        res.reason = "benchmark and regime reference; never a candidate"
        return res

    required = ("sma20", "sma50", "atr14", "rsi14", "rvol20", "adv20_usd",
                "rs20_pp", "ext_atr")
    missing = [k for k in required if m[k] is None]
    if missing:
        res.label = INSUFFICIENT_DATA
        res.reason = "missing: " + ", ".join(missing)
        return res

    # Liquidity gate
    liquid = _check(res, "close>=min_price", t.close >= p["min_price"])
    liquid &= _check(res, "adv20_usd>=min_adv", m["adv20_usd"] >= p["min_adv_usd"])
    if not liquid:
        res.label = REJECT
        res.reason = "fails liquidity screen"
        return res

    if m["rsi14"] >= p["rsi_overbought"]:
        res.flags.append("RSI_OVERBOUGHT_RECORDED_ONLY")

    sma20, sma50, atr = m["sma20"], m["sma50"], m["atr14"]
    zone_lo = sma20 - p["zone_atr_mult"] * atr
    zone_hi = sma20 + p["zone_atr_mult"] * atr
    m["zone_lo"], m["zone_hi"] = zone_lo, zone_hi

    lb = int(p["breakout_lookback"])
    prior_high = max(b.high for b in bars[-1 - lb:-1])
    m["prior_20d_high"] = prior_high

    # ---- setup detection (breakout takes precedence)
    is_breakout = t.close > prior_high and t.close > sma50
    if is_breakout:
        res.setup = BREAKOUT
        _check(res, "close>prior_20d_high", True)
        _check(res, "close>sma50", True)
        conf = _check(res, "range_pos>=0.5",
                      m["range_pos"] is not None and m["range_pos"] >= p["min_range_pos"])
        conf &= _check(res, "rvol20>=1.5", m["rvol20"] >= p["breakout_min_rvol"])
        res.pivot = t.high
        res.invalidation = prior_high
    else:
        uptrend = _check(res, "close>sma50", t.close > sma50)
        uptrend &= _check(res, "sma20>sma50", sma20 > sma50)
        k = int(p["pullback_touch_lookback"])
        touched = _check(res, "low_touched_zone_last3",
                         min(b.low for b in bars[-k:]) <= zone_hi)
        held = _check(res, "close>=zone_lo", t.close >= zone_lo)
        if not (uptrend and touched and held):
            res.label = WATCH
            res.reason = "no qualifying setup"
            return res
        res.setup = PULLBACK
        res.pivot = sma20
        res.invalidation = zone_lo
        if not _check(res, "rs20>0", m["rs20_pp"] > 0.0):
            res.label = WATCH
            res.reason = "pullback structure but relative strength not positive"
            return res
        conf = _check(res, "close>prev_close", t.close > prev.close)
        conf &= _check(res, "range_pos>=0.5",
                       m["range_pos"] is not None and m["range_pos"] >= p["min_range_pos"])
        conf &= _check(res, "low_t<=zone_hi", t.low <= zone_hi)
        conf &= _check(res, "close>=sma20", t.close >= sma20)
        conf &= _check(res, "rvol20>=0.8", m["rvol20"] >= p["pullback_min_rvol"])

    # ---- extension penalty (applies to any setup)
    ext = m["ext_atr"]
    if ext > p["ext_block_atr"]:
        res.flags.append("OVEREXTENDED")
        res.label = WATCH
        res.reason = f"setup present but extension {ext:.2f} ATR > {p['ext_block_atr']}"
        return res
    if ext > p["ext_flag_atr"]:
        res.flags.append("EXTENDED")
        conf = False
        res.reason = f"extension {ext:.2f} ATR caps tier at RESEARCH_PASS"

    res.label = CONFIRMED_SETUP if conf else RESEARCH_PASS
    if not res.reason:
        res.reason = ("all confirmation conditions met" if conf
                      else "setup present; confirmation incomplete")
    return res


# ----------------------------------------------------------- ranking/select


def rank_key(r: Result):
    return (TIER_ORDER[r.label], SETUP_ORDER[r.setup],
            -(r.metrics["rs20_pp"]), -(r.metrics["rvol20"]), r.symbol)


def select(results: Sequence[Result], bars_by_symbol: Dict[str, Sequence[Bar]],
           p: Dict[str, float] = PARAMS) -> Dict[str, object]:
    eligible = sorted([r for r in results if r.label in TIER_ORDER], key=rank_key)
    chosen: List[Result] = []
    skipped: List[Dict[str, object]] = []
    corr_log: List[Dict[str, object]] = []
    for r in eligible:
        if len(chosen) >= int(p["max_candidates"]):
            break
        blocked_by = None
        for c in chosen:
            cr = correlation(bars_by_symbol[r.symbol], bars_by_symbol[c.symbol],
                             int(p["corr_window"]), int(p["corr_min_overlap"]))
            corr_log.append({"pair": [c.symbol, r.symbol], **cr})
            if cr["r"] is None:
                r.flags.append(f"CORRELATION_UNAVAILABLE_WITH_{c.symbol}")
            elif abs(cr["r"]) >= p["corr_flag"]:
                blocked_by = c.symbol
                break
        if blocked_by:
            r.flags.append(f"CORRELATED_WITH_{blocked_by}")
            skipped.append({"symbol": r.symbol, "reason": f"|r|>={p['corr_flag']} vs {blocked_by}"})
            continue
        chosen.append(r)
    return {
        "verdict": "CANDIDATES" if chosen else "NO_CANDIDATES",
        "shortlist": [r.symbol for r in chosen],
        "skipped_for_correlation": skipped,
        "correlation_log": corr_log,
    }


def regime(bars_by_symbol: Dict[str, Sequence[Bar]]) -> Dict[str, object]:
    """RECORDED ONLY in V1.1. Breadth is watchlist breadth, not market breadth."""
    def above(sym: str, n: int) -> Optional[bool]:
        bars = bars_by_symbol.get(sym)
        if not bars:
            return None
        s = sma([b.close for b in bars], n)
        return None if s is None else bars[-1].close > s

    usable50 = [s for s in bars_by_symbol if above(s, 50) is not None]
    usable20 = [s for s in bars_by_symbol if above(s, 20) is not None]
    b50 = (sum(above(s, 50) for s in usable50) / len(usable50)) if usable50 else None
    b20 = (sum(above(s, 20) for s in usable20) / len(usable20)) if usable20 else None
    sectors = [s for s in SECTOR_ETFS if above(s, 20) is not None]
    spy50, qqq50 = above("SPY", 50), above("QQQ", 50)
    if spy50 and qqq50 and b50 is not None and b50 >= 0.60:
        label = "RISK_ON"
    elif spy50 is False and qqq50 is False and b50 is not None and b50 < 0.40:
        label = "RISK_OFF"
    else:
        label = "MIXED"
    return {
        "label": label,
        "spy_above_sma50": spy50,
        "qqq_above_sma50": qqq50,
        "watchlist_breadth_above_sma50": b50,
        "watchlist_breadth_above_sma20": b20,
        "sector_etfs_above_sma20": sum(above(s, 20) for s in sectors),
        "sector_etfs_counted": len(sectors),
        "status": "RECORDED_ONLY",
    }
