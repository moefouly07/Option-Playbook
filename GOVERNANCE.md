# Governance

## Purpose

This file prevents the playbook from drifting after results are seen.

## Rule hierarchy

1. Data integrity and reproducibility
2. Frozen strategy specification
3. Pre-registered testing protocol
4. Training notes
5. Research ideas and optional indicators

Training material may explain more concepts than the frozen strategy uses. A lesson does not automatically create a strategy rule.

## Freeze policy

A version marked **FROZEN** is not edited to improve its historical result.

If a rule needs to change:

1. Record the reason in `DECISION_LOG.md`.
2. Add a new entry to `CHANGELOG.md`.
3. Create a new version identifier.
4. Keep the old version available.
5. Test the new version on data not used to choose the change.

## No silent optimization

Do not tune thresholds after seeing the answer and then report the tuned result as an unbiased test.

Examples:

- changing the retest band from 0.25 ATR to 0.35 ATR because the result looks better;
- changing the last-entry time after reviewing losing trades;
- adding RSI only after noticing it filters specific losses.

Those are new hypotheses and need new validation.

## Active vs recorded-only variables

A variable can be:

- **ACTIVE** — changes whether a trade is taken.
- **RECORDED ONLY** — logged for later analysis but cannot change the V1 decision.
- **SECONDARY PRE-REGISTERED** — one named comparison defined before the test.
- **FUTURE RESEARCH** — not part of V1.

## Data integrity

Use consolidated market data when the rule depends on volume or VWAP.

If data is venue-limited, delayed, modeled, or incomplete, label it.

Never mix actual option quotes with modeled option prices without identifying which is which.

## Research conclusion

A small forward sample can debug the system and estimate execution friction. It cannot by itself prove a small statistical edge.

The final conclusion must report sample definition, sample size, date range, execution assumptions, costs, out-of-sample handling, and material limitations.
