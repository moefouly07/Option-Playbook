# Option Playbook

A version-controlled research, teaching, and validation repository for developing repeatable US listed-options playbooks.

## Start here

New learner or new AI session:

```text
START_HERE.md
CURRENT_STATE.md
LEARNER_STATE.md
SYSTEM_PROMPT.md
```

Reusable skill:

```text
skills/option-playbook/SKILL.md
```

New-chat copy/paste helper:

```text
templates/NEW_CHAT_BOOTSTRAP.md
```

Project-completeness audit:

```text
PROJECT_AUDIT.md
```

## Current strategy

```text
Confirmed Intraday Momentum
CIM-V1.0
Underlying: SPY
Status: FROZEN FOR PHASE-1 TESTING
```

Frozen reproducibility branch:

```text
frozen/cim-v1.0
```

Development branch:

```text
main
```

The evidence state remains:

```text
INSUFFICIENT EVIDENCE TO DETERMINE POSITIVE EXPECTANCY
```

The frozen strategy is a hypothesis to test, not a proven edge.

## Project structure

### Operation and governance

- `START_HERE.md` — entry point for humans and AI sessions.
- `SYSTEM_PROMPT.md` — portable project prompt.
- `AGENTS.md` — coding/research-agent instructions.
- `PROJECT_INSTRUCTIONS.md` — project behavior and teaching rules.
- `CURRENT_STATE.md` — current project/research state.
- `LEARNER_STATE.md` — exact lesson and learner-resume state.
- `GOVERNANCE.md` — anti-overfitting and version-control rules.
- `ROADMAP.md` — phase plan.
- `PROJECT_AUDIT.md` — what is complete vs intentionally future work.
- `SECURITY.md` — secrets, broker-data, and vendor-data rules.
- `CHANGELOG.md` and `DECISION_LOG.md` — documented evolution.

### Strategy

- `strategy/PHASE_1_CIM_V1_FROZEN.md`
- `strategy/RULE_DEFINITIONS.md`
- `strategy/OPTION_TRANSLATION.md`

### Skills

- `SKILL_ROUTER.md`
- `skills/option-playbook/SKILL.md`

### Data

- `DATA_SOURCES.md` — roles for GitHub, Webull, Alpaca, AlphaStocks, and web research.
- `DATA_CONTRACT.md` — requirements for valid historical/live inputs.
- `data/README.md` — local dataset policy.

### Workflows

- `workflows/LIVE_SESSION_WORKFLOW.md` — exact live-data sequence for Webull / Alpaca / AlphaStocks usage.

### Testing

- `testing/BACKTEST_PROTOCOL.md`
- `testing/ACCEPTANCE_TESTS.md`
- `testing/IMPLEMENTATION_CHECKLIST.md`
- `testing/TRADE_LOG_SCHEMA.md`
- `testing/PILOT_PROTOCOL.md`

### Lessons

The course starts from zero.

Foundation lessons:

```text
00A Market Basics
00B Charts and Timeframes
00C Orders and Execution
00D Options Basics
00E Risk and Process
```

Then the CIM operating curriculum covers market structure, opening range, break/retest, VWAP, ATR, volume, option selection, execution, R/MAE/MFE, replay, and journaling.

SMA, EMA, RSI, previous-day levels, premarket levels, and event context are also taught, but are not active CIM-V1 entry filters.

### Templates

- `templates/REPLAY_WORKSHEET.md`
- `templates/LESSON_SESSION.md`
- `templates/BACKTEST_RUN_REPORT.md`
- `templates/NEW_CHAT_BOOTSTRAP.md`

### Discovery scanner

Separate, research-only track for Muse:

```text
scanner/README.md
scanner/SCANNER_V1_1_SPEC.md        SCANNER-V1.1, pre-registered, not validated
scanner/MUSE_ACCEPTANCE_TESTS.md    gate before any scheduling
python3 -m unittest discover -s scanner/tests -v
```

The scanner never modifies CIM-V1.0 and never executes trades.

## Research architecture

The project deliberately separates:

```text
Underlying signal
Option translation
Execution
Trader behavior
Trade outcome
```

A good chart is not automatically a good option contract, entry, execution, or trade.

## Backtest gate

Performance results should not be trusted until:

```text
DATA_CONTRACT.md is satisfied
AND
testing/ACCEPTANCE_TESTS.md passes
AND
testing/IMPLEMENTATION_CHECKLIST.md is complete
```

## Important

This repository is for research and education.

Do not change a frozen strategy after seeing results and present the modified version as an unbiased test.

Historical performance does not guarantee future results.
