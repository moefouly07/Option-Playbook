# Phase 1 Freeze Manifest

## Version

```text
Strategy: Confirmed Intraday Momentum
Version:  CIM-V1.0
Status:   FROZEN
Date:     2026-09-29
```

## Canonical strategy files

```text
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
strategy/OPTION_TRANSLATION.md
```

## Governance and state

```text
CURRENT_STATE.md
GOVERNANCE.md
CHANGELOG.md
DECISION_LOG.md
PROJECT_INSTRUCTIONS.md
```

## Test specification

```text
testing/BACKTEST_PROTOCOL.md
testing/TRADE_LOG_SCHEMA.md
testing/PILOT_PROTOCOL.md
```

## Training curriculum

```text
lessons/00_COURSE_MAP.md
lessons/01_MARKET_STRUCTURE_AND_CANDLES.md
lessons/02_OPENING_RANGE_AND_BREAKOUT.md
lessons/03_RETEST_CONFIRMATION_INVALIDATION.md
lessons/04_VWAP.md
lessons/05_ATR.md
lessons/06_VOLUME_AND_RELATIVE_VOLUME.md
lessons/07_OPTION_SELECTION_FOR_SCALPING.md
lessons/08_EXECUTION_SPREAD_SLIPPAGE.md
lessons/09_R_MAE_MFE.md
lessons/10_FULL_STRATEGY_REPLAY.md
lessons/11_PILOT_JOURNAL.md
lessons/12_SMA_AND_EMA.md
lessons/13_RSI.md
lessons/14_PDH_PDL_PREMARKET.md
lessons/15_EVENT_AND_SESSION_CONTEXT.md
lessons/QUICK_CHECKLIST.md
```

## Reference

```text
reference/GLOSSARY.md
reference/INDICATORS_NOT_ACTIVE_V1.md
```

## Freeze rule

The frozen branch/reference is a research snapshot.

Do not modify the V1 behavior in place after results are observed. Any change that affects trade eligibility, entry, stop, target, timing, contract selection, or exit creates a new strategy version.

Educational wording and typo fixes may be made on the development branch only if they do not alter behavior; the frozen snapshot remains the reproducibility reference.
