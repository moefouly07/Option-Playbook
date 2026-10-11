# Decision Log

## D-001 — Start with a simple baseline

Decision: test opening-range break + retest before adding many indicators.

Reason: reduce overfitting and make every decision reproducible.

## D-002 — VWAP is context, not independent confirmation

A first-touch breakout guarantees the breakout price is above prior prices, but a 5-minute-close breakout does not mathematically guarantee the closing price is above VWAP because trading may already have occurred beyond the range.

Decision: V1 does not require `price > VWAP` for calls or `price < VWAP` for puts as an independent directional rule. VWAP remains active only in the chop definition and is logged for analysis.

## D-003 — Retest is a bounded zone

The original one-sided inequality allowed an excessively deep wick to qualify as a retest.

Decision: retest must occur inside a symmetric 0.25 × ATR5 band around the broken opening-range level.

## D-004 — Wick through the level is allowed

Decision: a call retest may wick below ORH, and a put retest may wick above ORL, provided the wick stays inside the retest band and the 1-minute bar closes back on the correct side.

Secondary pre-registered comparison: strict retest, where the wick never crosses the broken level.

## D-005 — Deep wick cancels the setup

Decision: once price exceeds the outer boundary of the retest band before entry, that breakout setup is canceled. It is not allowed to wait for a later bar and pretend the failed retest never happened.

## D-006 — Keep true structural R

A proposal used:

```text
R = max(structural risk, 1.5 × ATR5)
```

while leaving the actual stop at the structural level.

Decision: rejected for V1 because it would rename a larger distance as R without changing the real stop. V1 defines:

```text
R = absolute distance between underlying entry and structural stop
```

The ratio `structural risk / ATR5` is recorded so a minimum-stop filter can be tested later without changing the baseline first.

## D-007 — Separate underlying edge from option execution

Decision: Layer 1 tests the underlying signal. Layer 2 measures option translation and friction. A correct underlying signal can still be a poor option trade.

## D-008 — No 0DTE in initial translation/pilot

Decision: use next-trading-day expiry first. 0DTE becomes a separate version/comparison after the signal is understood.

Reason: reduce extreme gamma/theta interaction while debugging the strategy.

---

# Scanner decisions

These entries govern the Muse discovery scanner only. None of them changes CIM-V1.0.

## D-009 — SCANNER-V1.1 is a post-pilot revision, not an unbiased test

Context: the V1.0 pilot ran on 2026-10-09 completed bars. After reviewing its output, Muse applied eight changes in its own workspace that were never committed to this repository. One of them demoted the name with the highest relative strength (AMD). A further review on 2026-10-10 found: SPY nominated as a candidate against itself, an undefined "SMA20 zone", a negative-relative-strength pullback passing, an extended breakout ranked first, regime breadth computed on the watchlist but described as market breadth, and an AAPL/SPY 60-day correlation of 0.05 that needs forensic review.

Decision: all V1.1 rules are declared as designed after seeing V1.0 output. The 2026-10-09 data is in-sample for V1.1 and is not evidence for it. The first out-of-sample observation is the first live V1.1 run after this commit. V1.1 parameters are frozen at commit; any change creates V1.2.

## D-010 — One label enum; TRADE_READY removed from the scanner

Decision: labels are `CONFIRMED_SETUP`, `RESEARCH_PASS`, `WATCH`, `REJECT`, `INSUFFICIENT_DATA`, `BENCHMARK`. `TRADE_READY` was assigned on delayed, completed-bar data and implied an entry the spec forbids. It is removed. Trade readiness, if ever built, is a separate stage requiring live executable quotes, verified option data, and human approval.

## D-011 — SPY is benchmark only

Decision: SPY's relative strength against itself is zero by definition and it anchors the regime. It is labeled `BENCHMARK` and can never be a candidate.

## D-012 — Pullback structure and confirmation are bounded by ATR

Decision: zone = SMA20 ± 0.5 × ATR14 (Wilder, daily). Structure needs close and SMA20 above SMA50, a low inside or below the zone's upper edge within the last three sessions, and close not below the zone's lower edge. Confirmation needs an up close, range position ≥ 0.5, today's low ≤ zone upper edge, close ≥ SMA20, and RVOL20 ≥ 0.8. The volume floor addresses a V1.0 case confirmed on roughly half-normal volume.

## D-013 — Pullbacks require positive relative strength

Decision: RS20 versus SPY must be strictly greater than zero for a pullback to qualify; otherwise `WATCH`. Zero is a valid value and fails the gate; it is never treated as missing.

## D-014 — Extension penalty for any setup

Decision: ext = (close − SMA20) / ATR14. Above 2.0 adds `EXTENDED` and caps the label at `RESEARCH_PASS`. Above 3.0 adds `OVEREXTENDED` and the label becomes `WATCH`. RSI ≥ 75 is flagged but recorded only.

## D-015 — Correlation method is fixed and reported

Decision: Pearson correlation of simple daily returns computed per series on its own consecutive completed bars, inner-joined on date, last 60 joined dates, minimum 55 joined returns. Every value reports method, n, first and last date. |r| ≥ 0.70 against an already-selected name skips the candidate. Prices are never correlated directly. The V1.0 AAPL/SPY value is under forensic review (acceptance test T2); a synthetic unit test shows how zipping returns by position after date gaps can produce a near-zero value.

## D-016 — Context fields are recorded only in V1.1

Decision: regime (named `watchlist_breadth`), catalysts, RSI, earnings proximity, and intraday status are recorded but cannot change any label. Catalysts need exact publication timestamps, source tier, and URL; aggregator figures stay `UNVERIFIED` until matched to filings. Options remain `OPTIONS_NOT_VERIFIED`.

## D-017 — Reference implementation and golden fixtures gate production code

Decision: `scanner/reference/scanner_rules.py` is the executable definition of V1.1. Synthetic fixtures (year 2099) with a designed-intent table and `expected_output.json` must be reproduced exactly by any production implementation before its live output is trusted. Scheduling waits for `scanner/MUSE_ACCEPTANCE_TESTS.md` T0–T6 and a human sign-off entry here.

## D-018 — T0 findings: undisclosed V1.0 gates and incomplete deployment

Date: 2026-10-11 (ET).

Deployment: commit `84f23fb` uploaded root documents and the patch file itself, but not the `scanner/` changes. Root documents therefore pointed to V1.1 files that did not exist. Muse read the V1.1 content from inside the patch and said so. Correction: the `scanner/` tree is committed, the stray root `scanner-v1.1.patch` and root `MUSE_ACCEPTANCE_TESTS.md` duplicate are removed. T0 must be re-confirmed against the corrected commit.

Findings reported by Muse in T0 (self-reported, not yet verified against exported code):

- V1.0 workspace code applied gates that the V1.0 pilot report did not disclose: pullback RSI band 40–65, breakout RSI ≤ 80, a sell-climax filter (RVOL ≤ 1.5 on pullbacks), a ±3% SMA20 zone, close > open as reversal, 55-bar minimum history, and an ETF exemption from the dollar-volume screen.
- Relative strength was a ratio without date alignment.
- RVOL included the current bar in its own baseline, which compresses spikes toward 1.0.
- Correlation was a positional zip of 60 returns with no date join. This matches the synthetic reproduction in `test_join_on_dates_not_positions` and is the leading explanation for the V1.0 AAPL/SPY value of 0.05. T2 must still demonstrate it with code.

Consequence: the V1.0 pilot report described its own logic incompletely, so its outputs cannot be reproduced from its text. This confirms the D-017 gate: no implementation is trusted from its description, only from reproducing the golden fixtures and exporting its code (T1b).
