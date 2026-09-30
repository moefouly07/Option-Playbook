# Backtest Implementation Checklist

Before running performance statistics:

```text
[ ] Strategy version pinned
[ ] Code commit pinned
[ ] Data source documented
[ ] America/New_York handling verified
[ ] Exchange calendar verified
[ ] Early-close handling verified
[ ] 1m → 5m aggregation tested
[ ] OR interval tested
[ ] Wilder ATR warm-up tested
[ ] VWAP provenance documented
[ ] Missing-bar policy implemented
[ ] All acceptance tests pass
[ ] No look-ahead checks pass
[ ] Call/put symmetry reviewed
[ ] Layer 1 separate from Layer 2
[ ] Option quote quality labeled
[ ] Ask-entry/Bid-exit convention tested
[ ] Output schema complete
```

After the run:

```text
[ ] Signal count reconciled
[ ] No-trade day count reported
[ ] Calls and puts reported separately
[ ] Exclusions reported with reasons
[ ] MAE/MFE available
[ ] R/ATR5 distribution available
[ ] Year/regime breakdown available
[ ] Out-of-sample status explicit
[ ] No threshold changed after seeing results
```
