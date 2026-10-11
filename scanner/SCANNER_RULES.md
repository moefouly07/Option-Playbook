# Scanner Rules — Plain-Language Summary

This page summarizes `SCANNER_V1_1_SPEC.md`. If anything here disagrees with the spec or `reference/scanner_rules.py`, the spec and the reference implementation win.

Status: research draft. Not a proven trading strategy. No execution.

Universe: 21 fixed liquid symbols. SPY is the benchmark and is never a candidate.

Liquidity: close at least 10 dollars and 20-day average dollar volume at least 50 million, else REJECT. Missing data is INSUFFICIENT_DATA, never a negative signal.

Setups on the latest completed daily bar:

- Breakout: close above the prior 20-day high and above SMA50. Confirmed when the close is in the upper half of the day's range on at least 1.5x volume.
- Pullback: uptrend (close and SMA20 above SMA50), a low that reached the SMA20 zone (plus or minus 0.5 ATR14) in the last three sessions, and positive 20-day relative strength versus SPY. Confirmed by an up close, upper-half range position, today's low inside the zone, close back at or above SMA20, and at least 0.8x volume.
- Extension: more than 2 ATR above SMA20 caps the label at RESEARCH_PASS; more than 3 ATR blocks it to WATCH.

Selection: at most three, ranked by a fixed convention, skipping any name with absolute 60-day return correlation of 0.70 or more with a name already selected. Empty list means NO_CANDIDATES.

Recorded only, never decisive in V1.1: regime, catalysts, RSI, earnings proximity, intraday status.

Labels: CONFIRMED_SETUP, RESEARCH_PASS, WATCH, REJECT, INSUFFICIENT_DATA, BENCHMARK.

No arbitrary probabilities or scores, no edge claims, no trading, no edits to the frozen strategy.
