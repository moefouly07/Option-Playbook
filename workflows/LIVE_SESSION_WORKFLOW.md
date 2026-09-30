# Live Session Workflow

Use this workflow when CIM-V1 is being taught or illustrated with current market data.

A live example is not a backtest.

## 1. Load the rules first

Read:

```text
CURRENT_STATE.md
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
strategy/OPTION_TRANSLATION.md
```

Do not let the current chart change the frozen definition.

## 2. Establish market state

Preferred first check:

```text
Alpaca market clock
```

State:

```text
timestamp ET
market open/closed
RTH / premarket / after-hours / overnight
```

## 3. Cross-check the underlying

Use at least one reliable current SPY source.

When practical, compare:

```text
Webull snapshot/bars
Alpaca snapshot/quote
```

If prices disagree materially, inspect:

```text
timestamp
session
feed
IEX vs SIP
delayed status
in-progress vs completed bar
```

Do not silently average the prices.

## 4. Build the chart context

For educational/live rule application:

```text
SPY 1m
SPY 5m
RTH
```

Use completed bars when the frozen rule requires a close.

For formal VWAP research, consolidated volume is preferred.

If the live chart uses venue-limited volume, label VWAP:

```text
APPROXIMATE
```

## 5. Check event context

Use AlphaStocks as a secondary headline/sentiment view when useful.

Use authoritative web/official sources for material scheduled events or breaking facts when needed.

Event context is recorded in V1; it is not an automatic entry filter.

## 6. Wait for a mechanical signal

Classify only from frozen rules:

```text
NO TRADE
NOT YET
CANCELED
VALID SETUP
```

Do not choose CALL/PUT because the last candle is green/red.

## 7. Option chain only after the signal

Use Alpaca option chain/snapshot when available.

Identify the feed:

```text
OPRA
or
INDICATIVE
```

Select next-trading-day expiry and a practical contract within:

```text
|Delta| 0.40–0.60
```

preferably closest to 0.50 under the frozen tie-break rules.

Record:

```text
bid
ask
spread
delta
gamma
theta
vega
IV
quote timestamp
feed
```

## 8. Execution accounting

Without an actual fill:

```text
entry = ask
exit = bid
```

Do not present midpoint/mark/last as guaranteed execution.

## 9. Output discipline

Every live CIM example should state:

```text
strategy version
timestamp ET
session
underlying source/feed
option source/feed
data-quality warnings
setup state
```

Then separate:

```text
underlying thesis
contract quality
execution risk
```

## 10. Stop condition

If required timestamps, completed bars, or two-sided option quotes are unavailable:

```text
STATE THE LIMITATION
DO NOT INVENT THE MISSING INPUT
```
