# Muse Scanner — Beginner Operations Runbook

This runbook is for the Muse environment; documenting a schedule is NOT the same as installing one.

## One-off pilot
Ask Muse to read `scanner/README.md`, `scanner/SCANNER_V1_SPEC.md`, and `scanner/MUSE_RUNBOOK.md`. Inspect the installed `alpaca-market-data` skill. Check access and permissions before code edits. Implement the V1 constraints using the allowed read-only stock-data API; add no credential exposure or trading endpoints. Run a one-off scan and produce an honest report (including NO TRADE if necessary). Distinguish historical SIP >=15min delay from live IEX single venue. Report what worked and failed.

## After pilot acceptance — schedule
Request an autonomous recurring Muse task at 10:30 America/New_York on *US equity market sessions* (not blanket weekdays). Confirm the task in Muse's UI and its notifications. It should read the scanner spec on every run, generate one brief report or NO TRADE, and record data provenance. Do not execute trades or recommend contracts with no option data. Disable on repeated authentication failure or noisy data anomalies; report the failure.

## Audit fields per report
`scan_started_at_et`, `latest_completed_sip_bar_et`, `source_feed`, `market_session`, `universe_count`, `processed_count`, `symbols_with_data_gaps`, `candidates`, `no_trade_reason`, `audit_notes`.

## Expansion later
Phase 2: obtain an authoritative, current and reproducible all-US-listed universe source; apply deterministic price/dollar-volume screening; process batches with endpoint limits; avoid survivorship and pagination biases. Phase 3: option-chain validation only after reliable and appropriately licensed options data. These phases are not active.
