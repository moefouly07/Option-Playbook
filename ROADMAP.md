# Roadmap

## Phase 0 — Foundations

Status: ACTIVE

Goal: learn market, chart, order, option, and risk basics from zero.

Files:

```text
lessons/00A_MARKET_BASICS_FROM_ZERO.md
lessons/00B_CHARTS_AND_TIMEFRAMES_FROM_ZERO.md
lessons/00C_ORDERS_AND_EXECUTION_FROM_ZERO.md
lessons/00D_OPTIONS_BASICS_FROM_ZERO.md
lessons/00E_RISK_AND_PROCESS_FROM_ZERO.md
```

Exit condition: learner can explain the basic market vocabulary and read a simple chart without using indicators as magic signals.

## Phase 1 — CIM Operating Skills

Goal: complete lessons 01–11 and operate the frozen strategy on replay.

Exit condition: repeated replay decisions match the frozen rules with minimal interpretation drift.

## Phase 2 — Historical Signal Engine

Goal: implement CIM-V1 Layer 1 on consolidated SPY one-minute data.

Required before performance output:

```text
DATA_CONTRACT.md satisfied
testing/ACCEPTANCE_TESTS.md passing
testing/IMPLEMENTATION_CHECKLIST.md complete
```

Deliverables:

```text
reproducible code
synthetic fixtures
test report
run metadata
Layer-1 results
```

## Phase 3 — Option Translation

Goal: translate qualifying signals to actual or clearly modeled next-day SPY option outcomes.

Priority:

```text
historical two-sided quotes
>
documented snapshots
>
labeled model
```

Deliverables include spread/slippage and underlying-R vs option-R comparisons.

## Phase 4 — Forward Pilot

Goal: debug human execution and collect real fills.

Initial target:

```text
20 trades
```

Then larger calibration:

```text
50+ trades
```

These samples calibrate execution; they are not automatically proof of a small edge.

## Phase 5 — Research Extensions

Possible new hypotheses:

```text
0DTE
minimum structural-stop / ATR filters
RSI
EMA / SMA
relative volume
PDH / PDL
premarket levels
event filters
alternative targets
alternative time windows
```

Each material rule change requires a new version and out-of-sample validation.

## Parallel track — Discovery scanner

Independent of the CIM phases above. Never changes CIM-V1.

```text
S1  SCANNER-V1.1 acceptance (T0-T7)          ACTIVE
S2  Scheduled daily research runs + outcome log
S3  Authoritative full-market universe (Phase-2 discovery)
S4  Licensed option-chain validation with its own acceptance test
S5  Prospective evaluation of logged outcomes (pre-registered horizons +1/+5/+10)
```

Each rule change is a new scanner version with a decision-log entry.
