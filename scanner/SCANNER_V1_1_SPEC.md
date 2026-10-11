# Muse Scanner — SCANNER-V1.1 Specification

```text
Version:      SCANNER-V1.1
Status:       PRE-REGISTERED / NOT VALIDATED / RESEARCH ONLY
Supersedes:   SCANNER-V1.0 (scanner/SCANNER_V1_SPEC.md)
Registered:   2026-10-10, before the first live V1.1 run
Decisions:    DECISION_LOG.md D-009 to D-017
Executable:   scanner/reference/scanner_rules.py
Gate:         scanner/MUSE_ACCEPTANCE_TESTS.md
Report shape: scanner/OUTPUT_SCHEMA.json
```

This scanner is an independent discovery layer. It never modifies, replaces, or validates frozen CIM-V1.0.

## 0. Honesty statement (read first)

Every V1.1 rule was written **after** reviewing the V1.0 pilot output on 2026-10-09 completed bars. V1.1 is therefore a new hypothesis, not an improved result. The 2026-10-09 data is in-sample for V1.1 and is not evidence for it. The first out-of-sample observation is the first live run made after this file is committed.

If this document and the reference implementation disagree, stop and log the ambiguity. Do not choose the interpretation that produces more candidates.

## 1. Freeze rule

Every value in `PARAMS` (section 5) is fixed at commit time. Changing any value, label, gate, or ranking key creates SCANNER-V1.2 and requires a `DECISION_LOG.md` entry and a new validation plan. An exploratory variant may be run only when labeled `EXPLORATORY_NOT_V1.1` and must never replace the V1.1 report.

## 2. Universe

```text
universe_source: fixed pilot watchlist (this file)
universe_count:  21
benchmark:       SPY            (never a candidate)
eligible_count:  20
broad ETFs:      SPY QQQ IWM
sector ETFs:     SMH XLK XLF XLE XLI
equities:        AAPL MSFT NVDA AMZN GOOGL META TSLA AMD MU AVGO MRVL PLTR QCOM
```

This is not a full-market scan and must never be described as one.

## 3. Data and time

- Timezone `America/New_York`. Use the actual exchange calendar, including holidays and early closes.
- Daily classification uses **completed** consolidated SIP daily bars only. During a live session, today's daily bar is incomplete and is excluded; the latest completed daily bar is the previous session.
- Minimum history: 70 completed daily bars per symbol and for SPY. Otherwise `INSUFFICIENT_DATA`.
- History window: each run requests the 130 completed daily sessions ending at the latest completed session and computes every indicator over that window (D-021). Wilder ATR and RSI depend on the seeding length, so the window is fixed.
- Freshness: if SPY's latest completed bar is not the expected session, the run refuses. Any other symbol whose latest bar differs, or whose bars fail integrity checks, is `INSUFFICIENT_DATA` and named in `data_quality`.
- A symbol whose latest completed daily date differs from SPY's is `INSUFFICIENT_DATA`.
- Intraday: completed RTH SIP 5-minute bars, requested with `end = now − 20 minutes`. Extended-hours bars removed. Intraday data is **recorded only** in V1.1 (section 9).
- IEX quotes are single-venue. Never mix IEX and SIP volume. Never treat delayed data as an execution signal.
- Every report records `spec_commit_sha`: the last commit that changed this spec or `OUTPUT_SCHEMA.json`.

## 4. Labels (single enum, used everywhere)

```text
CONFIRMED_SETUP     setup + every confirmation condition on the latest completed daily bar
RESEARCH_PASS       setup structure present, confirmation incomplete or capped
WATCH               eligible symbol without a qualifying setup, or a blocked setup
REJECT              fails the liquidity screen
INSUFFICIENT_DATA   missing or misaligned data; never a negative signal
BENCHMARK           SPY only; regime reference
```

`TRADE_READY` is **not** a scanner label. No V1.1 output authorizes entry. A future trade-readiness stage would require live executable quotes, verified option-chain data, and human approval, and would be a separate specification.

