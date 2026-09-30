# Glossary

## ORH / ORL

Opening Range High / Opening Range Low.

For CIM-V1, the opening range is the first 25 minutes of regular trading.

## Breakout

A move beyond a defined level. In V1, a breakout is not valid until a 5-minute bar closes beyond the opening range.

## Retest

Price returning to the broken level after a valid break.

## Confirmation

The mechanical condition that says the retest has started moving back in the breakout direction.

## Invalidation

The condition showing the setup thesis is no longer valid.

## VWAP

Volume-Weighted Average Price. It weights traded prices by volume.

## ATR

Average True Range. A volatility measure, not a direction indicator.

## SMA

Simple Moving Average.

## EMA

Exponential Moving Average. It weights recent prices more heavily than an SMA.

## RSI

Relative Strength Index. A bounded momentum oscillator.

## ATM

At The Money. Strike near the underlying price.

## ITM

In The Money.

## OTM

Out of The Money.

## Delta

Approximate first-order sensitivity of option price to a small move in the underlying.

## Gamma

How fast delta changes as the underlying moves.

## Theta

Option value decay associated with passage of time, all else equal.

## Vega

Sensitivity to implied volatility changes.

## IV

Implied Volatility.

## Bid / Ask

Bid is the price buyers are currently quoting. Ask is the price sellers are currently quoting.

## Spread

Difference between ask and bid. It is direct execution friction.

## Slippage

Difference between an expected/reference execution price and the actual fill.

## R

A unit of risk.

In CIM-V1:

```text
R = distance from underlying entry to structural stop
```

## MAE

Maximum Adverse Excursion: worst movement against the trade while open.

## MFE

Maximum Favorable Excursion: best movement in favor of the trade while open.

## Expectancy

```text
Expectancy
= WinRate × AverageWin
− LossRate × AverageLoss
− TradingFriction
```

## Profit Factor

Gross profits divided by gross losses.

## Whipsaw

Rapid direction changes that repeatedly trigger entries or exits without sustained follow-through.

## Chop

Sideways/noisy price action with weak directional follow-through. V1 uses a specific VWAP side-flip rule to classify it.
