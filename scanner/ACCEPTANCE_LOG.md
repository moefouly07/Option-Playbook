# SCANNER-V1.1 Acceptance Log

One row per attempt. Never delete rows; add a new attempt instead.

| Test | Attempt | Date ET | Spec commit | Result | Evidence / notes |
| --- | --- | --- | --- | --- | --- |
| T0 | 1 | 2026-10-11 | 84f23fb | BLOCKED (deployment) | Muse behaved correctly: exact SHA, exact PARAMS, complete gap table, no code changes. Spec files were missing from `scanner/` because only root docs and the patch file were uploaded. Muse read V1.1 from the patch and disclosed it. See D-018. |
| T0 | 2 | 2026-10-11 | 87e1d53 | PASS | All V1.1 paths present, stray root patch and duplicate removed, PARAMS identical to attempt 1 (23 values). Independent clone matched the prepared tree byte for byte. Two transfer files were committed by mistake (`scanner-v1.1-fix.patch`, `upload-scanner-fix.zip`); Muse flagged the patch, not the zip. Both removed in the next commit. |
| T1 | 1 | 2026-10-11 | 87e1d53 | PASS (self-reported) | Reference suite OK (14). Muse `scanner_v11.py` matched `expected_output.json` with zero differences; shortlist BRKC, PULC, BRKE; TWIN skipped. implementation_ref `sha256:a3fe7a600a62b4586b745d378955eadfb6e232db56b879660cefd7561c60117b`. Independent re-run pending T1b export. Fixture test covers the rules engine only, not the data layer. |
| T1b | 1 | 2026-10-11 | 4df4ee1 | PARTIAL | Muse corrected its entry-point claim (harness is not a scan; no live entry point exists). Chat paste lost line breaks, so byte identity with `a3fe7a60…` was unverifiable. Independent run of the transcription: 0 diffs on 14 symbols, 0 diffs on the expanded 21. Mutation testing found 2 uncaught wrong implementations on the old fixtures; fixtures expanded (D-019). Transcription committed as canonical copy. |
| T1b-2 | 1 | 2026-10-11 | 7409c17 | PASS | AST EQUAL for scanner_v11.py and t1_fixture_check.py; workspace copies replaced byte for byte (cmp verified). Reference suite OK (16). Harness: 21 symbols, 0 diffs, shortlist BRKC, PULC, GAPF. implementation_ref sha256:1ffed572a4b908ad66c33fa18dc6b9de69b97825e6e0bb5bd4cc17cd652e212c, identical in Muse workspace, independent Linux check, and local Windows run. Counts as T1 attempt 2: PASS. |
| T1c | 1 | 2026-10-11 | ce94f49 | CHANGES REQUIRED | base64 export decoded byte-exact (run_scan_v11.py 7016fa88..., 478 lines; data_adapter.py 88adb59b..., 283 lines). No credentials or trading endpoints. Simulation found: stale SPY accepted silently, HEAD-based spec gate, uncommitted code ran, outcome log duplicated/mixed. Fixed in canonical copies; pipeline_sim 13/13. Canonical implementation_ref sha256:d3563058a554edf5c72147c4ab2ded26dfe37d8801e099b3ec3225526bdb6c4f. See D-021. |
| T1c-2 | 1 | 2026-10-11 | 03731ab | PASS | Every diff hunk mapped to a D-021 fix; CLI request and response contract unchanged. Workspace copies replaced byte for byte (cmp). Unit tests OK (16), pipeline_sim 13/13, implementation_ref sha256:d3563058a554edf5c72147c4ab2ded26dfe37d8801e099b3ec3225526bdb6c4f (Muse, Windows, Linux). Real-CLI probe: SPY 130 bars 2026-04-07 to 2026-10-09, no integrity issue. Accepted spec SHA 03731aba77198d8c21b2589557a5bfafe8f90ebc. |
| T2 | 1 | 2026-10-11 | not reported | PASS | SIP 1Day split-adjusted, 100 bars per symbol, no missing sessions. V1.1 correlation(): AAPL/SPY 0.047, PLTR/SPY 0.436, AAPL/PLTR 0.142, AMD/SMH 0.828, NVDA/SMH 0.707, MU/SMH 0.808 (n=60, 2026-07-17 to 2026-10-09). Archived V1.0 path reproduces 0.047222; misalignment hypothesis refuted with code. Independent FMP cross-check: 0.047222. See D-020. |
| T3 | 1 | | | | |
| T4 | 1 | | | | |
| T4b | 1 | | | | |
| T5a-f | 1 | | | | |
| T6 | 1 | | | | |
| T7 | sign-off | | | | Human sign-off required before any recurring task. |

## Known issues

| ID | Found | Description | Plan |
| --- | --- | --- | --- |
| KI-001 | T1c-2 | outcome_rows_to_write raises KeyError if an existing outcome log has different headers (hand-edited file); should refuse cleanly. | Fix with the next code change; requires a new implementation_ref and adoption. |
