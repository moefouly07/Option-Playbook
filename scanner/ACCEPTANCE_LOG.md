# SCANNER-V1.1 Acceptance Log

One row per attempt. Never delete rows; add a new attempt instead.

| Test | Attempt | Date ET | Spec commit | Result | Evidence / notes |
| --- | --- | --- | --- | --- | --- |
| T0 | 1 | 2026-10-11 | 84f23fb | BLOCKED (deployment) | Muse behaved correctly: exact SHA, exact PARAMS, complete gap table, no code changes. Spec files were missing from `scanner/` because only root docs and the patch file were uploaded. Muse read V1.1 from the patch and disclosed it. See D-018. |
| T0 | 2 | 2026-10-11 | 87e1d53 | PASS | All V1.1 paths present, stray root patch and duplicate removed, PARAMS identical to attempt 1 (23 values). Independent clone matched the prepared tree byte for byte. Two transfer files were committed by mistake (`scanner-v1.1-fix.patch`, `upload-scanner-fix.zip`); Muse flagged the patch, not the zip. Both removed in the next commit. |
| T1 | 1 | 2026-10-11 | 87e1d53 | PASS (self-reported) | Reference suite OK (14). Muse `scanner_v11.py` matched `expected_output.json` with zero differences; shortlist BRKC, PULC, BRKE; TWIN skipped. implementation_ref `sha256:a3fe7a600a62b4586b745d378955eadfb6e232db56b879660cefd7561c60117b`. Independent re-run pending T1b export. Fixture test covers the rules engine only, not the data layer. |
| T1b | 1 | | | | |
| T2 | 1 | | | | |
| T3 | 1 | | | | |
| T4 | 1 | | | | |
| T4b | 1 | | | | |
| T5a-f | 1 | | | | |
| T6 | 1 | | | | |
| T7 | sign-off | | | | Human sign-off required before any recurring task. |
