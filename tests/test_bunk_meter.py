"""Unit tests for the BunkWise fuzzy-logic core.  Run: python -m unittest discover -s tests -v"""
import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bunk_meter as bm


def run(att, cred, temp):
    return bm.infer({"attendance": att, "credits": cred, "temptation": temp})


class TestTrimf(unittest.TestCase):
    def test_peak_edges_and_midpoints(self):
        self.assertEqual(bm.trimf(78, 70, 78, 85), 1.0)
        self.assertEqual(bm.trimf(70, 70, 78, 85), 0.0)
        self.assertEqual(bm.trimf(85, 70, 78, 85), 0.0)
        self.assertAlmostEqual(bm.trimf(74, 70, 78, 85), 0.5)
        self.assertAlmostEqual(bm.trimf(81.5, 70, 78, 85), 0.5)

    def test_outside_support_is_zero(self):
        self.assertEqual(bm.trimf(69.9, 70, 78, 85), 0.0)
        self.assertEqual(bm.trimf(85.1, 70, 78, 85), 0.0)

    def test_degenerate_left_shoulder(self):  # (0, 0, 75): a == b
        self.assertEqual(bm.trimf(0, 0, 0, 75), 1.0)
        self.assertAlmostEqual(bm.trimf(37.5, 0, 0, 75), 0.5)
        self.assertEqual(bm.trimf(75, 0, 0, 75), 0.0)
        self.assertEqual(bm.trimf(80, 0, 0, 75), 0.0)

    def test_degenerate_right_shoulder(self):  # (80, 100, 100): b == c
        self.assertEqual(bm.trimf(100, 80, 100, 100), 1.0)
        self.assertAlmostEqual(bm.trimf(90, 80, 100, 100), 0.5)
        self.assertEqual(bm.trimf(80, 80, 100, 100), 0.0)
        self.assertEqual(bm.trimf(79, 80, 100, 100), 0.0)

    def test_every_configured_set_stays_in_unit_interval(self):
        for cfg in bm.INPUTS.values():
            lo, hi = cfg["range"]
            for abc in cfg["sets"].values():
                for x in np.linspace(lo, hi, 501):
                    self.assertTrue(0.0 <= bm.trimf(x, *abc) <= 1.0)
        for abc in bm.OUTPUT_SETS.values():
            for x in np.linspace(0, 100, 501):
                self.assertTrue(0.0 <= bm.trimf(x, *abc) <= 1.0)


class TestValidation(unittest.TestCase):
    def test_accepts_range_limits(self):
        run(0, 1, 0)
        run(100, 4, 10)

    def test_rejects_out_of_range(self):
        for bad in [(-1, 2, 5), (101, 2, 5), (50, 0.9, 5), (50, 4.1, 5), (50, 2, -0.1), (50, 2, 10.1)]:
            with self.assertRaises(ValueError, msg=str(bad)):
                run(*bad)

    def test_rejects_nan_inf_and_non_numbers(self):
        for bad in [(float("nan"), 2, 5), (50, float("inf"), 5), (50, 2, "high")]:
            with self.assertRaises(ValueError, msg=str(bad)):
                run(*bad)

    def test_rejects_missing_input(self):
        with self.assertRaises(ValueError):
            bm.infer({"attendance": 80, "credits": 2})


