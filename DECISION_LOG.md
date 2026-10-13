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

## D-019 — Fixture coverage expansion, canonical code copy, manifest implementation_ref

Date: 2026-10-11 (ET). No rule, parameter, label, gate, or ranking changed.

Context: Muse's T1b export arrived through a chat paste that lost line breaks, so byte identity with its stated hash could not be verified. The code was transcribed with whitespace restored. Run independently, the transcription reproduced the original 14-symbol fixtures with zero differences. Mutation testing then showed the gate was weak: a wrong RS gate (`>= 0`) and a positional, date-blind correlation (the V1.0 bug) both still passed.

Decision:

- Fixtures expanded from 14 to 21 synthetic symbols: ZERO (RS exactly 0.0), PULV (volume floor), GAPF (close above prior close but below open), BRKS (above 20-day high but below SMA50), BARS60 (between 55 and 70 bars), XLI (thin synthetic sector ETF), BRKO (extension between 3.0 and 3.5 ATR); TWIN now has five missing sessions. Intended shortlist becomes BRKC, PULC, GAPF.
- `scanner/tests/test_fixture_sensitivity.py` applies 12 known-wrong mutants (most are disclosed V1.0 behaviours) to the reference and requires every one to fail the golden comparison.
- `scanner/src/muse/` holds the canonical copy of Muse's code. GitHub is the source of truth; Muse verifies equivalence with `scanner/tools/ast_equivalence.py`, then runs the committed bytes only.
- `implementation_ref` is redefined as a manifest hash over every executed file (`scanner/tools/implementation_ref.py`). A report whose manifest does not match the accepted one is rejected. The T1 attempt-1 value (`a3fe7a60…`) remains in the acceptance log as history.
- A live entry point and data adapter must be built, exported in a transfer-safe encoding, and reviewed (T1c) before T3.

Consequence: T1 is repeated on the expanded fixtures as part of T1b-2.

## D-020 - Correction to D-018: the V1.0 AAPL/SPY correlation was correct

Date: 2026-10-11 (ET). No rule changed.

D-018 recorded the positional zip as the leading explanation for the V1.0 AAPL/SPY value of 0.05. T2 refutes that for this pair and window. All seven tested symbols share the same 100 sessions ending 2026-10-09, so the positional zip happened to be date-aligned. The archived V1.0 path and the committed V1.1 correlation() both return 0.047222 on the same SIP bars. An independent second vendor (FMP end-of-day closes) gives the same 0.047222 over the same 60 returns (2026-07-17 to 2026-10-09).

The low value is real in this data. It is dominated by AAPL-specific sessions: the largest AAPL moves ran against SPY (2026-07-31: AAPL -7.35%, SPY +0.72%; 2026-09-10: AAPL +3.56%, SPY -0.60%). Excluding the three largest AAPL sessions gives 0.22, and the 20-session window ending 2026-10-09 gives 0.35.

What stands: the V1.0 positional method is unsafe in principle because it has no date check; the V1.1 method and fixtures already guard against it. The criticism of the V1.0 "diversification intact" claim also stands, because low pairwise correlation over one window does not remove shared broad-market beta in a selloff.

FUTURE RESEARCH (not V1.1, not active): event-robust correlation, for example excluding earnings sessions or using rank correlation. Any adoption is a new scanner version.

## D-021 - T1c review: live-pipeline fixes and pre-registered history window

Date: 2026-10-11 (ET). No classification rule, parameter, label, or ranking changed.

Muse exported `run_scan_v11.py` (sha256 7016fa88...) and `data_adapter.py` (sha256 88adb59b...) as base64; both decoded byte-exact. Review found no credentials, no trading or account endpoints, and no shell invocation. An end-to-end simulation against a fake read-only CLI found four defects:

1. Stale data accepted silently: when the vendor lacked the latest session for every symbol, the run still reported the expected session date and produced a different shortlist.
2. The spec gate used `git rev-parse HEAD`, so any unrelated commit (an acceptance-log row) refused the run, which would train operators to pass whatever HEAD is current.
3. Uncommitted edits to the rules engine ran without refusal.
4. The outcome log lived inside the repository, duplicated rows on repeated runs, and mixed replay rows with live rows.

Decision (applied to the canonical copies in `scanner/src/muse/`):

- Refuse if SPY's latest completed bar is not the expected session; other stale or malformed symbols become INSUFFICIENT_DATA and are named in `data_quality`. Bars must have strictly increasing unique dates, finite values, and consistent OHLC.
- `spec_commit_sha` is the last commit that changed `SCANNER_V1_1_SPEC.md` or `OUTPUT_SCHEMA.json`.
- Refuse on uncommitted changes to tracked files under `scanner/`, and on any `implementation_ref` other than `--accepted-impl-ref`.
- Outcome logs default to git-ignored `scanner/runs/`, one file for LIVE and one for replay, one row per (session, symbol).
- Error text from the CLI is redacted of token-like strings; Windows needs the `tzdata` package.
- The daily history window (130 completed sessions) is pre-registered in the spec, because Wilder ATR and RSI depend on the seeding length.