## 5. Parameters (PRE-REGISTERED)

```text
min_daily_bars          70
atr_len / rsi_len       14 / 14        Wilder
sma_fast / sma_slow     20 / 50
rs_lookback             20 sessions
rvol_lookback           20 sessions
adv_lookback            20 sessions
breakout_lookback       20 sessions
pullback_touch_lookback 3 sessions
zone_atr_mult           0.5
breakout_min_rvol       1.5
pullback_min_rvol       0.8
min_range_pos           0.5
ext_flag_atr            2.0
ext_block_atr           3.0
rsi_overbought          75   (recorded only)
min_price               10.00
min_adv_usd             50,000,000
corr_window             60 joined returns
corr_min_overlap        55
corr_flag               0.70
max_candidates          3
```

## 6. Definitions

All values on completed daily bars; `t` = latest completed bar.

```text
SMA_n        mean of the last n closes
TR_i         max(H_i − L_i, |H_i − C_{i−1}|, |L_i − C_{i−1}|)
ATR14        seed = mean of first 14 TR; then ATR_i = (ATR_{i−1} × 13 + TR_i) / 14
RSI14        Wilder; seed = mean of first 14 gains / losses
range_pos    (C_t − L_t) / (H_t − L_t); undefined if H_t = L_t (fails the condition)
RVOL20       V_t / mean(V_{t−20} … V_{t−1})
ADV20_usd    mean(C × V) over the last 20 bars
RS20_pp      [(C_t / C_{t−20}) − 1 − ((SPY_t / SPY_{t−20}) − 1)] × 100, on date-aligned closes
ext_atr      (C_t − SMA20) / ATR14
zone         [SMA20 − 0.5 × ATR14 , SMA20 + 0.5 × ATR14]
prior_20d_high  max(H_{t−20} … H_{t−1})
```

`RS20_pp = 0.0` is a valid value. Implementations must test for missing values with an explicit `None` check, never truthiness (V1.0 bug).

## 7. Classification order

1. `SPY` → `BENCHMARK`.
2. Fewer than 70 bars, misaligned latest date, or any required metric missing → `INSUFFICIENT_DATA`.
3. `C_t < 10` or `ADV20_usd < 50M` → `REJECT`.
4. **Breakout** (checked first): `C_t > prior_20d_high` and `C_t > SMA50`.
   Confirmation: `range_pos ≥ 0.5` and `RVOL20 ≥ 1.5`.
   Pivot = `H_t`. Invalidation = daily close below `prior_20d_high`.
5. **Pullback** (only if not a breakout):
   Structure: `C_t > SMA50`, `SMA20 > SMA50`, `min(L_{t−2}, L_{t−1}, L_t) ≤ zone_hi`, `C_t ≥ zone_lo`.
   If structure fails → `WATCH` ("no qualifying setup").
   Gate: `RS20_pp > 0`. If it fails → `WATCH` ("relative strength not positive").
   Confirmation: `C_t > C_{t−1}`, `range_pos ≥ 0.5`, `L_t ≤ zone_hi`, `C_t ≥ SMA20`, `RVOL20 ≥ 0.8`.
   Pivot = `SMA20`. Invalidation = daily close below `zone_lo`.
6. **Extension penalty** (any setup): `ext_atr > 3.0` → `WATCH` with flag `OVEREXTENDED`. `2.0 < ext_atr ≤ 3.0` → flag `EXTENDED`; tier capped at `RESEARCH_PASS`.
7. Setup with all confirmations and no cap → `CONFIRMED_SETUP`; otherwise `RESEARCH_PASS`.

Every result lists `triggered` and `failed` condition names exactly as in the reference implementation.

## 8. Ranking, selection, correlation

Ranking is a reproducibility convention, not a quality score or edge claim:

