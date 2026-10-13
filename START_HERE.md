# Start Here

This is the entry point for a new ChatGPT, Claude, Codex, or other AI session.

## If you are the learner

Start with:

1. `CURRENT_STATE.md`
2. `LEARNER_STATE.md`
3. `lessons/00_COURSE_MAP.md`
4. the current lesson in `LEARNER_STATE.md`

The curriculum starts from zero. Do not skip foundational lessons unless the learner explicitly asks to.

## If you are an AI assistant

Read only the minimum files needed.

### Teaching request

Read:

```text
CURRENT_STATE.md
LEARNER_STATE.md
PROJECT_INSTRUCTIONS.md
lessons/00_COURSE_MAP.md
the current lesson file
```

Continue from the exact `Current lesson phase` in `LEARNER_STATE.md`.

Do not ask the learner where the course stopped if the state file is current.

### Strategy-rule question

Read:

```text
CURRENT_STATE.md
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
strategy/CLARIFICATIONS.md
```

### Backtest/coding request

Read:

```text
CURRENT_STATE.md
GOVERNANCE.md
AGENTS.md
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
strategy/CLARIFICATIONS.md
testing/BACKTEST_PROTOCOL.md
testing/ACCEPTANCE_TESTS.md
DATA_CONTRACT.md
```

### Current-market application

Also read:

```text
workflows/LIVE_SESSION_WORKFLOW.md
DATA_SOURCES.md
```

Then obtain fresh market data and clearly state:

```text
timestamp
US Eastern Time
market session
source/feed
live / delayed / indicative / unknown
```

Do not use a current chart example as proof that the strategy has an edge.

### Scanner / Muse request

Read:

```text
CURRENT_STATE.md
scanner/README.md
scanner/SCANNER_V1_1_SPEC.md
scanner/MUSE_ACCEPTANCE_TESTS.md
DECISION_LOG.md (D-009 onward)
```

The scanner is separate from CIM-V1. Never let a scanner label become a CIM entry.

## New-chat shortcut

If the assistant can access this GitHub repository, say:

```text
Use moefouly07/Option-Playbook as the canonical source.
Read START_HERE.md, CURRENT_STATE.md, and LEARNER_STATE.md first.
Follow SYSTEM_PROMPT.md and skills/option-playbook/SKILL.md.
Continue from the documented learner phase without changing frozen rules.
```

If the assistant cannot access GitHub, paste `SYSTEM_PROMPT.md` into the project/system instructions and upload the relevant state/strategy/lesson files.

## Canonical freeze

The reproducibility snapshot is:

```text
frozen/cim-v1.0
```

Development continues on:

```text
main
```
