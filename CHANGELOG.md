# Changelog

## SCANNER-V1.1 — 2026-10-10

Status: **PRE-REGISTERED / NOT VALIDATED / NOT SCHEDULED**

No CIM-V1 behavioral rule changed. `strategy/` is untouched.

Added:

- `scanner/SCANNER_V1_1_SPEC.md` — canonical V1.1 rules with an explicit post-pilot honesty statement;
- `scanner/reference/scanner_rules.py` — executable rule definition, standard library only;
- `scanner/reference/make_fixtures.py` and `scanner/tests/` — synthetic golden fixtures and 14 unit tests;
- `scanner/OUTPUT_SCHEMA.json` — required run-report shape;
- `scanner/MUSE_ACCEPTANCE_TESTS.md` — staged T0–T7 gate before scheduling.

Changed:

- single label enum; `TRADE_READY` removed from scanner vocabulary (D-010);
- SPY benchmark-only (D-011);
- ATR-bounded SMA20 zone and pullback confirmation with volume floor (D-012);
- positive RS required for pullbacks (D-013);
- extension cap and block (D-014);
- fixed, reported correlation method (D-015);
- regime, catalysts, RSI, earnings, intraday status recorded only (D-016);
- `scanner/MUSE_SETUP.md` schedule corrected from 09:00 ET to 10:30 ET on exchange trading days;
- `scanner/SCANNER_V1_SPEC.md` marked superseded;
- scanner linked from README, START_HERE, CURRENT_STATE, SKILL_ROUTER, ROADMAP, PROJECT_AUDIT, AGENTS, SECURITY, DATA_SOURCES.

---

## Operational / education update — 2026-09-29

No CIM-V1 behavioral rule changed.

Added:

- new-chat onboarding via `START_HERE.md`;
- portable `SYSTEM_PROMPT.md`;
- `AGENTS.md` for coding/research agents;
- reusable `skills/option-playbook/SKILL.md`;
- `SKILL_ROUTER.md`;
- dedicated `LEARNER_STATE.md` for exact lesson resumption;
- `DATA_SOURCES.md` and `DATA_CONTRACT.md`;
- `workflows/LIVE_SESSION_WORKFLOW.md` for Webull / Alpaca / AlphaStocks usage;
- synthetic `testing/ACCEPTANCE_TESTS.md`;
- backtest implementation checklist;
- project roadmap and project audit;
- replay, lesson-session, backtest-report, and new-chat templates;
- beginner foundation lessons 00A–00E;
- `SECURITY.md`, `.gitignore`, and local-data policy.

Learner instruction changed to:

```text
START FROM ZERO
```

This is a teaching-state change, not a strategy-rule change.

---

## CIM-V1.0 — 2026-09-29

Status: **FROZEN FOR PHASE-1 TESTING**

Initial research baseline created.

Key decisions:

- SPY is the first research instrument.
- Opening range is 09:30–09:55 ET.
- Break requires a 5-minute close beyond the opening-range boundary.
- Retest uses a ±0.25 × ATR14-on-5m band around the broken level.
- A wick through the level is allowed if it stays inside the retest band and the 1-minute bar closes back on the correct side.
- A wick beyond the outer retest-band boundary cancels the setup.
- Confirmation is a 1-minute close beyond the retest bar's confirmation level.
- Entry is the next 1-minute bar after confirmation.
- Structural invalidation is based on the underlying.
- True R remains the structural risk distance. No artificial ATR floor is active in V1.
- Stop-distance / ATR is recorded for later analysis.
- Underlying target is 1.5R.
- Setup expires after 30 minutes without a valid retest/confirmation.
- Last entry is 11:45 ET.
- Time exit is 12:30 ET.
- Maximum one trade per direction and two trades per day.
- VWAP is not an independent directional confirmation in V1; it is used for the pre-registered chop rule and recorded as context.
- Next-trading-day options are used for the initial option translation/pilot; 0DTE is deferred.
- RSI, SMA, EMA, PDH/PDL, premarket levels, relative volume, and event tags are recorded/researched but are not active V1 filters.
