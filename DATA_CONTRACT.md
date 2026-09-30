# Data Contract — CIM-V1

The backtest is not valid unless the input data satisfies or explicitly documents these requirements.

## Time

Canonical timezone:

```text
America/New_York
```

Use an exchange calendar rather than assuming every weekday is a full session.

Handle:

```text
holidays
early closes
daylight-saving transitions
```

explicitly.

## Session

Layer 1 uses regular trading hours.

```text
09:30:00–16:00:00 ET
```

The opening range is:

```text
09:30:00–09:54:59 ET
```

## Underlying bars

Required base resolution:

```text
1-minute OHLCV
```

Preferred source:

```text
consolidated US market data
```

5-minute bars must be derived deterministically from the same 1-minute dataset.

Do not mix a venue-limited 1-minute source with a different consolidated 5-minute source in the same formal test.

## Completed-bar rule

If a strategy condition says `close`, only a completed bar may be used.

No look-ahead from a partially formed 1-minute or 5-minute bar.

## VWAP

Formal V1 chop testing requires volume appropriate for the chosen market-data definition.

If volume is venue-limited, mark:

```text
VWAP_QUALITY = APPROXIMATE
```

and keep those results separate from the primary consolidated test.

## ATR

```text
ATR5 = Wilder ATR14 on completed 5-minute bars
```

Warm-up bars must exist before the first timestamp where ATR is used.

Document the warm-up method.

## Missing bars

Never silently forward-fill OHLCV.

Classify missing data:

```text
expected no-trade interval
source gap
halt
unknown
```

A day with material unknown missing bars in the active trading window should be flagged/excluded under a documented rule.

## Corporate actions

Use prices consistent across the tested period.

Document whether data are adjusted and how splits/dividends are handled.

## Option Layer

Preferred historical option input:

```text
timestamped two-sided quote
bid
ask
contract specification
expiry
strike
type
```

Greeks/IV may be source-provided or model-derived, but the method must be labeled.

Without actual fills:

```text
entry = ask
exit = bid
```

## Provenance fields

Every dataset/run should identify:

```text
vendor/source
feed
download/query date
timezone
session definition
adjustment policy
missing-data policy
quote quality
strategy version
code version/commit
```