```text
key = (tier: CONFIRMED_SETUP=0, RESEARCH_PASS=1,
       setup: BREAKOUT_20D=0, PULLBACK_TO_SMA20=1,
       −RS20_pp, −RVOL20, symbol ascending)
```

Walk the ranked list. Before adding a symbol, compute its correlation with every already-selected symbol:

```text
1. simple daily returns per series, on that series' own consecutive completed bars
2. inner join on return date
3. last 60 joined dates
4. require ≥ 55 joined returns, else r = None (flag CORRELATION_UNAVAILABLE_WITH_X)
5. |r| ≥ 0.70 → skip with flag CORRELATED_WITH_X and continue down the list
```

Prices are never correlated directly. Every reported r includes `method`, `n`, `first`, `last`. Stop at 3 selections. Empty shortlist → verdict `NO_CANDIDATES`.

Shared-factor tags (static, recorded only): `semis` (SMH NVDA AMD MU AVGO MRVL QCOM), `megacap_tech` (AAPL MSFT AMZN GOOGL META), `software_ai` (PLTR), `ev_auto` (TSLA), `broad` (QQQ IWM), `sector` (XLK XLF XLE XLI). Note in every report that all long candidates share broad-market beta and that equities in the universe are SPY constituents.

## 9. Recorded-only fields (cannot change any label in V1.1)

- **Regime**: `RISK_ON` if SPY and QQQ close above SMA50 and watchlist breadth above SMA50 ≥ 60%; `RISK_OFF` if both below and breadth < 40%; else `MIXED`. Breadth is labeled `watchlist_breadth`, never market breadth. Sector count uses only the five sector ETFs.
- **RSI ≥ 75** → flag `RSI_OVERBOUGHT_RECORDED_ONLY`.
- **Catalysts** for shortlisted names: each with paraphrased headline, source name, source tier (`PRIMARY` company/SEC/exchange, `PRESS`, `AGGREGATOR`), URL, exact publication timestamp ET (or `DATE_ONLY` flag), `verified` true/false. Aggregator figures are `UNVERIFIED` until matched to a filing. No date ranges such as "10-08/09".
- **Earnings**: next date from a primary source, else `EARNINGS_DATE_UNVERIFIED`. Within 10 sessions of the scan → `EVENT_RISK`.
- **Intraday status** for shortlisted names from the latest completed delayed SIP 5-minute bar: `ABOVE_PIVOT`, `BETWEEN_PIVOT_AND_INVALIDATION`, `BELOW_INVALIDATION`, or `NOT_AVAILABLE`.
- **Options**: `OPTIONS_NOT_VERIFIED` for every symbol until a licensed option-chain feed passes its own acceptance test.

## 10. Report

The run report must validate against `scanner/OUTPUT_SCHEMA.json`, include all 21 symbols, and state the verdict. Raw vendor bars are not committed (see `SECURITY.md`).

`implementation_ref` is a manifest hash over every executed file, computed by `scanner/tools/implementation_ref.py` (D-019): per-file sha256 of UTF-8 bytes with LF line endings, one `path  sha256` line per file sorted by path, then sha256 of the manifest. The report lists the files in `implementation_files`. Live runs use only the committed entry point `scanner/src/muse/run_scan_v11.py`.

## 11. Outcome logging (starts with the first live run)

For every symbol in every run, log label, setup, pivot, invalidation, and close at the scan's latest completed daily bar. Later fill forward closes at +1, +5, and +10 sessions, and whether invalidation was hit first. These horizons are pre-registered now so evaluation is not chosen after the fact. Logging is research bookkeeping, not a performance claim.

## 12. Acceptance

V1.1 may be scheduled only after every test in `scanner/MUSE_ACCEPTANCE_TESTS.md` passes and a human signs off in `DECISION_LOG.md`.

The golden fixtures are themselves tested: `scanner/tests/test_fixture_sensitivity.py` requires every listed wrong implementation to fail. Expanding fixtures or mutants is a test change, not a rule change, but is logged in `DECISION_LOG.md`.