class TestRulesAndAggregation(unittest.TestCase):
    def test_rule_base_is_complete(self):
        self.assertEqual(len(bm.RULES), 18)  # 3 attendance x 3 credits x 2 temptation
        combos = {(a, c, t) for a, c, t, _ in bm.RULES}
        self.assertEqual(len(combos), 18)

    def test_firing_strength_is_min_of_antecedents(self):
        fuzzy, fired, *_ = run(78, 2.5, 8)
        self.assertEqual(len(fired), 1)  # only ok / moderate / high is non-zero
        s, a, c, t, out = fired[0]
        self.assertEqual((a, c, t, out), ("ok", "moderate", "high", "bunk"))
        self.assertAlmostEqual(s, min(1.0, 1.0, 2 / 3))  # temptation 'high' = (8-4)/6
        self.assertAlmostEqual(s, 2 / 3)

    def test_multiple_rules_use_each_rules_own_min(self):
        fuzzy, fired, *_ = run(90, 2, 9)
        for s, a, c, t, _ in fired:
            expected = min(fuzzy["attendance"][a], fuzzy["credits"][c], fuzzy["temptation"][t])
            self.assertAlmostEqual(s, expected)
        self.assertEqual({(a, c, t) for _, a, c, t, _ in fired},
                         {("safe", "fragile", "high"), ("safe", "moderate", "high")})

    def test_zero_strength_rules_are_not_reported_or_used(self):
        _, fired, out_strength, *_ = run(78, 2.5, 8)
        self.assertTrue(all(s > 0 for s, *_ in fired))
        self.assertEqual(out_strength["attend"], 0.0)
        self.assertEqual(out_strength["maybe"], 0.0)

    def test_output_strength_is_max_over_rules(self):
        _, fired, out_strength, *_ = run(90, 2, 9)
        for name in bm.OUTPUT_SETS:
            strengths = [s for s, *_, out in fired if out == name]
            self.assertAlmostEqual(out_strength[name], max(strengths, default=0.0))

    def test_aggregate_is_max_of_clipped_sets(self):
        _, _, out_strength, xs, agg, _ = run(90, 2, 9)
        expected = np.zeros_like(xs)
        for name, s in out_strength.items():
            shape = np.array([bm.trimf(x, *bm.OUTPUT_SETS[name]) for x in xs])
            expected = np.maximum(expected, np.minimum(s, shape))
        np.testing.assert_allclose(agg, expected)
        self.assertLessEqual(agg.max(), max(out_strength.values()) + 1e-12)

    def test_centroid_uses_aggregate(self):
        _, _, _, xs, agg, score = run(78, 2.5, 8)
        self.assertAlmostEqual(score, (xs * agg).sum() / agg.sum())

    def test_defuzzify_known_shapes(self):
        xs = np.linspace(0, 100, 401)
        flat = np.where((xs >= 40) & (xs <= 60), 1.0, 0.0)  # symmetric block -> centre 50
        self.assertAlmostEqual(bm.defuzzify(xs, flat), 50.0)
        right = np.where(xs >= 80, 1.0, 0.0)
        self.assertAlmostEqual(bm.defuzzify(xs, right), 90.0)

    def test_zero_area_falls_back_to_50(self):
        xs = np.linspace(0, 100, 401)
        self.assertEqual(bm.defuzzify(xs, np.zeros_like(xs)), 50.0)

    def test_some_rule_always_fires_over_the_whole_input_space(self):
        # Why the zero-area fallback is unreachable for valid inputs.
        for att in np.linspace(0, 100, 41):
            for cred in np.linspace(1, 4, 13):
                for temp in np.linspace(0, 10, 21):
                    _, fired, _, _, agg, _ = run(att, cred, temp)
                    self.assertTrue(fired)
                    self.assertGreater(agg.sum(), 0)


class TestScoresAndVerdicts(unittest.TestCase):
    def test_scores_finite_and_in_range_across_input_space(self):
        for att in np.linspace(0, 100, 21):
            for cred in np.linspace(1, 4, 7):
                for temp in np.linspace(0, 10, 11):
                    score = run(att, cred, temp)[-1]
                    self.assertTrue(math.isfinite(score))
                    self.assertTrue(0 <= score <= 100)

    def test_verdict_thresholds(self):
        self.assertEqual(bm.verdict(34.999)[0], "CANNOT SKIP THE CLASS!!")
        self.assertEqual(bm.verdict(35)[0], "PROCEED WITH CAUTION")
        self.assertEqual(bm.verdict(64.999)[0], "PROCEED WITH CAUTION")
        self.assertEqual(bm.verdict(65)[0], "CAN SKIP THE CLASS")
        self.assertEqual(bm.verdict(0)[0], "CANNOT SKIP THE CLASS!!")
        self.assertEqual(bm.verdict(100)[0], "CAN SKIP THE CLASS")

    def test_representative_scenarios(self):
        low = run(50, 4, 3)[-1]
        mid = run(90, 4, 2)[-1]
        high = run(100, 2.5, 10)[-1]
        self.assertLess(low, 35)
        self.assertTrue(35 <= mid < 65)
        self.assertGreaterEqual(high, 65)
        self.assertLess(low, mid)
        self.assertLess(mid, high)

    def test_default_demo_value(self):
        self.assertAlmostEqual(run(78, 2.5, 8)[-1], 83.82, places=2)

    def test_attendance_warning_depends_only_on_attendance(self):
        self.assertTrue(bm.below_attendance_minimum(74.9))
        self.assertFalse(bm.below_attendance_minimum(75))
        self.assertFalse(bm.below_attendance_minimum(100))
        # A high fuzzy score does not remove the warning:
        score = run(72, 2.5, 9)[-1]
        self.assertGreaterEqual(score, 65)
        self.assertTrue(bm.below_attendance_minimum(72))


if __name__ == "__main__":
    unittest.main()
