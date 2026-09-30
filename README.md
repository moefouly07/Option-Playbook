# Option Playbook

A version-controlled research and training repository for developing, testing, and learning repeatable listed-options trading playbooks.

## Current project

**Phase 1:** Confirmed Intraday Momentum (CIM)  
**Research instrument:** SPY  
**Status:** V1 baseline frozen for testing  
**Primary goal:** Test whether a mechanically defined opening-range break/retest signal has positive expectancy before adding discretionary filters.

The project deliberately separates:

1. **Signal quality on the underlying**
2. **Option-contract translation and execution**
3. **Trader training and replay practice**
4. **Forward/pilot execution data**

A good chart is not automatically a good option trade.

## Repository map

- `strategy/` — frozen rules and exact definitions.
- `testing/` — backtest, pilot, logging, and validation protocols.
- `lessons/` — practical training required to operate the playbook.
- `reference/` — glossary, indicator references, and concepts that are recorded but are not active V1 filters.
- `CURRENT_STATE.md` — current phase, version, and learner/research status.
- `CHANGELOG.md` — every strategy change after the freeze.
- `GOVERNANCE.md` — rules preventing silent rule changes and overfitting.

## Phase 1 philosophy

The baseline is intentionally simple:

```text
Wait for the opening range
→ Require a 5-minute close beyond it
→ Wait for a mechanical retest
→ Require confirmation
→ Enter only after confirmation
→ Stop on underlying structural invalidation
→ Measure the option separately
```

No trend means no trade.

Indicators such as RSI, SMA, EMA, relative volume, previous-day levels, and premarket levels are taught and logged where useful, but they are **not active V1 entry filters** unless a future version change is pre-registered and documented.

## Research layers

### Layer 1 — Underlying signal

Use consolidated SPY 1-minute data over a multi-year sample. Build 5-minute bars from the same data source. Test the frozen signal mechanically and record underlying R, MAE, MFE, time in trade, and context variables.

### Layer 2 — Option translation

Translate qualifying signals to the specified option-selection method using actual historical option data when available. If only a model is available, label model-derived results separately from observed quotes/fills. Include bid/ask friction and slippage assumptions.

### Pilot

Use a small forward sample to debug rule interpretation and measure real execution. A pilot is not proof of edge.

## Important

This repository is for research and education. Historical performance does not guarantee future results. Rules should not be changed after seeing test outcomes without creating a new version and an out-of-sample validation plan.
