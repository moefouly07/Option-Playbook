# Current State

## Project

Option Playbook

## Active research

- Strategy: Confirmed Intraday Momentum
- Version: CIM-V1.0
- Status: FROZEN FOR PHASE-1 TESTING
- Underlying: SPY
- Signal data: consolidated 1-minute RTH data; 5-minute bars derived from the same source
- Option expiry for V1 translation/pilot: next trading day, not 0DTE
- Primary option target: ATM / near-ATM, absolute delta 0.40–0.60

## Evidence state

Insufficient evidence to determine whether the strategy has positive expectancy.

The current strategy is a pre-registered hypothesis. No historical result, screenshot, or pilot trade should be treated as proof of edge.

## Active work order

1. Learn the operating concepts in `lessons/`.
2. Implement Layer 1 on SPY underlying data.
3. Run a rules/debug pilot on historical replay before evaluating performance.
4. Run a multi-year historical signal test.
5. Translate qualifying signals into option P/L with real historical quotes when available.
6. Run a small forward pilot to measure actual spread/slippage and rule consistency.

## Learner state

- Options mechanics: prior experience; do not repeat beginner material unnecessarily.
- Current focus: intraday structure, opening range, retest mechanics, VWAP context, ATR, volume, option selection, and execution.
- Preferred learning mode: explain the complete lesson first, then discuss, then test with chart/replay cases.

## Version-control rule

Do not edit the frozen V1 rules after observing performance. Any behavioral rule change creates a new version and must be logged in `CHANGELOG.md` and `DECISION_LOG.md`.
