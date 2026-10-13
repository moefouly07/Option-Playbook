# Changelog

## CIM-V1.0 clarification C-002 — 2026-10-12

No CIM rule changed. C-002 pins the ATR5 series construction (3 previous sessions plus the current one, gap-inclusive Wilder true range, mean-of-14 seed) with test A27 (D-025). T7b logged PASS.

---

## CIM-V1.0 clarification C-001 — 2026-10-12

No CIM rule changed. Added `strategy/CLARIFICATIONS.md` (C-001: ATR5 current at every evaluated timestamp; C-002 seeding pending) and acceptance tests A25-A26 (D-024). Scanner sign-off renumbered to D-025.

---

## Data-availability fix — 2026-10-12

No classification rule changed. Daily bars are never requested for the current ET date (`latest_available_session`); outcomes job moved to 09:15 ET; fake CLI models the data plan; pipeline_sim 34 scenarios (D-023, KI-004). implementation_ref `sha256:06b4d1c8860ce1400f403205b288e03236ca059d812b51f8b1fe852cc3fc30ca`.

---

## Scheduling package — 2026-10-12

No classification rule changed. Added `scheduled_job.py`, `outcome_tools.py`, `pipeline_gates.py`; `scan_time_price`; pre-registered outcome definitions and scheduling (spec sections 11 and 13); fixed KI-001, KI-002, KI-003; pipeline_sim extended to 30 scenarios; acceptance steps T7a-T7d (D-022). implementation_ref `sha256:0c31a73ebac963f4f75a936a59c2ce92fe415c4674426ac4c2f5d76e7ab19a6b`.

---

## Live pipeline review — 2026-10-11

No classification rule changed. Added Muse's reviewed live pipeline (`run_scan_v11.py`, `data_adapter.py`) with freshness, spec, clean-tree and implementation gates; outcome logs moved to git-ignored `scanner/runs/`; pre-registered 130-session history window; `scanner/tests/pipeline_sim/` (13 scenarios); acceptance step T1c-2 (D-021).

---

## Test hardening — 2026-10-11

No rule changed. Fixtures 14 → 21 synthetic symbols; 12-mutant sensitivity test; canonical `scanner/src/muse/` copy of Muse's rules engine and harness; `scanner/tools/ast_equivalence.py` and `scanner/tools/implementation_ref.py`; manifest-based `implementation_ref`; acceptance steps T1b-2 and T1c (D-019).

---

## Deployment correction — 2026-10-11

No rule changed. Completed the SCANNER-V1.1 upload: committed the `scanner/` tree (spec, reference implementation, tests, fixtures, schema, acceptance tests), removed the stray root `scanner-v1.1.patch` and root `MUSE_ACCEPTANCE_TESTS.md`, added `scanner/ACCEPTANCE_LOG.md` and D-018.

---

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
