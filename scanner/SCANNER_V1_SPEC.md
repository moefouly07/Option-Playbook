# Muse Scanner V1 — Pilot Specification

Status: DESIGN / NOT VALIDATED / NO AUTO-EXECUTION
Owner: Muse research workflow, separate from frozen CIM-V1.0.

## Scope and claims
Pilot is a fixed liquid-US-symbol watchlist, NOT a full-market discovery scan. Do not claim to have scanned all US equities. Every report must declare `universe_source`, `universe_count`, `processed_count`, `rejected_count`, `missing_data_count`, and scan timestamp ET. Broader automated symbol discovery is phase 2, conditional on an auditable universe source.

## Pilot universe
Broad and sectors: SPY, QQQ, IWM, SMH, XLK, XLF, XLE, XLI.
Equities: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AMD, MU, AVGO, MRVL, PLTR, QCOM.
Additional symbols can be flagged separately for manual review but cannot be represented as systematic universe coverage.

## Time / source
Market timezone: America/New_York; use actual US equity trading calendar including half-days. At 10:30 ET on stock-market sessions, conduct one research scan. Report market-time and most recent completed-bar time. 
- `feed=iex`: real-time trades/quotes from ONE VENUE only; not consolidated volume, not a full-market executable quote.
- `feed=sip` historical bars: request only the interval eligible under subscription (end at least 15 minutes before now). Prefer `end = now - 20 minutes` with an additional completed-bar-only safety margin; do not unnecessarily freeze to previous day if eligible same-day SIP bars are available.
- `feed=delayed_sip` quotes when entitled: mark as delayed; separate timestamps from IEX.
- Do not combine IEX and SIP volume in a single calculation.
- Session filters: RTH 09:30–16:00 ET, handling early-close days. Filter intraday extended-hours bars before market-structure/volume calculations. Use actual exchange calendar, not merely weekdays.
- Prevent lookahead. Bar `close` means the bar is completed. Check bars for partial periods, gaps, split adjustments, and timestamps.

## Universe & compute constraints
Start only with supported endpoints and explicitly list coverage limits. If a symbol lacks sufficient data, mark INSUFFICIENT DATA, not a negative signal. Respect plan's rate limits and API pagination. For multi-symbol bars: paginate `next_page_token` until complete for all requested symbols; record count per ticker. Verify requests by symbol.
For daily SMA50 and ATR14, 70 completed daily bars are usually sufficient; do NOT compute SMA200 from 70 bars. For comparable time-of-day intraday RVOL, fetch enough previous RTH sessions at equivalent timestamps; one Friday of 5-minute bars cannot support a robust baseline.

## Initial objective
Identify a small number of interesting liquid equity/ETF setups for research, not live entry/0DTE execution:
- underlying quality: robust price structure on completed daily and 5m bars, relative strength vs SPY/QQQ and relevant sector;
- discovery conditions: verified price/volume expansion vs matched data source, clean continuation or pullback, and sourced catalysts when available;
- market regime: broader market and sector alignment;
- bear-case challenge: strongest credible invalidation, distance/extension from trend or key levels;
- skip trades when evidence is inadequate.

Provisional liquidity filter for equities (NOT empirically optimized): last completed daily close >= $10 and 20-day consolidated SIP average dollar volume >= $50 million. ETFs can be handled separately. This is a quality screen, not a guarantee. A candidate with missing liquidity history is INSUFFICIENT DATA.

## Options limitations
Current Alpaca skill is stocks-only. No option chain, OPRA spread, Greeks, option OI/volume or execution assessment has been established. Report OPTIONS NOT VERIFIED for every instrument. Do not invent a specific contract or convert a good stock setup into an implied good option trade.

## Research output
Maximum 3 candidates, each with ticker, PASS/WATCH/REJECT/INSUFFICIENT DATA, confidence as qualitative evidence only (no fictional statistical probabilities), price/source/time/session, setup and catalyst sources, primary pivot, confirmation condition, invalidation, bear case, what is missing, and stale/venue limitations.
A delayed SIP-confirmed technical setup is not a live trade trigger. Only market-data permission, no trading; no automated orders; no changes to frozen strategy.
Report NO TRADE if nothing passes, plus exclusions and data limitations.

## Pilot acceptance tests
1. For SPY, QQQ, NVDA, show SIP 1Day + 5Min sample timestamps, RTH-only counts, latest IEX quote timestamps, eligible recent SIP cutoff.
2. No future bars, no extended-hours bars in RTH signals.
3. Run after 10:30 ET during market hours. Prove same-day delayed SIP 5m bars are actually returned where permitted; otherwise mark insufficiency.
4. Verify historical sample completeness across pagination, adjustment policy, and market calendar.
5. Verify anomalous IEX after-hours spreads are flagged as NOT EXECUTABLE.
6. Verify candidate report includes scanned universe size, robust bear case, no fake catalysts, NO TRADE where appropriate.
7. Verify no trading endpoints and no secret leakage.
8. Accept V1 only after human review of pilot output.
