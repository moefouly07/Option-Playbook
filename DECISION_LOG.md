# Decision Log

## D-001 — Start with a simple baseline

Decision: test opening-range break + retest before adding many indicators.

Reason: reduce overfitting and make every decision reproducible.

## D-002 — VWAP is context, not independent confirmation

A first-touch breakout guarantees the breakout price is above prior prices, but a 5-minute-close breakout does not mathematically guarantee the closing price is above VWAP because trading may already have occurred beyond the range.

Decision: V1 does not require `price > VWAP` for calls or `price < VWAP` for puts as an independent directional rule. VWAP remains active only in the chop definition and is logged for analysis.

## D-003 — Retest is a bounded zone

The original one-sided inequality allowed an excessively deep wick to qualify as a retest.

Decision: retest must occur inside a symmetric 0.25 × ATR5 band around the broken opening-range level.

## D-004 — Wick through the level is allowed

Decision: a call retest may wick below ORH, and a put retest may wick above ORL, provided the wick stays inside the retest band and the 1-minute bar closes back on the correct side.

Secondary pre-registered comparison: strict retest, where the wick never crosses the broken level.

## D-005 — Deep wick cancels the setup

Decision: once price exceeds the outer boundary of the retest band before entry, that breakout setup is canceled. It is not allowed to wait for a later bar and pretend the failed retest never happened.

## D-006 — Keep true structural R

A proposal used:

```text
R = max(structural risk, 1.5 × ATR5)
```

while leaving the actual stop at the structural level.

Decision: rejected for V1 because it would rename a larger distance as R without changing the real stop. V1 defines:

```text
R = absolute distance between underlying entry and structural stop
```

The ratio `structural risk / ATR5` is recorded so a minimum-stop filter can be tested later without changing the baseline first.

## D-007 — Separate underlying edge from option execution

Decision: Layer 1 tests the underlying signal. Layer 2 measures option translation and friction. A correct underlying signal can still be a poor option trade.

## D-008 — No 0DTE in initial translation/pilot

Decision: use next-trading-day expiry first. 0DTE becomes a separate version/comparison after the signal is understood.

Reason: reduce extreme gamma/theta interaction while debugging the strategy.
