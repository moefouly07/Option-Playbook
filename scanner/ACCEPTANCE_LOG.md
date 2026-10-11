# SCANNER-V1.1 Acceptance Log

One row per attempt. Never delete rows; add a new attempt instead.

| Test | Attempt | Date ET | Spec commit | Result | Evidence / notes |
| --- | --- | --- | --- | --- | --- |
| T0 | 1 | 2026-10-11 | 84f23fb | BLOCKED (deployment) | Muse behaved correctly: exact SHA, exact PARAMS, complete gap table, no code changes. Spec files were missing from `scanner/` because only root docs and the patch file were uploaded. Muse read V1.1 from the patch and disclosed it. See D-018. |
| T0 | 2 | | | | Re-confirm paths and SHA after corrective commit. |
| T1 | 1 | | | | |
| T1b | 1 | | | | |
| T2 | 1 | | | | |
| T3 | 1 | | | | |
| T4 | 1 | | | | |
| T4b | 1 | | | | |
| T5a-f | 1 | | | | |
| T6 | 1 | | | | |
| T7 | sign-off | | | | Human sign-off required before any recurring task. |
