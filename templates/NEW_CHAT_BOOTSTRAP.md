# New Chat Bootstrap

Copy this into a new conversation when the model has GitHub access:

```text
Use the GitHub repository moefouly07/Option-Playbook as the canonical source.

Read START_HERE.md and CURRENT_STATE.md first.
Then follow SYSTEM_PROMPT.md and skills/option-playbook/SKILL.md.

Important:
- teach the curriculum from zero;
- explain the full lesson before testing me;
- do not silently change CIM-V1 frozen rules;
- only load files relevant to the current task;
- keep strategy validation separate from live examples;
- continue from the documented learner state.

Tell me what the current phase is and continue with the next documented lesson.
```

If GitHub access is unavailable, paste `SYSTEM_PROMPT.md` into project instructions and upload the current-state, strategy, and lesson files.
