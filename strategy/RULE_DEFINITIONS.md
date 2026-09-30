# Mechanical Rule Definitions

This file resolves ambiguous language.

## Break

Not a wick. Not a touch.

```text
Call break = completed 5m close > ORH
Put break  = completed 5m close < ORL
```

## Retest

A retest is the first post-break 1-minute bar that enters the defined ATR band and closes back on the correct side of the broken level.

It is not any later bar selected because it makes the trade look better.

## Successful wick

For a call, the wick may pass below ORH but not below the lower retest-band boundary.

For a put, the wick may pass above ORL but not above the upper retest-band boundary.

## Failed retest

A deep wick beyond the outer retest boundary before entry cancels the current breakout setup.

## Confirmation

Confirmation always occurs after the initial retest bar.

```text
Call = later 1m close > initial retest-bar high
Put  = later 1m close < initial retest-bar low
```

## Structural stop

The stop level is built from the entire retest-to-confirmation sequence:

```text
Call = minimum low from initial retest bar through confirmation bar
Put  = maximum high from initial retest bar through confirmation bar
```

## Invalidation

A wick through the structural stop does not by itself trigger the V1 stop.

```text
Call invalidation = completed 1m close < structural stop
Put invalidation  = completed 1m close > structural stop
```

## Opening-range re-entry

Before entry, a completed 5-minute close back inside the opening range cancels the setup.

## Setup expiry

If valid confirmation has not occurred within 30 minutes after the break-bar close, cancel the setup.

## VWAP cross

For each completed 5-minute bar, compare the closing price to VWAP at that bar's end.

A cross/side flip occurs only when the sign changes between consecutive completed bars.

Two or more side flips within the last four completed bars = CHOP.

## No trade

No trade is a valid system output, not a missed opportunity.
