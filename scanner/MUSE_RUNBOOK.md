# Muse Scanner — Operations Runbook

Documenting a schedule is NOT the same as installing one.

## Before any run

Read `scanner/SCANNER_V1_1_SPEC.md` from GitHub and record the commit SHA. If the SHA differs from the last accepted SHA, stop: a spec change needs a new acceptance pass.

## Acceptance (once per spec version)

Follow `scanner/MUSE_ACCEPTANCE_TESTS.md` T0 to T7 in order. No recurring task before T7.

## Each scheduled run (after T7)

1. Confirm exchange calendar and session from an exchange source.
2. Fetch completed SIP daily bars (latest completed session) and same-day completed RTH SIP 5-minute bars with `end = now - 20 min`.
3. Classify all 21 symbols with V1.1; select at most three; or `NO_CANDIDATES`.
4. Add recorded-only fields: regime, catalysts with exact timestamps, earnings status, intraday status, `OPTIONS_NOT_VERIFIED`.
5. Validate the report against `scanner/OUTPUT_SCHEMA.json`.
6. Append outcome-log rows (spec section 11).
7. Notify the user with the verdict, shortlist, and data-quality notes.

## Stop conditions

Disable the task and notify the user on: repeated authentication failure, missing same-day SIP data, schema-validation failure, or a spec SHA change.

## Never

Place orders, name option contracts, write to GitHub, print credentials, or apply a parameter change without a new scanner version.

## Expansion later

Phase 2: an authoritative, reproducible all-US-listed universe with deterministic screening and survivorship-safe handling. Phase 3: option-chain validation only with reliable, licensed options data and its own acceptance test. Neither is active.
