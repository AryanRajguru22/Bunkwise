"""Characterisation tests for the audited properties of the hand-designed fuzzy model.

These pin the numbers quoted in README.md / docs (so they cannot silently drift) and document known,
accepted limitations; they are not claims that the model is optimal.
"""
import itertools
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bunk_meter as bm

ORDER = {"CANNOT SKIP THE CLASS!!": 0, "PROCEED WITH CAUTION": 1, "CAN SKIP THE CLASS": 2}


class TestAuditedProperties(unittest.TestCase):
    def test_every_set_peaks_at_one_and_stays_in_unit_interval(self):
        for cfg in bm.INPUTS.values():
            lo, hi = cfg["range"]
            xs = np.linspace(lo, hi, 2001)
            for abc in cfg["sets"].values():
                a, b, c = abc
                self.assertTrue(a <= b <= c and a < c)
                ys = np.array([bm.trimf(x, *abc) for x in xs])
                self.assertTrue(((ys >= 0) & (ys <= 1)).all())
                self.assertEqual(bm.trimf(b, *abc), 1.0)
        for abc in bm.OUTPUT_SETS.values():
            self.assertEqual(bm.trimf(abc[1], *abc), 1.0)

    def test_weak_attendance_coverage_values_are_the_documented_ones(self):
        """Coverage never reaches 0, but the strongest set is weak near 70% and 85% (not a partition of unity)."""
        def best(x):
            return max(bm.trimf(x, *abc) for abc in bm.INPUTS["attendance"]["sets"].values())
        self.assertTrue(all(best(x) > 0 for x in np.arange(0, 100.001, 0.5)))
        self.assertAlmostEqual(best(70), 5 / 75, places=6)    # danger(70); ok(70) = 0
        self.assertAlmostEqual(best(85), 0.25, places=6)      # safe(85) = 5/20; ok(85) = 0

    def test_reachable_score_range_is_not_zero_to_hundred(self):
        """Centroids of shoulder sets cannot reach 0 or 100: the reachable raw range is about 14.9 to 85.1."""
        scores = [bm.evaluate(a, c, t).score
                  for a in np.arange(0, 100.1, 2.5) for c in np.arange(1, 4.1, 0.5) for t in np.arange(0, 10.1, 1)]
        self.assertTrue(all(0 <= s <= 100 for s in scores))
        self.assertAlmostEqual(min(scores), 14.9167, places=3)
        self.assertAlmostEqual(max(scores), 85.0833, places=3)

    def test_raw_score_is_high_just_below_75_but_final_is_attend(self):
        """Documented consequence of danger=(0,0,75): at 72% the raw verdict is CAN SKIP, the policy still says attend."""
        ev = bm.evaluate(72, 2.5, 9)
        self.assertAlmostEqual(ev.score, 76.8, places=1)
        self.assertEqual(ev.raw_verdict, "CAN SKIP THE CLASS")
        self.assertEqual(ev.final_text, bm.BELOW_MINIMUM_TEXT)
        self.assertTrue(ev.overridden)

    def test_final_recommendation_below_75_is_attend_across_whole_grid(self):
        for a, c, t in itertools.product(np.arange(0, 75, 0.5), (1, 2.5, 4), (0, 5, 10)):
            self.assertEqual(bm.evaluate(a, c, t).final_text, bm.BELOW_MINIMUM_TEXT)

    def test_known_limitation_verdict_flip_with_rising_attendance(self):
        """KNOWN LIMITATION (not a fix): between 75% and 100% the raw verdict can move CAUTION -> CANNOT SKIP as
        attendance rises, because ok falls faster than safe rises (their sum dips to 0.25 at 85%). It is a
        threshold crossing of about one score point. If this test starts failing the model changed:
        update README/docs/report together."""
        ev_a, ev_b = bm.evaluate(81.75, 2, 0), bm.evaluate(82, 2, 0)
        self.assertEqual(ORDER[ev_a.raw_verdict], 1)
        self.assertEqual(ORDER[ev_b.raw_verdict], 0)
        worst = 0.0
        for c in np.arange(1, 4.01, 0.5):
            for t in np.arange(0, 10.01, 0.5):
                s = [bm.evaluate(a, c, t).score for a in np.arange(75, 100.01, 0.25)]
                worst = min(worst, float(np.diff(s).min()))
        self.assertGreater(worst, -1.2)     # observed largest single step down is about -1.06
        self.assertLess(worst, -1.0)

    def test_centroid_discretisation_error_is_small(self):
        """401 sample points vs a 20001-point reference: error stays well under 0.1 score points."""
        rng = np.random.default_rng(0)
        xs = np.linspace(0, 100, 20001)
        shapes = {k: np.array([bm.trimf(x, *abc) for x in xs]) for k, abc in bm.OUTPUT_SETS.items()}
        for _ in range(25):
            ev = bm.evaluate(rng.uniform(0, 100), rng.uniform(1, 4), rng.uniform(0, 10))
            agg = np.zeros_like(xs)
            for k, s in ev.out_strength.items():
                agg = np.maximum(agg, np.minimum(s, shapes[k]))
            self.assertLess(abs((xs * agg).sum() / agg.sum() - ev.score), 0.1)


class TestFallbackFlag(unittest.TestCase):
    def test_flag_is_false_for_valid_inputs(self):
        for a, c, t in itertools.product((0, 37.5, 75, 100), (1, 2.5, 4), (0, 5, 10)):
            self.assertFalse(bm.evaluate(a, c, t).fallback_used)

    def test_zero_area_is_reported_not_silent(self):
        zero = np.zeros_like(bm.OUTPUT_XS)
        self.assertEqual(bm.defuzzify(bm.OUTPUT_XS, zero), 50.0)   # neutral value
        self.assertFalse(zero.sum() > 0)                             # exactly the test evaluate() uses for the flag


if __name__ == "__main__":
    unittest.main()
