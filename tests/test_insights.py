"""Tests for the presentation helpers (no Streamlit needed)."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bunk_meter as bm
import insights


class TestEvaluate(unittest.TestCase):
    def test_evaluate_matches_infer_and_policy(self):
        for att, cred, temp in [(78, 2.5, 8), (72, 2.5, 9), (75, 1, 0), (100, 4, 10), (0, 1, 0)]:
            ev = bm.evaluate(att, cred, temp)
            score = bm.infer({"attendance": att, "credits": cred, "temptation": temp})[-1]
            self.assertEqual(ev.score, score)
            self.assertEqual(ev.raw_verdict, bm.verdict(score)[0])
            self.assertEqual(ev.final_text, bm.final_recommendation(score, att)[0])
            self.assertEqual(ev.below_minimum, att < 75)

    def test_override_flag_only_when_policy_changes_verdict(self):
        self.assertTrue(bm.evaluate(72, 2.5, 9).overridden)        # raw CAN SKIP, final ATTEND
        self.assertFalse(bm.evaluate(78, 2.5, 8).overridden)
        self.assertFalse(bm.evaluate(75, 2.5, 8).overridden)       # exactly 75% follows the fuzzy verdict
        # below 75% the raw verdict can already be "cannot skip" but the final text is still the policy text
        self.assertEqual(bm.evaluate(50, 4, 3).final_text, bm.BELOW_MINIMUM_TEXT)

    def test_fired_rules_sorted_strongest_first(self):
        fired = bm.evaluate(78, 2.5, 8).fired
        self.assertEqual(fired, sorted(fired, reverse=True))

    def test_evaluation_is_immutable_and_rejects_bad_input(self):
        ev = bm.evaluate(78, 2.5, 8)
        with self.assertRaises(Exception):
            ev.score = 1.0
        for bad in [(float("nan"), 2, 5), (101, 2, 5), (50, 5, 5), (50, 2, -1), (True, 2, 5)]:
            with self.assertRaises(ValueError):
                bm.evaluate(*bad)

    def test_output_shapes_are_read_only_and_match_trimf(self):
        for name, abc in bm.OUTPUT_SETS.items():
            shape = bm.OUTPUT_SHAPES[name]
            self.assertFalse(shape.flags.writeable)
            for x, y in zip(bm.OUTPUT_XS, shape):
                self.assertEqual(y, bm.trimf(x, *abc))


class TestExplain(unittest.TestCase):
    def test_four_steps_and_policy_wording(self):
        steps = insights.explain(bm.evaluate(72, 2.5, 9))
        self.assertEqual(len(steps), 4)
        self.assertIn("below the mandatory 75%", steps[3])
        self.assertIn(bm.BELOW_MINIMUM_TEXT, steps[3])
        steps = insights.explain(bm.evaluate(80, 2.5, 9))
        self.assertIn("at or above the mandatory 75%", steps[3])
        self.assertIn("not proof that skipping is safe", steps[3])

    def test_scores_in_text_come_from_engine(self):
        ev = bm.evaluate(78, 2.5, 8)
        self.assertIn(f"{ev.score:.1f} / 100", insights.explain(ev)[2])


class TestSweep(unittest.TestCase):
    def test_sweep_covers_zero_to_hundred_and_matches_engine(self):
        rows = insights.attendance_sweep(2.5, 8)
        self.assertEqual(len(rows), 101)
        self.assertEqual(rows[0]["attendance"], 0)
        self.assertEqual(rows[-1]["attendance"], 100)
        for r in rows[::10]:
            self.assertEqual(r["score"], bm.evaluate(r["attendance"], 2.5, 8).score)
        self.assertTrue(all(r["final"] == bm.BELOW_MINIMUM_TEXT for r in rows if r["attendance"] < 75))

    def test_attendance_for_verdict(self):
        att = insights.attendance_for_verdict(2.5, 8, 65)
        self.assertIsNotNone(att)
        self.assertGreaterEqual(bm.evaluate(att, 2.5, 8).score, 65)
        if att > 75:
            self.assertLess(bm.evaluate(att - 0.5, 2.5, 8).score, 65)
        self.assertIsNone(insights.attendance_for_verdict(1, 0, 65))  # fragile + no temptation never reaches 65


class TestCompare(unittest.TestCase):
    def test_valid_rows_use_engine_and_policy(self):
        rows = insights.compare_subjects([
            {"name": "A", "attendance": 72, "credits": 2.5, "temptation": 9},
            {"name": "B", "attendance": 90, "credits": 4, "temptation": 2}])
        self.assertEqual(rows[0]["final"], bm.BELOW_MINIMUM_TEXT)
        self.assertTrue(rows[0]["overridden"])
        self.assertEqual(rows[0]["score"], bm.evaluate(72, 2.5, 9).score)
        self.assertEqual(rows[1]["final"], bm.evaluate(90, 4, 2).final_text)

    def test_bad_rows_are_flagged_not_raised(self):
        nan = float("nan")
        rows = insights.compare_subjects([
            {"name": None, "attendance": nan, "credits": 2, "temptation": 5},
            {"name": "x", "attendance": 101, "credits": 2, "temptation": 5},
            {"name": "y", "attendance": "abc", "credits": 2, "temptation": 5},
            {"name": "z", "attendance": 80, "credits": None, "temptation": 5},
            {"name": "w", "attendance": float("inf"), "credits": 2, "temptation": 5},
            {"name": "v", "attendance": True, "credits": 2, "temptation": 5}])
        self.assertTrue(all(not r["valid"] and r["final"] == "Check inputs" for r in rows))
        self.assertEqual(rows[0]["name"], "Subject 1")

    def test_names_are_trimmed_and_row_count_capped(self):
        long = "x" * 100
        rows = insights.compare_subjects(
            [{"name": f"  {long}  ", "attendance": 80, "credits": 2, "temptation": 5}] * 20)
        self.assertEqual(len(rows), insights.MAX_SUBJECTS)
        self.assertEqual(len(rows[0]["name"]), insights.MAX_NAME_LENGTH)

    def test_html_in_names_stays_plain_data(self):
        rows = insights.compare_subjects([{"name": "<script>alert(1)</script>", "attendance": 80,
                                           "credits": 2, "temptation": 5}])
        self.assertEqual(rows[0]["name"], "<script>alert(1)</script>"[:insights.MAX_NAME_LENGTH])  # rendered in a table, never as HTML


class TestReport(unittest.TestCase):
    def test_report_contains_real_numbers_and_disclaimer(self):
        ev = bm.evaluate(72, 2.5, 9)
        text = insights.build_report(ev)
        self.assertIn(f"{ev.score:.1f} / 100", text)
        self.assertIn(bm.BELOW_MINIMUM_TEXT, text)
        self.assertIn(ev.raw_verdict, text)
        self.assertIn("overrides the fuzzy verdict", text)
        self.assertIn("not a probability", text)
        self.assertEqual(text.count("IF attendance="), len(ev.fired))

    def test_report_without_override(self):
        text = insights.build_report(bm.evaluate(90, 2.5, 8))
        self.assertNotIn("overrides the fuzzy verdict", text)
        self.assertTrue(math.isfinite(bm.evaluate(90, 2.5, 8).score))


if __name__ == "__main__":
    unittest.main()
