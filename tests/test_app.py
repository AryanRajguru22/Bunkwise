"""UI consistency tests using Streamlit's headless AppTest (no browser needed)."""
import os
import sys
import unittest

from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import bunk_meter as bm

APP = os.path.join(ROOT, "app.py")


def page_text(at):
    return "\n".join(m.value for m in at.markdown)


def load():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    return at


class TestApp(unittest.TestCase):
    def check_matches_infer(self, at, att, cred, temp):
        score = bm.infer({"attendance": att, "credits": cred, "temptation": temp})[-1]
        text = page_text(at)
        self.assertIn(f"{score:.1f}<small", text)                         # raw fuzzy score
        self.assertIn(f"<b>{bm.verdict(score)[0]}</b>", text)             # raw fuzzy verdict
        self.assertIn(bm.final_recommendation(score, att)[0], text)       # final recommendation
        self.assertEqual(len(at.error) > 0, att < 75)                     # attendance banner iff < 75%

    def test_default_render_matches_inference(self):
        at = load()
        self.check_matches_infer(at, 78.0, 2.5, 8.0)
        self.assertIn("Skip the guesswork. Know your risk.", page_text(at))

    def test_slider_change_updates_result(self):
        at = load()
        at.slider(key="attendance").set_value(50.0)
        at.slider(key="credits").set_value(4.0)
        at.slider(key="temptation").set_value(3.0)
        at.run()
        self.assertFalse(at.exception)
        self.check_matches_infer(at, 50.0, 4.0, 3.0)
        self.assertIn("Below the mandatory 75% attendance", at.error[0].value)
        self.assertIn(bm.BELOW_MINIMUM_TEXT, page_text(at))

    def test_every_preset_runs_the_same_inference(self):
        at = load()
        for label, att, cred, temp, _ in self.presets():
            at.button(key=f"preset_{label}").click()
            at.run()
            self.assertFalse(at.exception, label)
            self.assertEqual(at.slider(key="attendance").value, att)
            self.assertEqual(at.slider(key="credits").value, cred)
            self.assertEqual(at.slider(key="temptation").value, temp)
            self.check_matches_infer(at, att, cred, temp)
            # independent expectation of the policy-aware output for each demo scenario
            expected = bm.BELOW_MINIMUM_TEXT if att < 75 else bm.verdict(bm.infer(
                {"attendance": att, "credits": cred, "temptation": temp})[-1])[0]
            self.assertIn(expected, page_text(at), label)

    def test_below_75_preset_with_high_score_is_overridden(self):
        at = load()
        at.button(key="preset_Below 75%, score still high").click()
        at.run()
        score = bm.infer({"attendance": 72.0, "credits": 2.5, "temptation": 9.0})[-1]
        self.assertGreaterEqual(score, 65)                      # raw fuzzy verdict is "CAN SKIP"
        text = page_text(at)
        self.assertIn(f"{score:.1f}<small", text)               # raw score still displayed unchanged
        self.assertIn(f"<b>{bm.verdict(score)[0]}</b>", text)   # raw verdict still displayed
        self.assertIn(bm.BELOW_MINIMUM_TEXT, text)              # final recommendation overrides it
        self.assertEqual(len(at.error), 1)
        self.assertIn("overrides the final recommendation", at.error[0].value)

    def test_exactly_75_and_above_follow_fuzzy_verdict(self):
        for att in (75.0, 80.0, 95.0):
            at = load()
            at.slider(key="attendance").set_value(att)
            at.run()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.error), 0, att)
            self.check_matches_infer(at, att, 2.5, 8.0)
            self.assertNotIn(bm.BELOW_MINIMUM_TEXT, page_text(at))

    def test_no_streamlit_warnings_on_load(self):
        at = load()
        self.assertEqual(len(at.warning), 0)

    def test_active_rule_table_comes_from_inference(self):
        at = load()
        fired = bm.infer({"attendance": 78.0, "credits": 2.5, "temptation": 8.0})[1]
        rules_df = [d.value for d in at.dataframe if "Strength" in d.value.columns][0]
        self.assertEqual(len(rules_df), len(fired))
        self.assertAlmostEqual(rules_df["Strength"].iloc[0], fired[0][0])

    @staticmethod
    def presets():
        # Parse PRESETS from the app source so the test follows the app without importing Streamlit UI code.
        import ast
        with open(APP, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.Assign) and node.targets[0].id == "PRESETS":
                return ast.literal_eval(node.value)
        raise AssertionError("PRESETS not found")


if __name__ == "__main__":
    unittest.main()
