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
        self.assertIn(f"{score:.1f} / 100", text)                         # raw fuzzy score
        self.assertIn(f"**{bm.verdict(score)[0]}**", text)             # raw fuzzy verdict
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
        self.assertIn(f"{score:.1f} / 100", text)               # raw score still displayed unchanged
        self.assertIn(f"**{bm.verdict(score)[0]}**", text)   # raw verdict still displayed
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

    # ---------------------------------------------------------------- redesign features
    def test_five_original_scenarios_are_preserved(self):
        self.assertEqual([(a, b, c, d) for a, b, c, d, _ in self.presets()], [
            ("Balanced buffer", 78.0, 2.5, 8.0),
            ("Comfortable, heavy subject", 90.0, 4.0, 2.0),
            ("Low attendance", 50.0, 4.0, 3.0),
            ("Below 75%, score still high", 72.0, 2.5, 9.0),
            ("Easy subject, very safe", 95.0, 1.0, 9.0)])

    def test_main_tabs_and_download_button_exist(self):
        at = load()
        labels = [t.label for t in at.tabs]
        for expected in ("Why this result", "What if?", "Compare subjects", "Inside the engine",
                         "Fuzzification", "Active rules", "Aggregation & centroid", "Membership graphs",
                         "About & limits"):
            self.assertIn(expected, labels)
        self.assertEqual(len(at.get("download_button")), 1)

    def test_explanation_steps_follow_inference_and_policy(self):
        at = load()
        at.button(key="preset_Below 75%, score still high").click()
        at.run()
        text = page_text(at)
        self.assertIn("**4. Attendance policy.**", text)
        self.assertIn("below the mandatory 75%", text)
        score = bm.infer({"attendance": 72.0, "credits": 2.5, "temptation": 9.0})[-1]
        self.assertIn(f"**{score:.1f} / 100**, which the fuzzy verdict reads as", text)

    def test_comparison_table_uses_engine_and_policy(self):
        at = load()
        cmp_df = [d.value for d in at.dataframe if "Final recommendation" in d.value.columns][0]
        self.assertEqual(list(cmp_df["Subject"]), ["Subject A", "Subject B", "Subject C"])
        for (_, row), (att, cred, temp) in zip(cmp_df.iterrows(), [(78, 2.5, 8), (90, 4, 2), (72, 2, 9)]):
            ev = bm.evaluate(att, cred, temp)
            self.assertAlmostEqual(row["Raw score"], ev.score)
            self.assertEqual(row["Final recommendation"], ev.final_text)
        self.assertEqual(cmp_df["Final recommendation"].iloc[2], bm.BELOW_MINIMUM_TEXT)

    def test_comparison_table_never_triggers_the_policy_banner(self):
        at = load()  # default attendance 78%: Subject C (72%) is below 75% but must not raise st.error
        self.assertEqual(len(at.error), 0)

    def test_what_if_tab_reports_thresholds_from_the_engine(self):
        import insights
        at = load()   # default 2.5 credits / temptation 8: already >= 65 at the 75% minimum
        self.assertGreaterEqual(bm.evaluate(75, 2.5, 8.0).score, 65)
        self.assertIn("already 65 or more (*can skip*) at the 75% minimum", page_text(at))
        self.assertEqual(len(at.get("plotly_chart")), 6)  # gauge, what-if, aggregate, 3 input graphs
        # 4 credits / temptation 8: score first reaches 65 above the minimum
        at.slider(key="credits").set_value(4.0)
        at.run()
        first = insights.attendance_for_verdict(4.0, 8.0, 65)
        self.assertEqual(first, 84.0)
        self.assertIn(f"first reaches 65 (*can skip*) at about {first:g}% attendance", page_text(at))
        self.assertGreaterEqual(bm.evaluate(first, 4.0, 8.0).score, 65)
        self.assertLess(bm.evaluate(first - 0.5, 4.0, 8.0).score, 65)
        # 1 credit / temptation 10: never reaches 65 between 75% and 100%
        at.slider(key="credits").set_value(1.0)
        at.slider(key="temptation").set_value(10.0)
        at.run()
        self.assertIn("does not reach 65 (*can skip*) at any attendance from 75% to 100%", page_text(at))

    def test_bad_session_state_shows_error_and_reset(self):
        at = AppTest.from_file(APP, default_timeout=60)
        at.session_state["attendance"] = 150.0
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.error), 1)
        self.assertIn("Invalid input", at.error[0].value)
        at.button[0].click()
        at.run()
        self.assertEqual(len(at.error), 0)
        self.assertEqual(at.slider(key="attendance").value, 78.0)

    def test_extremes_render_without_exceptions(self):
        at = load()
        for att, cred, temp in [(0.0, 1.0, 0.0), (100.0, 4.0, 10.0), (75.0, 1.0, 10.0), (74.5, 4.0, 0.0)]:
            at.slider(key="attendance").set_value(att)
            at.slider(key="credits").set_value(cred)
            at.slider(key="temptation").set_value(temp)
            at.run()
            self.assertFalse(at.exception, (att, cred, temp))
            self.check_matches_infer(at, att, cred, temp)

    def set_counts(self, at, attended, held):
        at.number_input(key="planner_held").set_value(held)
        at.run()
        at.number_input(key="planner_attended").set_value(attended)
        at.run()
        self.assertFalse(at.exception, (attended, held))

    def test_planner_projects_skip_and_recovery_from_counts(self):
        import attendance_policy as ap
        at = load()
        for att, held in ((39, 50), (3, 4), (1, 2), (3, 10)):
            self.set_counts(at, att, held)
            p = ap.project(att, held)
            self.assertIn(f"{p.percent_now:.2f}%", page_text(at))
            msgs = " ".join(e.value for e in at.error) + " ".join(s.value for s in at.success)
            if p.meets_now:
                self.assertIn(f"{p.percent_if_skip:.2f}%", msgs)
            else:
                self.assertIn(f"Attend the next {p.to_recover} class", msgs)

    def test_planner_button_copies_percentage_without_crossing_75(self):
        at = load()
        label = "Use this attendance in the slider"
        self.set_counts(at, 224, 300)                      # 74.67%: rounds down to 74.5, still below 75
        next(b for b in at.button if b.label == label).click()
        at.run()
        self.assertEqual(at.slider(key="attendance").value, 74.5)
        self.set_counts(at, 225, 300)                      # exactly 75%: stays at 75.0
        next(b for b in at.button if b.label == label).click()
        at.run()
        self.assertEqual(at.slider(key="attendance").value, 75.0)
        self.assertFalse(at.exception)

    def test_planner_attended_is_clamped_when_held_shrinks(self):
        at = load()
        at.number_input(key="planner_held").set_value(10)
        at.run()
        self.assertFalse(at.exception)
        self.assertLessEqual(at.number_input(key="planner_attended").value, 10)

    def test_planner_slider_mismatch_is_flagged(self):
        at = load()                                        # slider 78%, counts 39/50 = 78%: consistent
        self.assertEqual(len(at.warning), 0)
        self.set_counts(at, 20, 50)
        self.assertTrue(any("slider" in w.value for w in at.warning))

    @staticmethod
    def presets():
        # Parse PRESETS from the app source so the test follows the app without importing Streamlit UI code.
        import ast
        with open(APP, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "PRESETS":
                return ast.literal_eval(node.value)
        raise AssertionError("PRESETS not found")


if __name__ == "__main__":
    unittest.main()
