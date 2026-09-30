# Trade Log Schema

Use one row per executed signal and a separate daily table for no-trade days if possible.

## Identity

```text
date
strategy_version
direction
signal_id
```

## Opening context

```text
ORH
ORL
OR_width
open_gap_pct
ATR5_break
VWAP_break
break_time
break_close
```

## Retest

```text
retest_time
retest_low
retest_high
retest_close
retest_depth_ATR
strict_retest_true_false
cancel_reason_if_any
```

## Confirmation and entry

```text
confirmation_time
confirmation_close
entry_time
underlying_entry
ATR5_entry
R_to_ATR5
chop_flip_count
```

## Risk and outcome

```text
structural_stop
target
exit_time
underlying_exit
exit_reason
underlying_R
MAE_R
MFE_R
minutes_in_trade
```

## Option translation

```text
option_symbol
expiry
strike
call_put
entry_bid
entry_ask
entry_mid
entry_spread
entry_spread_pct
entry_delta
entry_gamma
entry_theta
entry_vega
entry_IV
entry_volume
entry_OI
exit_bid
exit_ask
option_PL_dollars
option_return_pct
option_R
quote_source
quote_quality
actual_or_modeled
```

## Recorded-only research fields

```text
RSI14
SMA20_distance
EMA9_distance
EMA21_distance
distance_PDH
distance_PDL
distance_premarket_high
distance_premarket_low
relative_volume
event_0830
event_1000
FOMC_day
notes
```

## Execution pilot fields

```text
actual_entry_fill
actual_exit_fill
entry_slippage_vs_ask
exit_slippage_vs_bid
order_type
manual_delay_seconds
rule_deviation
rule_deviation_reason
```
