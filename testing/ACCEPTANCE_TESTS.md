# CIM-V1 Acceptance Tests

These are behavioral tests for the implementation.

They must pass before a performance backtest is trusted.

Use synthetic data with known outcomes.

## A01 — OR boundary

Given one-minute data from 09:30 through 09:55:

- 09:54:59 belongs to the opening range.
- 09:55:00 does not.

Expected: ORH/ORL use only the frozen interval.

## A02 — Wick is not a break

Given:

```text
ORH = 100.00
5m high = 100.40
5m close = 99.95
```

Expected:

```text
NO CALL BREAK
```

## A03 — Close is a break

Given:

```text
ORH = 100.00
5m close = 100.01
```

Expected:

```text
CALL BREAK
```

## A04 — Break bar cannot be retest bar

If the same 5-minute break bar contains a one-minute bar touching the retest band before the 5-minute bar closes:

Expected: that one-minute bar cannot be the post-break retest.

## A05 — Wick-allowed call retest

Given:

```text
ORH = 100.00
ATR5 = 0.80
band = 99.80–100.20
1m low = 99.90
1m close = 100.05
```

Expected: valid primary call retest.

## A06 — Deep call wick cancels

Same setup but:

```text
1m low = 99.79
```

Expected:

```text
CANCEL CURRENT CALL SETUP
```

A later prettier retest must not resurrect that breakout.

## A07 — Close inside OR cancels before entry

After call break but before entry:

```text
completed 5m close < ORH
and still inside opening range
```

Expected: setup canceled.

## A08 — Confirmation uses initial retest-bar high

If later retest-looking bars occur before confirmation, the confirmation threshold remains the high of the initial qualifying retest bar.

Expected: no hindsight reselection.

## A09 — Entry is next one-minute bar

If confirmation closes at 10:13:

Expected Layer-1 entry timestamp:

```text
10:14
```

using that bar's open.

## A10 — Structural stop spans retest through confirmation

For call:

Expected stop = minimum one-minute low from initial retest bar through confirmation bar inclusive.

## A11 — Stop requires close, not wick

If price wicks below call structural stop but the completed 1-minute close remains above it:

Expected: position remains open.

## A12 — Target uses touch

If the one-minute high trades through the call target:

Expected: target reached even if the bar closes below target.

This intentional asymmetry with close-based stop must remain visible.

## A13 — Setup expiry

If no valid confirmation occurs within 30 minutes after the break-bar close:

Expected: setup canceled.

## A14 — Last entry

A signal requiring entry after 11:45 ET:

Expected:

```text
NO ENTRY
```

## A15 — Time exit

An open trade at 12:30 ET:

Expected: time exit according to the implementation's documented executable-price convention.

## A16 — Chop side flips

Given four completed 5-minute closes relative to each bar-ending VWAP:

```text
Above
Below
Above
Above
```

Expected:

```text
2 side flips
CHOP
NO NEW ENTRY
```

## A17 — Equal-to-VWAP instability

If one of the last four relevant completed bars closes exactly at VWAP:

Expected: no new entry while that equality remains inside the four-bar window.

## A18 — Daily limits

After one completed call trade and one completed put trade:

Expected: no third V1 trade that day.

## A19 — No overlapping positions

If a second valid setup appears while a V1 position is open:

Expected: no overlapping V1 entry.

## A20 — Put symmetry

Mirror call tests for ORL, retest band, cancellation, confirmation, structural stop, and target.

## A21 — True R

If:

```text
entry = 100.00
structural stop = 99.70
ATR5 = 1.00
```

Expected:

```text
R = 0.30
R/ATR5 = 0.30
target = 100.45
```

Do not replace R with an ATR floor.

## A22 — Option selection

Candidates with absolute delta inside 0.40–0.60:

Expected: choose the practical contract closest to 0.50 delta, then use documented tie-break rules.

## A23 — Conservative option accounting

Without actual fills:

Expected:

```text
entry = ask
exit = bid
```

Never substitute last/mid/mark silently.

## A24 — No future data

Changing any bar after the decision timestamp must not alter an earlier signal decision.

This is the look-ahead-bias guard.

## A25 — ATR5 is current at each evaluated timestamp (C-001)

Given a put setup and ATR5 values supplied directly:

```text
ORL = 100.00
ATR5 after the 5m bar starting 09:50 = 0.40    (band 99.90 / 100.10)
ATR5 after the 5m bar starting 10:10 = 0.80    (band 99.80 / 100.20)
put break: 5m bar starting 10:00 closes 99.80
1m bar starting 10:15: high 100.15, close 99.95
```

Expected: the bar starting 10:15 is evaluated at 10:16 with ATR5 = 0.80. It enters the band and closes below ORL, so it is the retest. It is not a deep wick and does not cancel the setup. An implementation that keeps ATR5 = 0.40 from 09:55 would wrongly cancel the setup.

## A26 — 5-minute bar completion

At an evaluated time t, ATR5 uses only 5-minute bars whose start + 5 minutes <= t.

Expected: for an entry decided at 10:22:00, ATR5 comes from the bar starting 10:15. Changing the bar starting 10:20 must not change the entry, the stop, the target, or the R/ATR5 record.

