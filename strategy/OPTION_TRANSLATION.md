# Option Translation — Phase 1

The underlying signal and the option trade are evaluated separately.

## Baseline contract

For the initial translation and forward pilot:

```text
Underlying: SPY
Expiry: next trading day
Target absolute delta: 0.40–0.60
Preference: contract with |delta| closest to 0.50
Type: Call for call signal, Put for put signal
```

If two candidates are equally close to 0.50 delta, prefer the tighter percentage spread. If still tied, prefer the higher open interest.

## Quote handling

Without an actual fill:

```text
Entry = ASK
Exit  = BID
```

The midpoint, mark, and last trade are references only.

Record:

- bid
- ask
- midpoint
- absolute spread
- percentage spread
- volume
- open interest
- delta
- gamma
- theta
- vega
- IV
- quote timestamp
- data source

Do not fabricate missing fields.

## Historical option data hierarchy

1. Actual historical NBBO/quote data
2. Actual historical trade/quote snapshots with known limitations
3. Model-derived price using stated inputs
4. No option result

A modeled result must never be labeled as an observed fill.

## Expiry

Next trading day means the nearest listed SPY expiration after the signal date.

Examples:

```text
Monday signal  → Tuesday expiry
Friday signal  → Monday expiry, unless the next trading session differs because of a holiday
```

No 0DTE contract belongs to CIM-V1 option translation.

## Underlying R vs option R

Always report both.

```text
Underlying R = move relative to structural underlying risk
Option R     = option P/L relative to option cash risk or defined option-risk convention
```

Do not assume a 1.5R target on SPY creates 1.5R in the option.

Spread, slippage, delta, gamma, theta, IV, and timing can materially change the option outcome.

## Liquidity

V1 logs spread and execution friction rather than inventing a post-hoc spread threshold.

Unusable or missing two-sided quotes are flagged and excluded from executable option results, with the exclusion count reported.

A future version may pre-register a numeric spread filter after the baseline distribution is measured.
