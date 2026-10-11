"""
Fixture sensitivity (mutation) tests for SCANNER-V1.1.

A golden-fixture comparison is only a gate if a WRONG implementation fails
it. Each mutant below is a deliberately wrong copy of the reference rules,
most of them real V1.0 behaviours disclosed in T0 (DECISION_LOG D-018).
Every mutant must produce at least one difference against
scanner/tests/fixtures/expected_output.json. If a mutant passes, the
fixtures have a coverage hole and must be extended (D-019).

Run from repository root:
    python3 -m unittest discover -s scanner/tests -v
"""
from __future__ import annotations

import csv
import json
import math
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "reference" / "scanner_rules.py"
FIX = ROOT / "tests" / "fixtures"

MUTANTS = [
    ("RVOL baseline includes the current bar (V1.0)",
     "base = sum(b.volume for b in bars[-1 - k:-1]) / k",
     "base = sum(b.volume for b in bars[-k:]) / k"),
    ("RS as a ratio instead of a pp difference (V1.0)",
     "return ((s1 / s0 - 1.0) - (b1 / b0 - 1.0)) * 100.0",
     "return ((s1 / s0) / (b1 / b0) - 1.0) * 100.0"),
    ("RS gate >= 0 instead of > 0",
     'm["rs20_pp"] > 0.0',
     'm["rs20_pp"] >= 0.0'),
    ("positional correlation without date join (V1.0)",
     'out["r"] = pearson([ra[d] for d in dates], [rb[d] for d in dates])',
     'out["r"] = pearson(list(ra.values())[-len(dates):], list(rb.values())[-len(dates):])'),
    ("pullback volume floor removed",
     '"pullback_min_rvol": 0.8',
     '"pullback_min_rvol": 0.0'),
    ("55-bar minimum history (V1.0)",
     '"min_daily_bars": 70',
     '"min_daily_bars": 55'),
    ("reversal = close > open (V1.0)",
     "t.close > prev.close",
     "t.close > t.open"),
    ("ETFs exempt from dollar-volume screen (V1.0)",
     'm["adv20_usd"] >= p["min_adv_usd"])',
     'm["adv20_usd"] >= p["min_adv_usd"] or symbol in SECTOR_ETFS + BROAD_ETFS)'),
    ("fixed +/-3% SMA20 zone (V1.0)",
     'zone_lo = sma20 - p["zone_atr_mult"] * atr\n    zone_hi = sma20 + p["zone_atr_mult"] * atr',
     'zone_lo = sma20 * 0.97\n    zone_hi = sma20 * 1.03'),
    ("breakout without SMA50 requirement (V1.0)",
     "is_breakout = t.close > prior_high and t.close > sma50",
     "is_breakout = t.close >= prior_high"),
    ("extension block loosened to 3.5",
     '"ext_block_atr": 3.0',
     '"ext_block_atr": 3.5'),
    ("extension cap removed",
     '"ext_flag_atr": 2.0',
     '"ext_flag_atr": 99.0'),
]


def load_module(source: str, name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod  # dataclasses need the module registered
    exec(compile(source, name, "exec"), mod.__dict__)
    return mod


def load_bars(mod, sym):
    with (FIX / "bars" / f"{sym}.csv").open() as fh:
        return [mod.Bar(r["date"], float(r["open"]), float(r["high"]),
                        float(r["low"]), float(r["close"]), float(r["volume"]))
                for r in csv.DictReader(fh)]


def same(a, b):
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
    return a == b


def count_diffs(mod, expected) -> int:
    symbols = sorted(p.stem for p in (FIX / "bars").glob("*.csv"))
    bars = {s: load_bars(mod, s) for s in symbols}
    results = [mod.classify(s, bars[s], bars[mod.BENCHMARK]) for s in symbols]
    sel = mod.select(results, bars)
    exp = {r["symbol"]: r for r in expected["results"]}
    diffs = 0
    for r in results:
        e, got = exp[r.symbol], r.as_dict()
        for f in ("label", "setup", "triggered", "failed", "flags", "pivot", "invalidation"):
            diffs += not same(e[f], got[f])
        for k, v in e["metrics"].items():
            g = got["metrics"].get(k)
            diffs += not ((v is None and g is None) or
                          (v is not None and g is not None and same(float(v), float(g))))
    esel = expected["selection"]
    diffs += esel["shortlist"] != sel["shortlist"]
    diffs += esel["skipped_for_correlation"] != sel["skipped_for_correlation"]
    diffs += len(esel["correlation_log"]) != len(sel["correlation_log"])
    for e, g in zip(esel["correlation_log"], sel["correlation_log"]):
        diffs += not (e["pair"] == g["pair"] and
                      ((e["r"] is None and g["r"] is None) or
                       (e["r"] is not None and g["r"] is not None and same(e["r"], g["r"]))))
    return diffs


class FixtureSensitivity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = REF.read_text()
        cls.expected = json.loads((FIX / "expected_output.json").read_text())

    def test_unmutated_reference_has_zero_diffs(self):
        mod = load_module(self.source, "ref_clean")
        self.assertEqual(count_diffs(mod, self.expected), 0)

    def test_every_mutant_is_caught(self):
        for i, (desc, old, new) in enumerate(MUTANTS):
            with self.subTest(mutant=desc):
                self.assertEqual(self.source.count(old), 1,
                                 f"mutation anchor not found exactly once: {desc}")
                mod = load_module(self.source.replace(old, new), f"ref_mut_{i}")
                self.assertGreater(count_diffs(mod, self.expected), 0,
                                   f"fixtures did not catch: {desc}")


if __name__ == "__main__":
    unittest.main()
