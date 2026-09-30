# Start Here

This is the entry point for a new ChatGPT, Claude, Codex, or other AI session.

## If you are the learner

Start with:

1. `CURRENT_STATE.md`
2. `lessons/00_COURSE_MAP.md`
3. the next lesson in sequence

The curriculum now starts from zero. Do not skip foundational lessons unless the learner explicitly asks to.

## If you are an AI assistant

Read only the minimum files needed.

### Teaching request

Read:

```text
CURRENT_STATE.md
PROJECT_INSTRUCTIONS.md
lessons/00_COURSE_MAP.md
the current lesson file
```

### Strategy-rule question

Read:

```text
CURRENT_STATE.md
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
```

### Backtest/coding request

Read:

```text
CURRENT_STATE.md
GOVERNANCE.md
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
testing/BACKTEST_PROTOCOL.md
testing/ACCEPTANCE_TESTS.md
DATA_CONTRACT.md
```

### Current-market application

Also obtain fresh market data and clearly state:

```text
timestamp
US Eastern Time
market session
live / delayed / indicative / unknown
```

Do not use a current chart example as proof that the strategy has an edge.

## New-chat shortcut

If the assistant can access this GitHub repository, say:

```text
Read START_HERE.md and CURRENT_STATE.md from
moefouly07/Option-Playbook.
Follow SYSTEM_PROMPT.md and the relevant skill.
Continue from the current learner state without changing frozen rules.
```

If the assistant cannot access GitHub, paste `SYSTEM_PROMPT.md` into the project/system instructions and upload the relevant files.

## Canonical freeze

The reproducibility snapshot is:

```text
frozen/cim-v1.0
```

Development continues on:

```text
main
```