`scanner/tests/pipeline_sim/` simulates the pipeline end to end (13 scenarios) without network or vendor data. Muse reviews the diff against its export and adopts the canonical files in T1c-2.

## D-022 - Scheduling package, outcome definitions, KI-001/002/003

Date: 2026-10-12 (ET). Approved by the project owner after T0-T6 passed: all proposed scheduling defaults, including the hourly watch, and the invalidation definition below. No classification rule, parameter, label, or ranking changed.

Decisions:

- Outcome log (spec section 11): returns are measured from `scan_time_price`, the close of the last complete SIP 5-minute bar ending at or before scan time - 20 minutes, because the move between the last daily close and the scan could not have been acted on. `close_pK` counts completed sessions after the scan. The undefined "invalidation hit first" is replaced by `invalidation_close_session`: the first of 10 sessions whose close is below invalidation, `NONE`, `NA`, or blank while pending. Filled values are immutable. The 21 T4 rows are migrated once with the same rule.
- Statistics stay withheld until 30 finalized candidate rows exist; afterwards only descriptive numbers against a WATCH baseline are reported.
- Scheduling (spec section 13): official 10:30 ET, hourly watch 11:30-15:30 ET (messages only on state change), outcomes 16:30 ET, weekly Saturday 10:00 ET. The scheduler has no holiday calendar and no failure alerts, so `scheduled_job.py` checks the ET window, the NYSE calendar and every gate itself, messages on every official run and every failure, and halts after 2 consecutive failures.
- KI-001: an outcome log with an unexpected header is refused before any fetch. KI-002: LIVE runs on non-trading days are refused. KI-003: a 5-minute bar is used only if its end is at or before the request end.
- One implementation manifest for every entry point (`pipeline_gates.PIPELINE_FILES`, 7 files). Accepted implementation_ref `sha256:0c31a73ebac963f4f75a936a59c2ce92fe415c4674426ac4c2f5d76e7ab19a6b`.
- A simulated clock exists only for `scanner/tests/pipeline_sim/` and is ignored unless the skill CLI in use lives under `scanner/tests/`. The simulation now covers 30 scenarios.

## D-023 - Data availability: never request today's daily bar (KI-004)

Date: 2026-10-12 (ET). No classification rule, parameter, label, or ranking changed.

Context: the first supervised scheduled run (T7c, outcomes at 16:31 ET) failed with HTTP 403 "subscription does not permit querying recent SIP data". Muse showed with direct probes that the market-data plan refuses consolidated SIP daily requests ending on the current calendar date even after the close, while the previous session works. The D-022 simulation missed it because the fake CLI did not model the plan; Muse caught it, posted the failure, and changed nothing.

Decision:

- `data_adapter.latest_available_session(now)` = the trading day strictly before today's ET date. LIVE runs and the outcome updater both use it, so no code path requests today's daily bar. During the session this is identical to D-022 behaviour. Beyond the plan limit, a same-day close can still be revised, so waiting a day is also the safer data rule.
- The outcomes job moves to 09:15 ET (window 09:00-10:00) and fills closes through the previous session. Day T's close enters the log on day T + 1.
- The fake CLI now refuses daily requests ending today and intraday requests ending less than 15 minutes ago. Run against the D-022 code, the extended simulation reproduces the exact 403; against the fix it passes 34/34.
- Accepted implementation_ref `sha256:06b4d1c8860ce1400f403205b288e03236ca059d812b51f8b1fe852cc3fc30ca` (was `sha256:0c31a73ebac963f4f75a936a59c2ce92fe415c4674426ac4c2f5d76e7ab19a6b`). The spec changes, so the accepted spec SHA changes too.
- Owner sign-off for recurring tasks moves to D-024.

## D-024 - CIM-V1.0 clarification C-001: ATR5 is current at every evaluated timestamp

Date: 2026-10-12 (ET). Owner decision. Clarification, not a rule change; CIM-V1.0 stays frozen.

Context: Muse's forward-log engine fixed ATR5 at its 09:55 value. CIM §3 says to use only information available at the evaluated timestamp but does not say whether ATR5 is fixed or updated. None of A01-A24 decides it. On 2026-10-12 the choice did not change the trade, but on another day a different band width can select a different retest bar or cancel a setup. Following AGENTS.md, the ambiguity was documented instead of being resolved by results.

Decision: ATR5 is recomputed at every evaluated timestamp from the most recent complete 5-minute RTH bar (`strategy/CLARIFICATIONS.md`, C-001; tests A25 and A26). Chosen before any validated forward result exists; the single forward-log row so far is UNVALIDATED and is recomputed under C-001.

Open: the ATR5 series seeding convention must be reported by the implementation and pinned as C-002 before A01-A26 acceptance.

The scanner is unaffected; its spec and implementation manifest do not change. Scanner sign-off moves to D-025.
