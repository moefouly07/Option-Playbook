# CIM-V1 Quick Checklist

## Before 09:55 ET

```text
[ ] SPY data source identified
[ ] 1m and 5m charts ready
[ ] VWAP available
[ ] ATR14 on 5m available
[ ] No trade yet
```

## At 09:55 ET

```text
[ ] ORH fixed
[ ] ORL fixed
[ ] Opening range will not be redrawn
```

## Setup

```text
[ ] Valid 5m close outside OR
[ ] Retest occurs after break bar
[ ] Retest is inside ±0.25 ATR5 band
[ ] Retest closes on correct side
[ ] No deep-band cancellation
[ ] No 5m close back inside OR before entry
[ ] Confirmation completed
[ ] Fewer than 2 VWAP side flips in last 4 closed 5m bars
[ ] Entry time ≤ 11:45 ET
[ ] Daily trade limit not exceeded
[ ] No overlapping trade
```

## Risk

```text
[ ] Structural stop fixed before entry
[ ] R calculated from actual structural distance
[ ] Target = 1.5R
[ ] R / ATR5 logged
```

## Option

```text
[ ] Next-trading-day expiry
[ ] Correct Call/Put
[ ] |Delta| between 0.40 and 0.60
[ ] Closest practical candidate to 0.50
[ ] Bid and Ask visible
[ ] Spread logged
[ ] Quote timestamp logged
```

## Exit

```text
[ ] Target hit
OR
[ ] 1m close invalidated structure
OR
[ ] Time exit at 12:30 ET
```

## Journal

```text
[ ] MAE
[ ] MFE
[ ] Underlying R
[ ] Option P/L
[ ] Option R
[ ] Slippage
[ ] Rule deviation
[ ] Recorded-only context
```
