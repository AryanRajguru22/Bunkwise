"""Regression: the inference engine must reproduce the ORIGINAL academic model exactly.

tests/golden.json was recorded from commit 89dcd27 (before the product polish) by tests/make_golden.py.
Any change to membership functions, rules, operators or defuzzification shows up here.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bunk_meter as bm

with open(os.path.join(ROOT, "tests", "golden.json"), encoding="utf-8") as f:
    GOLDEN = json.load(f)


class TestGoldenValues(unittest.TestCase):
    def test_cases_are_present(self):
        self.assertGreater(len(GOLDEN), 800)

    def test_infer_matches_original_model(self):
        for case in GOLDEN:
            a, c, t = case["in"]
            _, fired, out_strength, _, agg, score = bm.infer(
                {"attendance": a, "credits": c, "temptation": t})
            msg = str(case["in"])
            self.assertAlmostEqual(score, case["score"], places=12, msg=msg)
            self.assertAlmostEqual(float(agg.sum()), case["area"], places=12, msg=msg)
            for name, strength in case["out_strength"].items():
                self.assertAlmostEqual(out_strength[name], strength, places=12, msg=msg)
            self.assertEqual(len(fired), len(case["fired"]), msg)
            for got, want in zip(fired, case["fired"]):
                self.assertAlmostEqual(got[0], want[0], places=12, msg=msg)
                self.assertEqual(list(got[1:]), want[1:], msg)


if __name__ == "__main__":
    unittest.main()
