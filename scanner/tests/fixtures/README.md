# Golden fixtures — SYNTHETIC

These bars are synthetic and dated in 2099 on purpose. They are not market data and must never be used as evidence about any real instrument.

Each symbol is engineered to hit one rule path of SCANNER-V1.1. The intended label for each symbol is in `scanner/reference/make_fixtures.py` (`INTENDED`), and the exact expected output is in `expected_output.json`.

Never edit these files to make an implementation pass. A mismatch means the implementation, or the spec, is wrong; log it in `DECISION_LOG.md`.
