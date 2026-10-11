# Scanner Pilot Rules

Status: research draft, not a proven trading strategy.

Universe: listed US stocks and liquid ETFs. Equity screen based on price, dollar volume, and clean data quality, with numeric cutoffs to be selected and tested using known vendor capabilities. Never silently reject candidates using invented data.

Stages:
1. Determine market session, holiday calendar, broad ETF and sector environment.
2. Identify unusual *verified* volume, relative-strength movement, breakouts/pullbacks, relevant catalysts.
3. Examine daily and 5m completed bars where available; confirm technical structure and one primary decision level.
4. Independently challenge the bull thesis with the strongest bear interpretation.
5. If listed options matter, verify specific expiry, strike, bid, ask, volume, open interest, IV and Greeks when available. A missing live options feed means OPTIONS NOT VERIFIED.
6. Label each candidate PASS / WATCH / REJECT / INSUFFICIENT DATA. Return at most three PASS candidates. NO TRADE is permitted.

Required fields: ticker; scan time ET; regular/premarket/after-hours state; data source/feed; quote freshness; setup; catalyst with evidence; trigger; invalidation; risk and missing data.

No arbitrary probability/score, no backtested edge claim, no trading/execution, no edits to frozen strategy.
