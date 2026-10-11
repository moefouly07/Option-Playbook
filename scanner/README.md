# Muse Market Scanner

```text
Current version: SCANNER-V1.1
Status:          PRE-REGISTERED / NOT VALIDATED / NOT SCHEDULED
Scope:           fixed 21-symbol pilot watchlist, research only
Execution:       none. No orders, ever.
```

This directory defines an independent discovery workflow for Muse. It does not modify, replace, or validate frozen CIM-V1.0.

## Files

```text
SCANNER_V1_1_SPEC.md       canonical rules (read this first)
reference/scanner_rules.py executable definition of the rules (stdlib only)
src/muse/                  canonical copy of Muse's code (GitHub is the source of truth)
tools/                     ast_equivalence.py, implementation_ref.py
reference/make_fixtures.py how the synthetic golden fixtures were built
tests/                     unit tests, mutation tests, 21 synthetic golden fixtures (year 2099)
OUTPUT_SCHEMA.json         required shape of every run report
MUSE_ACCEPTANCE_TESTS.md   T0-T7 gate before any scheduling
ACCEPTANCE_LOG.md          result of every acceptance attempt
MUSE_SETUP.md              connecting Muse (beginner)
MUSE_RUNBOOK.md            operating procedure
SCANNER_RULES.md           one-page plain-language summary
SCANNER_V1_SPEC.md         SUPERSEDED V1.0 spec, kept for history
```

## Labels

```text
CONFIRMED_SETUP | RESEARCH_PASS | WATCH | REJECT | INSUFFICIENT_DATA | BENCHMARK
```

`TRADE_READY` is not a scanner label. No scanner output authorizes a trade.

## Run the tests

```bash
python3 -m unittest discover -s scanner/tests -v
```

## Gates

1. The reference tests pass.
2. Muse passes T0-T6 in `MUSE_ACCEPTANCE_TESTS.md`.
3. A human sign-off is recorded in `DECISION_LOG.md`.
4. Only then is a recurring task created (T7).

## Integrity

Every rule in V1.1 was written after seeing V1.0 pilot output (`DECISION_LOG.md` D-009). The 2026-10-09 data is in-sample. No scanner edge is claimed. Options are `OPTIONS_NOT_VERIFIED` until a licensed option-chain feed passes its own acceptance test.
