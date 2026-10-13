# CIM-V1.0 Clarifications

Interpretations of ambiguous CIM-V1.0 text. A clarification does not change a rule, a parameter, or a threshold; it pins one reading so every implementation computes the same thing. Each entry is recorded in `DECISION_LOG.md` before any validated result depends on it, and is covered by acceptance tests in `testing/ACCEPTANCE_TESTS.md`.

The frozen files (`PHASE_1_CIM_V1_FROZEN.md`, `RULE_DEFINITIONS.md`) are not edited. Where this file applies, it is read together with them.

## C-001 — ATR5 is recomputed at every evaluated timestamp

Decision: D-024 (owner, 2026-10-12). Tests: A25, A26.

Ambiguity: §3 defines ATR5 as Wilder ATR14 on completed 5-minute RTH bars and says "use only information available at the timestamp being evaluated", without saying whether ATR5 is fixed once (for example at 09:55) or updated as the session progresses.

Reading adopted: at every evaluated timestamp, ATR5 is the value after the most recent 5-minute RTH bar that is complete at that timestamp. A stale but available value is not used.

Timestamps:

```text
5-minute bar labeled by its start S     complete at S + 5 min
1-minute bar labeled by its start S     evaluated at its close, S + 1 min
entry at the open of 1-minute bar E     decided at E (= close of the previous bar)
```

ATR5 at evaluated time t uses only 5-minute bars with S + 5 min <= t.

Where ATR5 is used:

```text
retest band for a candidate 1-minute bar      ATR5 at that bar's close
failed-retest (deep wick) check for a bar     ATR5 at that bar's close
R / ATR5 record                               ATR5 at the entry decision time
```

Worked example (2026-10-12, put): the candidate retest bar starting 10:20 is evaluated at 10:21 with the ATR5 after the 5-minute bar starting 10:15. The entry decided at 10:22:00 uses the same 5-minute bar; the bar starting 10:20 is not complete until 10:25.

## C-002 — ATR5 series construction

Decision: D-025 (2026-10-12). Test: A27. Pins the convention the forward-log implementation already used, reported before any validated result.

Ambiguity: Wilder ATR14 needs 14 completed 5-minute bars, more than one opening range provides, and the frozen text does not say where the series starts, how overnight gaps enter the true range, or how the series is seeded.

Reading adopted:

```text
series     completed 5-minute RTH bars of the 3 previous NYSE sessions,
           then the current session, in time order (78 bars per full session;
           fewer on early-close days)
TR first   high - low for the first bar of the series
TR later   max(high - low, |high - prev_close|, |low - prev_close|), prev_close =
           previous bar's close; the first bar of each session uses the previous
           session's last RTH close, so the overnight gap is included
seed       simple mean of the first 14 TRs
update     ATR = (ATR_prev x 13 + TR) / 14 from the 15th bar onward
```

Combined with C-001, ATR5 at time t is the value after the last bar of this series that is complete at t.
