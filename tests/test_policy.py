"""Tests for the crisp 75% policy projection (attendance_policy.py), independent of the fuzzy engine."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import attendance_policy as ap


class TestPolicyBoundaries(unittest.TestCase):
    def test_exact_75_percent_meets_minimum(self):
        self.assertTrue(ap.meets_minimum(3, 4))
        self.assertTrue(ap.meets_minimum(75, 100))
        self.assertFalse(ap.meets_minimum(74, 100))
        self.assertFalse(ap.meets_minimum(224, 300))   # 74.666...%
        self.assertTrue(ap.meets_minimum(225, 300))

    def test_above_and_below(self):
        self.assertTrue(ap.meets_minimum(39, 50))
        self.assertFalse(ap.meets_minimum(1, 2))

    def test_no_classes_held(self):
        self.assertIsNone(ap.percent(0, 0))
        self.assertTrue(ap.meets_minimum(0, 0))
        self.assertEqual((ap.max_safe_skips(0, 0), ap.classes_to_recover(0, 0)), (0, 0))

    def test_invalid_counts_rejected(self):
        for bad in ((5, 4), (-1, 4), (1, -4), (1.5, 4), (True, 4), ("3", 4), (None, 4)):
            with self.assertRaises(ValueError, msg=repr(bad)):
                ap.project(*bad)

    def test_worked_examples(self):
        p = ap.project(39, 50)   # 78%
        self.assertEqual((p.safe_skips, p.to_recover, p.meets_if_skip), (2, 0, True))
        self.assertAlmostEqual(p.percent_if_skip, 100 * 39 / 51)
        p = ap.project(3, 4)     # exactly 75%: the next miss breaks the rule
        self.assertEqual((p.meets_now, p.safe_skips, p.meets_if_skip), (True, 0, False))
        p = ap.project(1, 2)     # 50%: needs 3H - 4A = 2 straight classes
        self.assertEqual((p.meets_now, p.to_recover), (False, 2))

    def test_policy_matches_brute_force_for_all_small_counts(self):
        """The closed-form skip/recovery counts agree with simply simulating the classes one by one."""
        for held in range(0, 121):
            for att in range(0, held + 1):
                skips = 0
                while ap.meets_minimum(att, held + skips + 1):
                    skips += 1
                expected_skips = skips if ap.meets_minimum(att, held) else 0
                recover = 0
                while not ap.meets_minimum(att + recover, held + recover):
                    recover += 1
                self.assertEqual(ap.max_safe_skips(att, held), expected_skips, (att, held))
                self.assertEqual(ap.classes_to_recover(att, held), recover, (att, held))

    def test_policy_never_touches_the_fuzzy_engine(self):
        import bunk_meter as bm
        before = bm.evaluate(78, 2.5, 8).score
        ap.project(10, 50)
        self.assertEqual(bm.evaluate(78, 2.5, 8).score, before)


if __name__ == "__main__":
    unittest.main()
