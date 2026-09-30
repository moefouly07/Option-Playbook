# Phase-1 Backtest Protocol

## Objective

Test whether CIM-V1 has evidence of positive expectancy without changing its frozen rules after seeing results.

## Layer 1 — Underlying signal

### Data

- SPY consolidated 1-minute RTH data
- Target history: 2–3 years
- Corporate-action-adjusted prices as appropriate
- Same source used to construct 5-minute bars
- Consolidated volume for formal VWAP

### Outputs per signal

Record:

- signal date and direction
- ORH / ORL / opening-range width
- break timestamp
- ATR5 at break and entry
- initial retest timestamp
- retest depth in ATR5 units
- confirmation timestamp
- entry timestamp and price
- structural stop
- R
- R / ATR5
- target
- exit reason
- realized underlying R
- MAE
- MFE
- time in trade

### Recorded-only context

Record but do not filter:

- RSI14
- SMA / EMA context
- PDH / PDL distance
- premarket high/low distance
- open gap percentage
- relative volume
- VWAP distance
- scheduled macro-event tag
- strict-retest membership

## Sample handling

Prefer chronological splitting.

Example framework:

```text
Development / implementation check
→ Out-of-sample validation
→ Forward pilot
```

Do not use the out-of-sample period to choose rule thresholds.

## Friction

Layer 1 reports underlying signal behavior before option friction.

Layer 2 applies option spread/slippage. Do not claim the underlying result is the tradable option result.

## Statistical reporting

Report at minimum:

- number of eligible days
- number of signals
- no-trade days
- call count
- put count
- win rate
- average win in R
- average loss in R
- expectancy
- profit factor
- maximum drawdown in R
- median and average hold time
- MAE/MFE distributions
- result by year
- result by call vs put
- strict-retest secondary comparison

Confidence intervals should be shown where appropriate.

Do not treat 20 or 50 trades as proof of a small edge.

## Failure conditions

The baseline can fail for several reasons:

- too few signals
- negative expectancy
- positive gross signal but negative option translation after friction
- unstable results across periods
- edge concentrated in one abnormal regime
- implementation ambiguity

A failed baseline is useful research information.
