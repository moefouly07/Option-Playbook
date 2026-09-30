# Forward Pilot Protocol

## Purpose

The pilot is for debugging execution and measuring real-world friction.

It is **not** the primary proof of statistical edge.

## Initial pilot

Target:

```text
20 completed trades
```

Use the frozen V1 rules. Do not modify rules mid-pilot because of wins or losses.

## What the pilot tests

- Can the trader identify ORH/ORL consistently?
- Are retest and confirmation rules interpreted identically each time?
- Can the correct contract be selected quickly?
- What is real bid/ask friction?
- What is actual fill slippage?
- How often does manual reaction delay matter?
- How often does the trader violate a rule?
- Does the broker support the required exit workflow?

## Forward calibration

After the debug pilot, a larger forward sample can calibrate execution:

```text
50+ trades
```

This still should not automatically be described as proof of a small edge.

## Cash-account note

For a cash account, the main operational constraint is settled cash and the broker's settlement/use-of-funds rules rather than the historical margin-account PDT rule.

Broker implementation and account restrictions can change. Verify the current broker rules before live trading.

## Discipline

If a setup does not satisfy the frozen definition, mark:

```text
NO TRADE
```

Do not record a discretionary trade as a V1 trade.
