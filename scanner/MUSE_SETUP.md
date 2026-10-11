# Muse Beginner Setup

## Connection

In Meta Muse, inspect Settings > Connectors for GitHub (labels may vary). Authorize only this repository, read-only, when possible. Never paste personal-access tokens, passwords, or secrets into a chat.

## First read-only test

```text
Read scanner/README.md, scanner/SCANNER_V1_1_SPEC.md, START_HERE.md and CURRENT_STATE.md in moefouly07/Option-Playbook.
Tell me which files you actually opened and the commit SHA.
Do not change any content or settings.
```

## Acceptance before automation

Run the staged tests in `scanner/MUSE_ACCEPTANCE_TESTS.md` (T0-T6). The scope is the fixed 21-symbol pilot watchlist in the spec, not the whole market.

## Schedule (not installed until T7)

```text
10:30 America/New_York, on US equity exchange trading days only
```

Not plain weekdays: exchange holidays are skipped and early-close days are handled by the calendar. A pre-market time such as 09:00 ET is not valid for V1.1 because the run needs same-day completed RTH bars. Create the task only after T0-T6 pass and the human sign-off is logged.

## Validate

Check repository access, a one-time run, the scheduled-task entry, timezone, notification setting, and logs. Documentation alone never proves automation is active.

## Security

Read-only research permission only. Keep brokerage trading disabled. Treat this repository as publicly readable (`SECURITY.md`).
