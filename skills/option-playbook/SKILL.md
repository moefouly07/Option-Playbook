---
name: option-playbook
description: Use for teaching, applying, testing, coding, or governing the Option Playbook and the frozen CIM-V1 SPY intraday options strategy.
---

# Option Playbook Skill

## Entry

Read:

```text
START_HERE.md
CURRENT_STATE.md
LEARNER_STATE.md
PROJECT_INSTRUCTIONS.md
```

Then load the minimum relevant files.

## Teaching mode

For a lesson request:

```text
lessons/00_COURSE_MAP.md
current lesson from LEARNER_STATE.md
reference/GLOSSARY.md when needed
```

Teach from zero unless the learner explicitly requests a skip.

Resume from the documented lesson phase.

Explain the whole lesson before testing.

Use:

```text
concept
→ simple example
→ mistake
→ CIM-V1 role
→ discussion
→ practice
```

After a lesson milestone, update `LEARNER_STATE.md`.

## Strategy mode

For rule interpretation:

```text
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
```

Frozen rules are authoritative.

If a chart creates an edge case not resolved by the specification, label it ambiguous and create a research/decision item. Do not pick the favorable interpretation.

## Backtest mode

Also read:

```text
GOVERNANCE.md
AGENTS.md
DATA_CONTRACT.md
testing/BACKTEST_PROTOCOL.md
testing/ACCEPTANCE_TESTS.md
testing/TRADE_LOG_SCHEMA.md
```

Implement acceptance tests before calculating strategy performance.

Keep Layer 1 underlying signal results separate from Layer 2 option translation.

## Live-example mode

For current SPY/options examples, use current reliable market sources when available.

State:

```text
timestamp ET
session
source/feed
quote quality
```

Use current data only to teach or illustrate the frozen rules, not to claim historical edge.

## Option data

Prefer actual executable two-sided quotes.

Without actual fills:

```text
entry = ask
exit = bid
```

Label OPRA, indicative, delayed, or modeled data.

Do not treat mark/last/mid as guaranteed fills.

## Governance

Any proposed change to:

```text
eligibility
entry
stop
target
timing
contract selection
exit
```

requires a new version after explicit adoption.

Record the proposal before testing it.

## Style

Egyptian Arabic for teaching and market discussion.

Keep English technical terms visible.

Be skeptical, concise, practical, and reproducible.
