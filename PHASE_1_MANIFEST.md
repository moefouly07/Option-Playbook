# Phase 1 Freeze Manifest

## Frozen version

```text
Strategy: Confirmed Intraday Momentum
Version:  CIM-V1.0
Status:   FROZEN
Date:     2026-09-29
Branch:   frozen/cim-v1.0
```

The frozen branch is the reproducibility snapshot.

## Files inside the frozen research snapshot

### Canonical strategy

```text
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
strategy/OPTION_TRANSLATION.md
```

### Governance/state at freeze time

```text
CURRENT_STATE.md
GOVERNANCE.md
CHANGELOG.md
DECISION_LOG.md
PROJECT_INSTRUCTIONS.md
```

### Test specification at freeze time

```text
testing/BACKTEST_PROTOCOL.md
testing/TRADE_LOG_SCHEMA.md
testing/PILOT_PROTOCOL.md
```

### Training content at freeze time

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

## Post-freeze operational layer on main

After the strategy snapshot was frozen, the development branch added operational and educational infrastructure that **does not change CIM-V1 behavior**:

```text
START_HERE.md
SYSTEM_PROMPT.md
AGENTS.md
SKILL_ROUTER.md
skills/option-playbook/SKILL.md
DATA_SOURCES.md
DATA_CONTRACT.md
testing/ACCEPTANCE_TESTS.md
testing/IMPLEMENTATION_CHECKLIST.md
ROADMAP.md
templates/
lessons/00A–00E foundation lessons
```

These files improve reproducibility, model onboarding, implementation safety, and beginner education.

They are not retroactively part of the original frozen snapshot.

## Freeze rule

Do not modify the frozen branch.

Any change that affects trade eligibility, entry, stop, target, timing, contract selection, or exit requires a new strategy version.

Educational wording, tooling, tests, and documentation may evolve on `main` as long as they do not silently change the strategy behavior.
