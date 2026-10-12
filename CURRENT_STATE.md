# Current State

## Project

Option Playbook

## Active research

- Strategy: Confirmed Intraday Momentum
- Version: CIM-V1.0
- Status: FROZEN FOR PHASE-1 TESTING
- Frozen reference: `frozen/cim-v1.0`
- Development branch: `main`
- Underlying: SPY
- Signal data target: consolidated 1-minute RTH data; 5-minute bars derived from the same source
- Initial option translation: next-trading-day expiry, not 0DTE
- Primary option target: ATM / near-ATM, absolute delta 0.40–0.60

## Evidence state

```text
INSUFFICIENT EVIDENCE TO DETERMINE
```

No historical backtest has yet established positive expectancy.

A screenshot, live example, or small pilot sample is not proof of edge.

## Current learner instruction

As of 2026-09-29:

```text
START THE CURRICULUM FROM ZERO
```

Do not rely on prior experience to skip foundations unless the learner explicitly asks to skip a lesson.

Preferred learning sequence:

```text
full explanation
→ discussion
→ examples
→ practical checks
→ replay
```

## Active work order

1. Complete foundation lessons 00A–00E.
2. Complete CIM operating lessons 01–09.
3. Run guided replay in lesson 10.
4. Learn pilot journaling in lesson 11.
5. Only then implement Layer 1.
6. Pass the synthetic acceptance tests before performance analysis.
7. Run multi-year historical signal testing.
8. Translate qualifying signals into option P/L with actual quotes when available.
9. Run a forward pilot to calibrate execution.

## Operational additions

The main branch now includes:

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
```

These improve operation, teaching, and implementation safety without changing frozen CIM-V1 behavior.

## Discovery scanner (separate track)

```text
Scanner:  Muse discovery scanner
Version:  SCANNER-V1.1
Status:   PRE-REGISTERED / NOT VALIDATED / NOT SCHEDULED
Spec:     scanner/SCANNER_V1_1_SPEC.md
Gate:     scanner/MUSE_ACCEPTANCE_TESTS.md (T0-T7)
```

The scanner is research-only discovery on a fixed 21-symbol watchlist. It never changes CIM-V1.0 and never authorizes trades. V1.1 rules were written after the V1.0 pilot (DECISION_LOG D-009); 2026-10-09 data is in-sample.

Next scanner action: T0-T6 passed (2026-10-12). Adopt the D-022 scheduling package (T7a), migrate the live outcome log (T7b), supervised run-once of each job (T7c), owner sign-off D-023 and recurring tasks (T7d).

## Version-control rule

Do not edit frozen V1 behavior after observing performance.

Any behavioral change requires:

```text
decision log
new version
new validation plan
```
