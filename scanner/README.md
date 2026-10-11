# Muse Market Scanner — Pilot

Status: DESIGN / NOT DEPLOYED

This directory defines an independent research and discovery workflow for Muse. It does not modify, replace, or validate frozen CIM-V1.0 rules.

## Objective

Find up to three liquid US equity/ETF opportunities for further investigation. A scan can return NO TRADE. Research does not authorize orders.

## Getting started

1. Connect Muse to GitHub using only the repository permissions required.
2. Ask Muse to read this file and MUSE_SETUP.md.
3. Run a one-time read-only demonstration scan and validate timestamps, sources, and candidate logic.
4. Only after checking results, create a daily recurring research task and confirm its schedule in Muse.
5. Never enable brokerage order placement or repository writes as part of scanner research.

## Research flow

deterministic market filter -> catalysts and market regime -> technical structure -> bear-case challenge -> options quality if data available -> shortlist.

## Source integrity

For each candidate log ticker, retrieval time ET, session, feed/vendor, delayed/live/unknown quote status, evidence links, technical trigger and invalidation, option liquidity if supported, and missing data.

Do not manufacture IV, Greeks, volume, spreads, probabilities, or historical performance. Do not claim a scanner edge before prospective evaluation.

## Separation

The existing CIM-V1.0 strategy remains frozen. This directory is experimental discovery only.
