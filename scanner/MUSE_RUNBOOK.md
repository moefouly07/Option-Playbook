# Muse Scanner — Operations Runbook

Documenting a schedule is NOT the same as installing one.

## Before any run

Read `scanner/SCANNER_V1_1_SPEC.md` from GitHub and record the commit SHA. If the SHA differs from the last accepted SHA, stop: a spec change needs a new acceptance pass.

## Acceptance (once per spec version)

Follow `scanner/MUSE_ACCEPTANCE_TESTS.md` T0 to T7 in order. No recurring task before T7.

## Each scheduled run (after T7)

Every task clones the repository fresh and runs `scanner/src/muse/scheduled_job.py` with the accepted spec SHA and implementation_ref (task body in `MUSE_ACCEPTANCE_TESTS.md`, T7). The job checks the ET window, the NYSE calendar and all gates, runs its mode, and prints one JSON line; the task posts it verbatim when `send` is true. State lives in `~/workspace/market-scanner/state/` (outcome log, reports, health, HALT).

## Stop conditions

Two consecutive failures create `state/HALT`; jobs then do nothing until a human fixes the cause and deletes it. A spec or code change makes every job refuse until new accepted values are adopted.

## Never

Place orders, name option contracts, write to GitHub, print credentials, or apply a parameter change without a new scanner version.

## Expansion later

Phase 2: an authoritative, reproducible all-US-listed universe with deterministic screening and survivorship-safe handling. Phase 3: option-chain validation only with reliable, licensed options data and its own acceptance test. Neither is active.
