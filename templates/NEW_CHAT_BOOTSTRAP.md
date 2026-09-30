# New Chat Bootstrap

Copy this into a new conversation when the model has GitHub access:

```text
Use the GitHub repository moefouly07/Option-Playbook as the canonical source.

Read START_HERE.md, CURRENT_STATE.md, and LEARNER_STATE.md first.
Then follow SYSTEM_PROMPT.md and skills/option-playbook/SKILL.md.

Important:
- teach the curriculum from zero;
- continue from the exact lesson phase in LEARNER_STATE.md;
- explain the full lesson before testing me;
- do not silently change CIM-V1 frozen rules;
- only load files relevant to the current task;
- keep strategy validation separate from live examples;
- update LEARNER_STATE.md after meaningful lesson progress.

Tell me the documented current lesson and continue from there.
```

If GitHub access is unavailable, paste `SYSTEM_PROMPT.md` into project instructions and upload:

```text
CURRENT_STATE.md
LEARNER_STATE.md
the relevant strategy file
the current lesson file
```
