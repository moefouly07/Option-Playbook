# AGENTS.md

Instructions for coding/research agents working in this repository.

## Read order

Before changing code or research artifacts:

```text
START_HERE.md
CURRENT_STATE.md
GOVERNANCE.md
```

If work touches CIM-V1 logic, also read:

```text
strategy/PHASE_1_CIM_V1_FROZEN.md
strategy/RULE_DEFINITIONS.md
testing/ACCEPTANCE_TESTS.md
DATA_CONTRACT.md
```

## Hard constraints

- Do not edit `frozen/cim-v1.0`.
- Do not change V1 behavior on `main` without an explicit version change.
- Do not optimize thresholds after seeing backtest results and call the result unbiased.
- Do not infer missing market data.
- Do not substitute underlying returns for option returns when reporting option performance.
- Do not use in-progress bars where the rule requires completed bars.
- Preserve U.S. Eastern Time semantics and exchange-calendar handling.
- Keep actual quotes/fills separate from modeled values.

## Scanner code

Scanner work follows `scanner/SCANNER_V1_1_SPEC.md`. Any scanner implementation must reproduce `scanner/tests/fixtures/expected_output.json` before its output is used. Never edit fixtures or expected outputs to make an implementation pass. Scanner code contains no trading or order endpoints.

## Implementation style

Prefer small pure functions for:

```text
opening-range construction
5m aggregation
Wilder ATR
break detection
retest-state machine
confirmation
chop classification
entry/stop/target
MAE/MFE
option-contract selection
execution accounting
```

Each rule function should be testable with synthetic fixtures.

## Tests before results

Implement `testing/ACCEPTANCE_TESTS.md` before running a performance backtest.

If an acceptance case is ambiguous, stop and document the ambiguity instead of choosing the interpretation that improves performance.

## Outputs

Backtest outputs must contain:

```text
strategy version
data source
date range
timezone
sample size
missing-data handling
friction assumptions
in-sample/out-of-sample status
```
