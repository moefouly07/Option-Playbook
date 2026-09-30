# Confirmed Intraday Momentum — CIM-V1.0

**Status:** FROZEN  
**Instrument:** SPY  
**Session:** U.S. regular trading hours  
**Time zone:** U.S. Eastern Time

This is the canonical Phase-1 strategy specification.

## 1. Data

Use consolidated SPY 1-minute regular-session bars.

Derive 5-minute bars from the same 1-minute source.

VWAP must use consolidated trade volume when used for the formal test. If only venue-limited volume is available, label the VWAP approximate and do not mix it silently with consolidated results.

## 2. Opening range

```text
Opening Range = 09:30:00 through 09:54:59 ET
ORH = highest high in that interval
ORL = lowest low in that interval
```

No entry can occur before 09:55 ET.

## 3. ATR5

`ATR5` means Wilder ATR14 calculated on completed 5-minute RTH bars.

Use only information available at the timestamp being evaluated.

## 4. Call setup

### Break

A call break exists when a completed 5-minute bar closes strictly above ORH.

```text
5m close > ORH
```

The break bar itself cannot be the retest bar.

### Retest window

After the break bar closes, allow up to 30 minutes for the setup to qualify.

Define:

```text
Lower band = ORH − 0.25 × ATR5
Upper band = ORH + 0.25 × ATR5
```

The first 1-minute bar that satisfies both conditions becomes the **initial retest bar**:

```text
Lower band ≤ 1m low ≤ Upper band
AND
1m close ≥ ORH
```

A wick below ORH is allowed.

### Cancellation

Before entry, cancel the setup if any 1-minute low is below the lower band.

Also cancel if a completed 5-minute bar closes back inside the opening range.

### Confirmation

After the initial retest bar, confirmation occurs when a later 1-minute bar closes strictly above the initial retest bar high.

```text
1m close > initial retest-bar high
```

### Entry timestamp

Enter on the next 1-minute bar after the confirmation bar.

For Layer 1, use that next bar's underlying open as the signal-entry price.

For Layer 2/pilot, use the first valid option ASK available at or immediately after that entry timestamp.

### Structural stop

Before entry, define the call structural stop as the lowest 1-minute low from the initial retest bar through the confirmation bar.

The setup is invalidated when a later completed 1-minute bar closes strictly below the structural stop.

For Layer 1, record the invalidation and next-bar executable price separately so gap/slippage beyond the structural level is visible.

### R and target

```text
R = underlying entry price − structural stop
Target = underlying entry price + 1.5 × R
```

If `R <= 0`, the setup is invalid.

V1 does not reject a setup because R is small relative to ATR. Instead record:

```text
R / ATR5
```

for later analysis.

## 5. Put setup

Mirror the call logic.

Break:

```text
5m close < ORL
```

Retest band:

```text
Lower band = ORL − 0.25 × ATR5
Upper band = ORL + 0.25 × ATR5
```

Initial retest bar:

```text
Lower band ≤ 1m high ≤ Upper band
AND
1m close ≤ ORL
```

Cancellation:

```text
any 1m high > Upper band
OR
completed 5m close back inside opening range
```

Confirmation:

```text
later 1m close < initial retest-bar low
```

Structural stop:

highest 1-minute high from initial retest bar through confirmation bar.

Risk and target:

```text
R = structural stop − underlying entry price
Target = underlying entry price − 1.5 × R
```

## 6. Chop rule

At every prospective entry, classify the last four completed 5-minute bars by whether each close is above or below that bar's ending VWAP.

A **VWAP side flip** occurs when consecutive completed bars change from above to below or below to above.

```text
2 or more side flips in the last 4 completed 5m bars
→ CHOP
→ NO NEW ENTRY
```

A close exactly equal to VWAP is treated as unstable; no new entry is allowed while it is inside the four-bar window.

This is the only active V1 VWAP filter.

## 7. Timing

```text
Earliest entry: 09:55 ET
Last entry:     11:45 ET
Time exit:      12:30 ET
Setup expiry:   30 minutes after break-bar close
```

Any open position is closed at the 12:30 ET time exit if neither target nor invalidation has ended it.

## 8. Daily limits

```text
Maximum call trades: 1 per day
Maximum put trades:  1 per day
Maximum total:       2 per day
No overlapping positions
```

## 9. Target handling in Layer 1

A target is considered reached when a 1-minute bar trades through the underlying target level.

Record the target-touch timestamp and target price.

Stop events are based on completed 1-minute closes because the rule defines structural failure by close, not wick.

This intentional asymmetry must be preserved and reported; a future version may test close-based targets as a separate rule.

## 10. Secondary pre-registered comparison

The only V1 retest comparison allowed without creating a new strategy version is:

```text
STRICT CALL: retest-bar low ≥ ORH
STRICT PUT:  retest-bar high ≤ ORL
```

The primary strategy remains wick-allowed inside the band.

## 11. Not active in V1

The following may be logged but cannot change a V1 trade decision:

- RSI
- SMA
- EMA
- previous-day high/low
- premarket high/low
- relative volume
- macro-event tags
- gap percentage
- discretionary support/resistance
- candle-pattern names

Adding any of them as a filter creates a new version.
