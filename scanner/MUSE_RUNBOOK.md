# Muse Scanner — Operations Runbook

Documenting a schedule is NOT the same as installing one.

## Before any run

Read `scanner/SCANNER_V1_1_SPEC.md` from GitHub and record the commit SHA. If the SHA differs from the last accepted SHA, stop: a spec change needs a new acceptance pass.

## Acceptance (once per spec version)

Follow `scanner/MUSE_ACCEPTANCE_TESTS.md` T0 to T7 in order. No recurring task before T7.

## Each scheduled run (after T7)

1. Confirm exchange calendar and session from an exchange source.
2. Fetch completed SIP daily bars (latest completed session) and same-day completed RTH SIP 5-minute bars with `end = now - 20 min`.
3. Run only the committed entry point:
   `python scanner/src/muse/run_scan_v11.py --run-type LIVE --as-of <today ET> --accepted-spec-sha <accepted> --accepted-impl-ref <accepted>`
   It classifies all 21 symbols, selects at most three or returns `NO_CANDIDATES`, and refuses on a spec, code, or data-freshness mismatch.
4. Add recorded-only fields: regime, catalysts with exact timestamps, earnings status, intraday status, `OPTIONS_NOT_VERIFIED`.
5. Validate the report against `scanner/OUTPUT_SCHEMA.json`.
6. Outcome-log rows are appended automatically to git-ignored `scanner/runs/outcome_log_live.csv` (one row per session and symbol).
7. Notify the user with the verdict, shortlist, and data-quality notes.

## Stop conditions

Disable the task and notify the user on: repeated authentication failure, missing same-day SIP data, schema-validation failure, or a spec SHA change.

## Never

Place orders, name option contracts, write to GitHub, print credentials, or apply a parameter change without a new scanner version.

## Expansion later

Phase 2: an authoritative, reproducible all-US-listed universe with deterministic screening and survivorship-safe handling. Phase 3: option-chain validation only with reliable, licensed options data and its own acceptance test. Neither is active.
