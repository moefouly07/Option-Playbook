"""
SCANNER-V1.1 acceptance tests for the reference implementation.

Run from repository root (standard library only):
    python3 -m unittest discover -s scanner/tests -v
"""
from __future__ import annotations

import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "reference"))

import scanner_rules as sr  # noqa: E402
import make_fixtures as mf  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def mkbar(i, o, h, l, c, v=1_000_000):
    return sr.Bar(f"2099-01-{i + 1:02d}", o, h, l, c, v)


class Indicators(unittest.TestCase):
    def test_wilder_atr_seed_then_recursion(self):
        # 16 bars, flat close 100. TR = 1 for bars 1..14, TR = 15 on bar 15.
        bars = [mkbar(0, 100, 100.5, 99.5, 100)]
        for i in range(1, 15):
            bars.append(mkbar(i, 100, 100.5, 99.5, 100))
        bars.append(mkbar(15, 100, 107.5, 92.5, 100))
        self.assertAlmostEqual(sr.wilder_atr(bars[:15], 14), 1.0)
        self.assertAlmostEqual(sr.wilder_atr(bars, 14), (1.0 * 13 + 15.0) / 14)

    def test_atr_needs_n_plus_one_bars(self):
        bars = [mkbar(i, 100, 101, 99, 100) for i in range(14)]
        self.assertIsNone(sr.wilder_atr(bars, 14))

    def test_rsi_extremes(self):
        self.assertEqual(sr.wilder_rsi([float(x) for x in range(1, 30)], 14), 100.0)
        self.assertEqual(sr.wilder_rsi([100.0] * 30, 14), 50.0)

    def test_range_position_zero_span_is_none(self):
        self.assertIsNone(sr.range_position(mkbar(0, 10, 10, 10, 10)))


class FalsyZero(unittest.TestCase):
    """Regression for the V1.0 bug: rs == 0.0 treated as missing."""

    def test_zero_relative_strength_is_a_value(self):
        bars = mf.load("PULC")
        rs = sr.relative_strength(bars, bars, 20)
        self.assertIsNotNone(rs)
        self.assertEqual(rs, 0.0)

    def test_zero_rs_fails_gate_not_data(self):
        bars = mf.load("PULC")
        res = sr.classify("PULC", bars, bars)  # benchmark == itself -> rs 0.0
        self.assertEqual(res.label, sr.WATCH)
        self.assertIn("rs20>0", res.failed)


class Correlation(unittest.TestCase):
    def test_join_on_dates_not_positions(self):
        closes = mf.path(100.0, [0.0] * 90, 0.01, 4242)  # driftless walk
        a = [sr.Bar(d, c, c * 1.005, c * 0.995, c, 1e6)
             for d, c in zip(mf.DATES, closes)]
        drop = {a[i].date for i in range(32, 88, 6)}  # 10 interior gaps
        b = [x for x in a if x.date not in drop]
        good = sr.correlation(a, b, 60, 40)
        self.assertGreater(good["r"], 0.80)
        # The bug class behind a suspicious near-zero value: zipping two
        # return lists by position after one series has gaps.
        ra = [c.close / p.close - 1 for p, c in zip(a[:-1], a[1:])][-60:]
        rb = [c.close / p.close - 1 for p, c in zip(b[:-1], b[1:])][-60:]
        naive = sr.pearson(ra, rb)
        self.assertLess(naive, good["r"] - 0.3)

    def test_insufficient_overlap_returns_none(self):
        a = mf.load("SPY")
        res = sr.correlation(a, a[-30:], 60, 55)
        self.assertIsNone(res["r"])
        self.assertEqual(res["method"], "simple_returns_inner_join")


class GoldenFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = json.loads((FIX / "expected_output.json").read_text())
        cls.bars, cls.results, cls.selection = mf.evaluate(sorted(mf.INTENDED))
        cls.by_sym = {r.symbol: r for r in cls.results}

    def test_spec_version(self):
        self.assertEqual(self.expected["spec_version"], sr.SPEC_VERSION)

    def test_labels_match_designed_intent(self):
        for sym, label in mf.INTENDED.items():
            with self.subTest(sym=sym):
                self.assertEqual(self.by_sym[sym].label, label, self.by_sym[sym].reason)

    def test_rule_paths(self):
        self.assertIn("rs20>0", self.by_sym["PULN"].failed)
        self.assertIn("EXTENDED", self.by_sym["BRKE"].flags)
        self.assertIn("OVEREXTENDED", self.by_sym["BRKX"].flags)
        self.assertIn("close>=min_price", self.by_sym["CHEAP"].failed)
        self.assertIn("adv20_usd>=min_adv", self.by_sym["THIN"].failed)

    def test_benchmark_is_never_a_candidate(self):
        self.assertEqual(self.by_sym["SPY"].label, sr.BENCHMARK_ONLY)
        self.assertNotIn("SPY", self.selection["shortlist"])

    def test_numbers_match_expected_file(self):
        exp = {r["symbol"]: r for r in self.expected["results"]}
        for sym, res in self.by_sym.items():
            for k, v in exp[sym]["metrics"].items():
                got = res.metrics.get(k)
                with self.subTest(sym=sym, metric=k):
                    if v is None:
                        self.assertIsNone(got)
                    else:
                        self.assertTrue(math.isclose(got, v, rel_tol=1e-9, abs_tol=1e-9))
            self.assertEqual(res.label, exp[sym]["label"])

    def test_selection_and_correlation_dedupe(self):
        self.assertEqual(self.selection["shortlist"], mf.INTENDED_SHORTLIST)
        self.assertEqual(self.selection["shortlist"], self.expected["selection"]["shortlist"])
        skipped = {s["symbol"] for s in self.selection["skipped_for_correlation"]}
        self.assertEqual(skipped, {"TWIN"})


if __name__ == "__main__":
    unittest.main()
