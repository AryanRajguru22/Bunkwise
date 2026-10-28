"""The text of the final project report, as a list of blocks (see final_report_render.py).

Every number that comes from the implementation is taken from `ctx`, which generate_final_report.py fills by
running the real bunk_meter code and the real test suite.
"""
from final_report_render import BUL, CASES, CODE, EQ, FIG, H1, H2, H3, NOTE, NUM, P, REFS, TAB

TITLE = "BunkWise: A Fuzzy-Logic (Mamdani) Attendance Decision-Support Tool"

REFERENCES = {
    "zadeh65": 'L. A. Zadeh, "Fuzzy sets," *Information and Control*, vol. 8, no. 3, pp. 338–353, 1965. '
               "doi:10.1016/S0019-9958(65)90241-X.",
    "zadeh73": 'L. A. Zadeh, "Outline of a new approach to the analysis of complex systems and decision processes," '
               "*IEEE Transactions on Systems, Man, and Cybernetics*, vol. SMC-3, no. 1, pp. 28–44, Jan. 1973.",
    "zadeh75": 'L. A. Zadeh, "The concept of a linguistic variable and its application to approximate reasoning—I," '
               "*Information Sciences*, vol. 8, no. 3, pp. 199–249, 1975.",
    "zadeh94": 'L. A. Zadeh, "Fuzzy logic, neural networks, and soft computing," *Communications of the ACM*, '
               "vol. 37, no. 3, pp. 77–84, Mar. 1994.",
    "mamdani74": 'E. H. Mamdani, "Application of fuzzy algorithms for control of simple dynamic plant," '
                 "*Proceedings of the IEE*, vol. 121, no. 12, pp. 1585–1588, Dec. 1974.",
    "mamdani75": 'E. H. Mamdani and S. Assilian, "An experiment in linguistic synthesis with a fuzzy logic controller," '
                 "*International Journal of Man-Machine Studies*, vol. 7, no. 1, pp. 1–13, 1975.",
    "lee90a": 'C. C. Lee, "Fuzzy logic in control systems: fuzzy logic controller—Part I," *IEEE Transactions on '
              "Systems, Man, and Cybernetics*, vol. 20, no. 2, pp. 404–418, Mar./Apr. 1990.",
    "lee90b": 'C. C. Lee, "Fuzzy logic in control systems: fuzzy logic controller—Part II," *IEEE Transactions on '
              "Systems, Man, and Cybernetics*, vol. 20, no. 2, pp. 419–435, Mar./Apr. 1990.",
    "leekwijck99": 'W. Van Leekwijck and E. E. Kerre, "Defuzzification: criteria and classification," *Fuzzy Sets and '
                   "Systems*, vol. 108, no. 2, pp. 159–178, 1999.",
    "klir95": "G. J. Klir and B. Yuan, *Fuzzy Sets and Fuzzy Logic: Theory and Applications*. Upper Saddle River, NJ, USA: "
              "Prentice Hall, 1995.",
    "ross10": "T. J. Ross, *Fuzzy Logic with Engineering Applications*, 3rd ed. Chichester, U.K.: Wiley, 2010.",
    "jang93": 'J.-S. R. Jang, "ANFIS: adaptive-network-based fuzzy inference system," *IEEE Transactions on Systems, '
              "Man, and Cybernetics*, vol. 23, no. 3, pp. 665–685, May/Jun. 1993.",
    "jang97": "J.-S. R. Jang, C.-T. Sun, and E. Mizutani, *Neuro-Fuzzy and Soft Computing: A Computational Approach to "
              "Learning and Machine Intelligence*. Upper Saddle River, NJ, USA: Prentice Hall, 1997.",
    "python": "Python Software Foundation, *The Python Language Reference* and *unittest — Unit testing framework*, "
              "Python 3 documentation. [Online]. Available: https://docs.python.org/3/",
    "numpy": "C. R. Harris et al., \"Array programming with NumPy,\" *Nature*, vol. 585, pp. 357–362, 2020. "
             "doi:10.1038/s41586-020-2649-2.",
    "pandas": 'W. McKinney, "Data structures for statistical computing in Python," in *Proc. 9th Python in Science '
              "Conference (SciPy 2010)*, 2010, pp. 56–61.",
    "matplotlib": 'J. D. Hunter, "Matplotlib: a 2D graphics environment," *Computing in Science & Engineering*, '
                  "vol. 9, no. 3, pp. 90–95, 2007.",
    "streamlit": "Streamlit Inc., *Streamlit documentation* (including the App testing API). [Online]. Available: "
                 "https://docs.streamlit.io/",
    "plotly": "Plotly Technologies Inc., *Plotly Python Graphing Library documentation*. [Online]. Available: "
              "https://plotly.com/python/",
    "playwright": "Microsoft, *Playwright for Python documentation*. [Online]. Available: https://playwright.dev/python/",
    "pythondocx": "S. Canny et al., *python-docx documentation*. [Online]. Available: https://python-docx.readthedocs.io/",
}

TEST_AREAS = [  # (area, objective, expected behaviour, [test method names])
    ("Membership functions", "Check trimf() at peaks, feet, mid-slopes, outside the support and for both degenerate shoulders; "
     "check every configured set stays within [0, 1].",
     "Peak = 1, feet = 0, mid-slope = 0.5, outside = 0; (0, 0, 75) and (80, 100, 100) give 1 at the flat edge; no value outside [0, 1].",
     ["test_peak_edges_and_midpoints", "test_outside_support_is_zero", "test_degenerate_left_shoulder",
      "test_degenerate_right_shoulder", "test_every_configured_set_stays_in_unit_interval"]),
    ("Input validation", "Check that infer() accepts the range limits and rejects out-of-range, NaN, infinite, non-numeric, "
     "boolean and missing inputs.",
     "Limits accepted; every invalid case raises ValueError.",
     ["test_accepts_range_limits", "test_rejects_out_of_range", "test_rejects_nan_inf_and_non_numbers",
      "test_rejects_missing_input", "test_bool_inputs_rejected_by_infer"]),
    ("Rule base and firing strength", "Check rule-base completeness, the min operator, per-rule strengths, exclusion of zero-strength "
     "rules and the max over rules that share a consequent.",
     "18 distinct rules; strength = min of the three degrees (2/3 for the 78 / 2.5 / 8 example); strengths > 0 only; output strength = max.",
     ["test_rule_base_is_complete", "test_firing_strength_is_min_of_antecedents",
      "test_multiple_rules_use_each_rules_own_min", "test_zero_strength_rules_are_not_reported_or_used",
      "test_output_strength_is_max_over_rules"]),
    ("Aggregation and centroid", "Check that the aggregate equals the max of the clipped sets and that the score is the centroid of "
     "that aggregate; check defuzzify() on known shapes.",
     "Aggregate matches an independent recomputation; centroid of a symmetric block is 50, of a block on [80, 100] is 90.",
     ["test_aggregate_is_max_of_clipped_sets", "test_centroid_uses_aggregate", "test_defuzzify_known_shapes"]),
    ("Zero-area fallback and rule coverage", "Check the neutral fallback and that it cannot be reached for valid inputs.",
     "defuzzify() returns 50 for an all-zero aggregate; on a 41 x 13 x 21 grid of valid inputs at least one rule always fires.",
     ["test_zero_area_falls_back_to_50", "test_some_rule_always_fires_over_the_whole_input_space"]),
    ("Scores and raw verdict", "Check score range, verdict thresholds, representative scenarios and the documented default score.",
     "Finite scores in [0, 100] on a 21 x 7 x 11 grid; thresholds at 35 and 65; default score 83.82 (2 decimals).",
     ["test_scores_finite_and_in_range_across_input_space", "test_verdict_thresholds",
      "test_representative_scenarios", "test_default_demo_value",
      "test_attendance_warning_depends_only_on_attendance"]),
    ("Attendance-policy override", "Check final_recommendation(): below 75 % always attend, normal thresholds at 75 % and above, raw "
     "score untouched, invalid arguments rejected.",
     "Below 75: BELOW-MINIMUM text for every score; at 75 and above: equals verdict(); score 76.77 unchanged by the policy step.",
     ["test_below_75_is_always_attend", "test_high_score_cannot_bypass_the_constraint",
      "test_exactly_75_uses_normal_thresholds", "test_above_75_uses_normal_thresholds",
      "test_raw_score_is_unchanged_by_the_policy_step", "test_invalid_arguments_are_rejected"]),
    ("Streamlit interface (AppTest)", "Run app.py headlessly and compare what it displays with bunk_meter.infer(): default view, "
     "slider changes, all five presets, the override preset, boundary attendance values, warnings and the rule table.",
     "Displayed score, raw verdict and final recommendation equal the engine output; error banner only below 75 %; no script exception or warning.",
     ["test_default_render_matches_inference", "test_slider_change_updates_result",
      "test_every_preset_runs_the_same_inference", "test_below_75_preset_with_high_score_is_overridden",
      "test_exactly_75_and_above_follow_fuzzy_verdict", "test_no_streamlit_warnings_on_load",
      "test_active_rule_table_comes_from_inference"]),
]

SHORT_VERDICT = {"CANNOT SKIP THE CLASS!!": "CANNOT SKIP", "PROCEED WITH CAUTION": "CAUTION",
                 "CAN SKIP THE CLASS": "CAN SKIP", "ATTEND CLASS — BELOW MINIMUM ATTENDANCE": "ATTEND (below 75%)"}


def build(ctx):
    bm = ctx["bm"]
    F = ctx["figs"]
    S = ctx["screens"]
    e1, e2, facts, tests = ctx["E1"], ctx["E2"], ctx["facts"], ctx["tests"]
    v = ctx["versions"]
    B = []
    add = B.append

    sc1, sc2 = e1["score"], e2["score"]
    mu = e1["fuzzy"]

    # ================================================================ 1 ABSTRACT
    add(H1("Abstract"))
    add(P("Deciding whether to attend a particular class involves several considerations at once: how much attendance a "
          "student has accumulated, how much weight one class carries, and how strongly the student wants to skip. A single "
          "crisp threshold cannot express such graded judgements. This report presents **BunkWise**, an interactive "
          "decision-support tool that combines three inputs, namely attendance percentage (0–100), subject credits (1–4) and "
          "temptation to skip (0–10), into a single index called the **Bunk Score** (0–100), using a Mamdani fuzzy inference system."))
    add(P("The objectives were to model the decision with linguistic variables and IF–THEN rules, to implement the full Mamdani "
          "pipeline faithfully, to keep the final recommendation consistent with a mandatory 75% attendance requirement, and to "
          "make every intermediate step visible to the user. The method uses triangular membership functions (eight input sets and "
          "three output sets), an 18-rule hand-written rule base, the minimum operator for fuzzy AND, clipping implication, maximum "
          "aggregation and centroid defuzzification over a 401-point grid. The raw score is mapped to a three-way fuzzy verdict; a "
          "separate, non-fuzzy policy step then enforces that attendance below 75% always yields the recommendation to attend, without "
          "altering the raw score."))
    add(P("The fuzzy engine (`bunk_meter.py`, Python and NumPy) is displayed through a Streamlit application (`app.py`) that shows a "
          "score gauge, the final recommendation, the fuzzification of each input, the active rules with their firing strengths, the "
          "aggregated output with its centroid, and the membership graphs. The implementation is covered by "
          f"{tests['total']} automated tests ({tests['algo']} algorithm tests and {tests['ui']} interface tests), which all pass."))
    add(P("**BunkWise is a rule-based fuzzy decision-support tool. It is not a trained machine-learning predictor.** Its membership "
          "functions and rules were written by hand, nothing was learned from data, and the Bunk Score is a fuzzy index rather than a "
          "probability. The system has not been validated against real student decisions or outcomes; its limitations are discussed in "
          "Chapter 12."))
    add(P("**Keywords:** fuzzy logic, Mamdani inference, soft computing, centroid defuzzification, decision support, Streamlit."))

    # ================================================================ 2 INTRODUCTION
    add(H1("Introduction"))
    add(H2("Background and motivation"))
    add(P("Students regularly face a small but recurring decision: whether to attend a given class. The decision is rarely "
          "determined by one number. A student with a comfortable attendance record may still hesitate over a class that covers a "
          "great deal of syllabus, while a student close to the institutional minimum may feel more pressure over a one-credit "
          "subject in which each missed class lowers the percentage quickly. Personal inclination also plays a part. These "
          "considerations are imprecise, overlapping and expressed in words such as “comfortable”, “risky” or “heavy”, which is "
          "exactly the kind of knowledge that soft-computing techniques were designed to handle [[cite:zadeh94,jang97]]."))
    add(H2("Limits of a rigid binary decision"))
    add(P("A conventional program would encode the decision as a chain of crisp conditions, for example “attend if attendance is "
          "below 75”. Such a rule treats 74.9% and 75.1% as categorically different and says nothing about how far from the boundary "
          "a student is. It also has no natural way to blend several factors: each extra factor multiplies the number of "
          "hard-edged cases. Fuzzy logic replaces sharp class boundaries with degrees of membership between 0 and 1 [[cite:zadeh65]], "
          "so that, for instance, an attendance of 82% can be partly “ok” (0.43) and partly “safe” (0.10) at the same time, and "
          "neighbouring inputs produce neighbouring outputs."))
    add(H2("Purpose of fuzzy logic in this project"))
    add(P("The purpose of using fuzzy logic in BunkWise is to model a graded, multi-factor judgement in a transparent way. "
          "A Mamdani fuzzy inference system [[cite:mamdani75]] was chosen because its rules are written in near-natural language "
          "(“IF attendance is ok AND credits are moderate AND temptation is high THEN bunk”), its inference steps can be shown one by "
          "one, and its output can be inspected as a shape rather than only as a number. The project is also a vehicle for "
          "studying the Mamdani pipeline end to end, which is the learning goal of the Artificial Intelligence and Soft Computing "
          "course."))
    add(H2("An interactive, explainable interface"))
    add(P("A bare number would offer little insight, so the system is wrapped in an interactive interface. The user moves three "
          "sliders and immediately sees the score, a recommendation and a step-by-step explanation drawn from the same inference "
          "that produced the score. Because the explanation is generated from the real intermediate results rather than written "
          "separately, the interface doubles as a teaching aid for fuzzification, rule firing, aggregation and defuzzification."))
    add(H2("Scope and responsible use"))
    add(P("BunkWise is an educational decision-support tool. It does not encourage violating attendance rules: the mandatory "
          "75% attendance requirement is enforced as a hard constraint on the final recommendation, and the interface states that 75% "
          "is a minimum, not proof that skipping another class is safe. The scope of the work is limited to the three inputs above, a "
          "single subject at a time, and a hand-built rule base. It does not read real attendance records, does not know how many "
          "classes have been held or attended, and does not model any institutional policy other than the 75% minimum."))
    add(P("The rest of the report is organised as follows. Chapter 3 states the problem and objectives; Chapter 4 reviews the "
          "theory; Chapters 5 to 7 describe the design, the fuzzy sets and rules, and the inference algorithm; Chapter 8 works two "
          "examples by hand and by code; Chapters 9 and 10 cover the implementation and its testing; Chapters 11 to 14 discuss "
          "results, limitations, future scope and conclusions."))

    # ================================================================ 3 PROBLEM
    add(H1("Problem Statement and Objectives"))
    add(H2("Formal problem statement"))
    add(P("Let x_{1} denote the attendance percentage, x_{2} the subject credits and x_{3} the temptation to skip. The problem is to "
          "construct a mapping from these three crisp inputs to a single crisp index S, the raw Bunk Score, such that a higher "
          "value indicates that skipping one class is more tolerable, and then to derive a final recommendation R that respects "
          "the mandatory attendance minimum."))
    add(EQ("problem", r"S=f(x_1,x_2,x_3),\qquad f:\ [0,100]\times[1,4]\times[0,10]\ \longrightarrow\ [0,100]"))
    add(P("The function f is realised by a Mamdani fuzzy inference system. The final recommendation R is then obtained from S and x_{1} "
          "by a crisp policy step: below 75% it is always “attend”, and otherwise it follows the three-way verdict V(S)."))
    add(CASES("final", r"R(S,x_1)", [(r"\mathrm{ATTEND}", r"x_1<75"), (r"V(S)", r"x_1\ \geq\ 75")]))
    add(CASES("verdict", r"V(S)", [(r"\mathrm{CANNOT\ SKIP}", r"S<35"), (r"\mathrm{PROCEED\ WITH\ CAUTION}", r"35\leq S<65"),
                                   (r"\mathrm{CAN\ SKIP}", r"S\geq 65")]))
    add(H2("Input variables"))
    add(P("[[tab:inputs]] summarises the three inputs, their ranges and their linguistic terms."))
    add(TAB("inputs", "Input variables of BunkWise.", ["Variable", "Range", "Meaning", "Linguistic terms"], [
        ["Attendance (x_{1})", "0–100 (%)", "Current attendance percentage in the subject; the mandatory minimum is 75%.", "danger, ok, safe"],
        ["Subject credits (x_{2})", "1–4", "A rough proxy for how much one class matters: 1 is fragile (a miss lowers attendance quickly), 4 is heavy (much syllabus per class).", "fragile, moderate, heavy"],
        ["Temptation to skip (x_{3})", "0–10", "How strongly the user wants to skip the class: 0 not at all, 10 very strongly. Subjective, self-reported.", "low, high"],
    ], [2.2, 1.3, 5.0, 2.0], size=9))
    add(H2("Output variable"))
    add(P("The raw **Bunk Score** S lies between 0 and 100 and is described by three output terms: *attend*, *maybe* and *bunk*. A higher score means "
          "that the fuzzy rules consider skipping more tolerable. The score is a fuzzy index; it is not a probability and has no "
          "frequency interpretation. Scores below 35 are read as “cannot skip the class”, scores from 35 up to but excluding 65 as "
          "“proceed with caution”, and scores of 65 or more as “can skip the class”."))
    add(H2("Objectives"))
    add(NUM("To model attendance, subject credits and temptation as linguistic variables with triangular membership functions.",
            "To encode expert-style knowledge as an 18-rule IF–THEN rule base covering every combination of input terms.",
            "To implement Mamdani inference (min, clipping, max, centroid) in Python so that each stage is separately testable.",
            "To enforce the mandatory 75% attendance requirement as a hard, separate policy step that never alters the raw fuzzy score.",
            "To build an interactive Streamlit interface that shows the score, the recommendation and every intermediate step.",
            "To verify the implementation with an automated test suite and to document its limits honestly."))
    add(H2("Intended users"))
    add(P("The intended users are undergraduate students who want a structured, explainable way to think about a single attendance "
          "decision, and students and instructors of soft computing who want to see Mamdani inference working on a small, relatable "
          "problem. It is not intended as an authoritative advisory system or as a replacement for institutional attendance regulations."))

    # ================================================================ 4 BACKGROUND
    add(H1("Background and Theoretical Foundation"))
    add(H2("Artificial intelligence and soft computing"))
    add(P("Artificial intelligence is the study of building systems that perform tasks associated with intelligent behaviour. "
          "Soft computing, a term popularised by Zadeh, is a consortium of methodologies, chiefly fuzzy logic, neural networks and "
          "probabilistic reasoning, that tolerate imprecision, uncertainty and partial truth in order to achieve tractability and "
          "robustness [[cite:zadeh94]]. Fuzzy logic is the component that deals with imprecision expressed in linguistic terms, and "
          "it is the only soft-computing technique used in BunkWise."))
    add(H2("Classical logic versus fuzzy logic"))
    add(P("In classical (Boolean) logic an element either belongs to a set or does not; a statement is true or false. Fuzzy logic "
          "generalises this by allowing a degree of truth between 0 and 1 [[cite:zadeh65,klir95]]. The statement “attendance is "
          "safe” is then neither wholly true nor wholly false at 82%; it is true to degree 0.10. Classical logic is recovered as the "
          "special case in which all degrees are 0 or 1."))
    add(H2("Crisp values, fuzzy sets and linguistic variables"))
    add(P("A **crisp value** is an ordinary number such as an attendance of 78. A **fuzzy set** A on a universe of discourse X is "
          "characterised by a membership function μ_{A}: X → [0, 1], which assigns to each x a degree of membership [[cite:zadeh65]]:"))
    add(EQ("fuzzyset", r"A=\{(x,\ \mu_A(x))\ \mid\ x\in X\},\qquad \mu_A:\ X\to[0,1]"))
    add(P("A **linguistic variable** is a variable whose values are words rather than numbers, each word being a fuzzy set on an "
          "underlying numeric universe [[cite:zadeh75]]. In BunkWise, “attendance” is a linguistic variable on [0, 100] with the "
          "terms danger, ok and safe; “credits” and “temptation” are defined analogously."))
    add(H2("Membership functions and the triangular form"))
    add(P("A membership function can take many shapes. The **triangular** membership function is the simplest piecewise-linear form "
          "and is defined by three parameters: the start a, the peak b and the end c, where a ≤ b ≤ c. The function rises linearly "
          "from 0 at a to 1 at b and falls linearly back to 0 at c:"))
    add(CASES("trimf", r"\mu(x;a,b,c)", [
        (r"0", r"x<a\ \ \mathrm{or}\ \ x>c"),
        (r"1", r"x=b"),
        (r"\frac{x-a}{b-a}", r"a\leq x<b"),
        (r"\frac{c-x}{c-b}", r"b<x\leq c")]))
    add(P("When a = b or b = c the triangle degenerates into a right-angled “shoulder”, which is useful at the ends of a universe "
          "(for example “danger” starting at full membership at 0%). The explicit test x = b in the definition gives the value 1 "
          "at such a flat edge and prevents a division by zero; this is revisited in Chapter 6."))
    add(H2("Fuzzification"))
    add(P("**Fuzzification** converts a crisp input into the vector of membership degrees it has in each fuzzy set of its "
          "linguistic variable. For the input x_{1} = 78, evaluating the three attendance sets gives μ_{danger} = 0, μ_{ok} = 1 and "
          "μ_{safe} = 0."))
    add(H2("Fuzzy IF–THEN rules and fuzzy inference systems"))
    add(P("A fuzzy IF–THEN rule has the form “IF x_{1} is A AND x_{2} is C AND x_{3} is T THEN y is O”, where A, C, T and O are fuzzy sets. "
          "The part between IF and THEN is the **antecedent**; the part after THEN is the **consequent**. A **fuzzy inference system "
          "(FIS)** is a framework that fuzzifies the inputs, evaluates a base of such rules, combines their consequents and, if a "
          "crisp answer is required, defuzzifies the result [[cite:lee90a,ross10]]. The use of linguistic rules to "
          "describe complex systems goes back to Zadeh’s work on linguistic approaches to decision processes [[cite:zadeh73]]."))
    add(H2("Mamdani inference"))
    add(P("The Mamdani system [[cite:mamdani74,mamdani75]] represents both antecedents and consequents as fuzzy sets and "
          "produces a fuzzy output set that is then defuzzified. For rule k with antecedent sets A_{k}, C_{k}, T_{k} and consequent set "
          "O_{k}, the following operations are used."))
    add(P("**Fuzzy AND by the minimum t-norm.** The truth of the conjunction of two statements is the smaller of their degrees:"))
    add(EQ("and", r"\mu_{A\cap B}(x)=\min\left\{\mu_A(x),\ \mu_B(x)\right\}"))
    add(P("**Rule firing strength.** The firing strength α_{k} of rule k is the minimum of the membership degrees of the three "
          "crisp inputs x_{1}, x_{2}, x_{3} in the rule’s antecedent sets:"))
    add(EQ("firing", r"\alpha_k=\min\left\{\mu_{A_k}(x_1),\ \mu_{C_k}(x_2),\ \mu_{T_k}(x_3)\right\}"))
    add(P("**Implication by clipping.** The consequent set is truncated at the firing strength, so a rule that is only partly "
          "true contributes only a partial shape (this is Mamdani’s min implication):"))
    add(EQ("clip", r"\hat{\mu}_k(y)=\min\left\{\alpha_k,\ \mu_{O_k}(y)\right\}"))
    add(P("**Aggregation by the maximum.** The clipped consequents of all rules are combined by pointwise maximum into one "
          "output fuzzy set:"))
    add(EQ("agg", r"\mu_{\mathrm{agg}}(y)=\max_{k=1,\ldots,18}\ \hat{\mu}_k(y)"))
    add(P("**Defuzzification by the centroid.** Defuzzification turns the aggregated fuzzy set back into a single crisp number. The "
          "**centroid** (centre of area) method [[cite:lee90b,leekwijck99]] returns the abscissa of the centre of gravity of the area "
          "under μ_{agg}:"))
    add(EQ("centroid", r"y^{*}=\frac{\int_{0}^{100} y\,\mu_{\mathrm{agg}}(y)\,dy}{\int_{0}^{100}\mu_{\mathrm{agg}}(y)\,dy}"))
    add(P("On a computer the integrals are approximated on a finite grid y_{i}. BunkWise uses 401 equally spaced points "
          "y_{i} = 0.25 i for i = 0, …, 400, so that the centroid becomes a ratio of sums:"))
    add(EQ("centroid_d", r"y^{*}\approx\frac{\sum_{i=0}^{400} y_i\,\mu_{\mathrm{agg}}(y_i)}{\sum_{i=0}^{400}\mu_{\mathrm{agg}}(y_i)},\qquad y_i=0.25\,i"))
    add(NOTE("Fuzzy membership is not probability.",
             "A membership degree describes how well a value fits a vague concept; a probability describes the likelihood of an "
             "event. Attendance 82% belongs to “safe” to degree 0.10 because it only partly fits the concept, not because there is a "
             "10% chance that it is safe. Likewise a Bunk Score of 80 is not an 80% probability that skipping is safe, and it says nothing "
             "about the chance of any outcome. It is an index on a 0–100 scale defined by the membership functions and rules. Fuzzy "
             "degrees also need not sum to one and are combined with min and max rather than with the product and sum rules of probability "
             "[[cite:zadeh65,klir95]]."))

    # ================================================================ 5 SYSTEM ANALYSIS
    add(H1("System Analysis and Design"))
    add(H2("Functional requirements"))
    add(P("[[tab:fr]] lists what the system must do."))
    add(TAB("fr", "Functional requirements.", ["ID", "Requirement"], [
        ["FR1", "Accept attendance (0–100), subject credits (1–4) and temptation (0–10) from the user."],
        ["FR2", "Validate every input: present, a finite real number (not a boolean) and within its range."],
        ["FR3", "Fuzzify each input into degrees of membership in its fuzzy sets."],
        ["FR4", "Evaluate the 18-rule base with the minimum operator and report the rules whose strength is above zero."],
        ["FR5", "Clip, aggregate (maximum) and defuzzify (centroid) to give a raw Bunk Score from 0 to 100."],
        ["FR6", "Map the raw score to a raw fuzzy verdict (below 35, 35 to below 65, 65 and above)."],
        ["FR7", "Apply the mandatory 75% attendance rule separately, giving a final recommendation without changing the raw score."],
        ["FR8", "Display the score, the final recommendation, an attendance warning and a plain-language explanation."],
        ["FR9", "Show the fuzzification, active rules, aggregation and centroid, and membership graphs."],
        ["FR10", "Offer demonstration presets that set the three inputs and run the same inference."],
    ], [0.9, 10.0], size=9.5))
    add(H2("Non-functional requirements"))
    add(P("[[tab:nfr]] lists the quality requirements that shaped the design."))
    add(TAB("nfr", "Non-functional requirements.", ["Quality", "Requirement"], [
        ["Transparency", "All displayed numbers come from one call to `infer()`; the interface never recomputes them separately."],
        ["Correctness", "Implementation checked by an automated test suite, including independent recomputation of key quantities."],
        ["Responsiveness", "Inference runs on a 401-point grid and is designed for live slider use (no formal performance benchmark was made)."],
        ["Usability", "Three labelled sliders with explanatory captions, one-click presets and a readable warm light theme."],
        ["Maintainability", "Fuzzy engine separated from the interface; fuzzy sets and rules held as plain data (`INPUTS`, `OUTPUT_SETS`, `RULES`)."],
        ["Portability", "Pure Python with NumPy, Streamlit, Plotly and pandas and no platform-specific code (developed and tested on Windows)."],
        ["Honesty of claims", "The interface and documentation state that the score is an index, not a probability, and that no learning or validation was performed."],
    ], [2.4, 9.0], size=9.5))
    add(H2("Inputs, outputs and constraints"))
    add(P("The system takes three numeric inputs and produces four kinds of output: the raw Bunk Score, the raw fuzzy verdict, the "
          "final recommendation and the intermediate results (membership degrees, fired rules, output clip levels and the "
          "aggregated shape). The principal constraints are the fixed input ranges, the fixed rule base, the 75% attendance "
          "requirement taken from the course handout, and the fact that the system sees only the percentage, not the number of "
          "classes attended or held."))
    add(H2("Overall architecture"))
    add(P("[[fig:arch]] shows the two-layer architecture. The **fuzzy engine** in `bunk_meter.py` contains all fuzzy-logic "
          "computation and has no dependency on the interface; it exposes `trimf()`, `validate_inputs()`, `infer()`, `defuzzify()`, "
          "`verdict()`, `below_attendance_minimum()` and `final_recommendation()`. The **presentation layer** in `app.py` collects "
          "the inputs, calls the engine exactly once per interaction and renders the results."))
    add(FIG("arch", F["arch"], "Architecture of BunkWise: Streamlit presentation layer (left) and fuzzy engine (right). "
            "The dashed arrow carries the intermediate results used by the explanation tabs.", 6.2))
    add(H2("Data flow"))
    add(P("The data flow follows [[fig:flow]]. The inputs are validated; if validation fails, a `ValueError` is raised and the interface "
          "shows an error message and stops. Otherwise the inputs are fuzzified, all 18 rules are evaluated, and the strongest strength "
          "for each output set is retained. The output sets are clipped and aggregated on the 401-point grid, and the centroid is "
          "computed (with a neutral fallback of 50 if the aggregate had zero area). The raw score is then interpreted by `verdict()`, and "
          "`final_recommendation()` applies the attendance policy to give the final text shown to the user."))
    add(FIG("flow", F["flow"], "Flowchart of the inference algorithm and the attendance-policy step, as implemented in "
            "`infer()` and `final_recommendation()`.", 4.3))
    add(H2("Relationship between the fuzzy engine and the interface"))
    add(P("The interface treats the engine as the single source of truth. `app.py` calls `bm.infer(values)` once and receives "
          "`(fuzzy, fired, out_strength, xs, agg, score)`; every figure on the screen is derived from that tuple, from "
          "`verdict()` and from `final_recommendation()`. If the engine raises a `ValueError`, the interface displays it and stops. "
          "This separation also makes the engine testable without a browser, while the interface is tested separately against the "
          "engine’s output."))
    add(H2("Explainability features"))
    add(P("Explainability is a design goal rather than an add-on. The interface shows (i) a sentence naming the strongest rule and its "
          "firing strength, (ii) a table of the degrees to which each input belongs to each fuzzy set, (iii) a table of the rules that "
          "fired, with an expander listing all 18, (iv) the clip level of each output set together with the centroid computation "
          "Σ(x·μ)/Σμ, (v) plots of the unclipped output sets, the aggregate and the centroid, (vi) membership graphs with the current "
          "input marked, and (vii) a text description of the algorithm. The raw fuzzy verdict and the final recommendation are shown "
          "separately so that the effect of the attendance policy is never hidden."))

    # ================================================================ 6 MEMBERSHIP FUNCTIONS AND RULES
    add(H1("Membership Functions and Rule Base"))
    add(H2("Fuzzy sets used in the final implementation"))
    add(P("[[tab:params]] lists the fuzzy sets exactly as defined in `INPUTS` and `OUTPUT_SETS` in `bunk_meter.py`, and [[fig:mfs]] plots them. "
          "Each set is written as a triple (a, b, c) of start, peak and end."))
    rows = []
    for name, cfg in bm.INPUTS.items():
        for sname, abc in cfg["sets"].items():
            rows.append([name.capitalize(), sname, f"({', '.join(f'{x:g}' for x in abc)})", f"{cfg['range'][0]}–{cfg['range'][1]}"])
    for sname, abc in bm.OUTPUT_SETS.items():
        rows.append(["Output (Bunk Score)", sname, f"({', '.join(f'{x:g}' for x in abc)})", "0–100"])
    add(TAB("params", "Triangular fuzzy sets (a, b, c) in the final code.", ["Variable", "Fuzzy set", "(a, b, c)", "Universe"],
            rows, [3.0, 2.2, 2.6, 1.8], align=["l", "l", "c", "c"], mono_cols=(2,)))
    add(FIG("mfs", F["mfs"], "Membership functions of the three inputs and of the output Bunk Score, plotted with the real "
            "`trimf()` function. Dotted vertical lines on the output panel mark the verdict thresholds 35 and 65.", 6.2))
    add(P("The design intent recorded in the source and in the presentation is as follows. The attendance sets are anchored on the 75% "
          "requirement: “danger” covers the range below 75, “ok” is a narrow peak around 78 spanning 70 to 85, and “safe” starts at 80 and "
          "reaches full membership at 100. The credit sets separate a one-credit “fragile” subject, in which a single missed class "
          "reduces attendance sharply, a “moderate” two-to-three-credit subject, and a four-credit “heavy” subject with a lot of syllabus "
          "per class. Temptation is split into “low” and “high”, which overlap between 4 and 6. The three output sets overlap so that "
          "neighbouring scores blend smoothly."))
    add(H2("The triangular membership function and its endpoint cases"))
    add(P("[[eq:trimf]] is implemented by `trimf(x, a, b, c)`. Three cases deserve attention. First, outside the support "
          "(x < a or x > c) the result is 0. Second, at the peak (x = b) the result is exactly 1; this test comes before any division, so "
          "the degenerate shoulders (0, 0, 75), (1, 1, 2.5), (0, 0, 6), (0, 0, 45) and (80, 100, 100), (2.5, 4, 4), (4, 10, 10), "
          "(55, 100, 100) return 1 at their flat edge. Third, a division happens only when x lies strictly between a and b "
          "(so b − a > 0) or strictly between b and c (so c − b > 0), which means that no zero denominator can occur. At the far foot of "
          "a shoulder the formula gives 0, for example `trimf(75, 0, 0, 75) = 0`. [[fig:trimf]] illustrates the general triangle and both shoulder types."))
    add(FIG("trimf", F["trimf"], "A general triangle and the two degenerate shoulder forms, evaluated with `trimf()`.", 6.2))
    add(H2("The rule base"))
    add(P("The rule base contains 18 rules, one for each combination of 3 attendance terms, 3 credit terms and 2 temptation terms. "
          "[[tab:rulematrix]] shows the consequent for low / high temptation; the complete list is given in Appendix A. The table was "
          "checked against the `RULES` list in the code when this report was generated."))
    add(TAB("rulematrix", "Rule base summary: consequent for low temptation / high temptation.",
            ["Attendance", "Fragile (low / high)", "Moderate (low / high)", "Heavy (low / high)"], ctx["rule_matrix"],
            [2.0, 3.0, 3.0, 3.0], align=["l", "c", "c", "c"], size=9.5))
    add(P("The pattern is easy to read. In the danger zone almost everything forces “attend”; the only exception is a moderate-credit "
          "subject with high temptation, which gives “maybe”. In the “ok” zone the rule base allows “bunk” only for moderate credits with high "
          "temptation, and otherwise asks for caution or attendance. In the safe zone the consequent is never “attend”, and "
          "“bunk” is returned for high temptation in moderate and heavy subjects, where the attendance buffer is large enough to absorb a missed class."))
    add(H2("Manually defined, not learned"))
    add(P("It is important to be clear about the provenance of these definitions. Every membership function and every rule was "
          "written by hand from common-sense reasoning about attendance. They were not estimated from a dataset, tuned by an optimiser "
          "or reviewed by a domain expert, and there was no training phase. The behaviour of BunkWise is therefore only as sound as these "
          "manual choices, which is discussed further in Chapter 12."))
    add(P("One structural property was checked by a test: over a grid of 41 × 13 × 21 valid inputs, at least one rule always fires "
          "and the aggregate always has positive area. This holds because the input sets cover their entire universes, and it is "
          "why the zero-area fallback of Chapter 7 is unreachable for validated inputs. The test supports this on the grid; it is not a "
          "formal proof for every real-valued input."))

    # ================================================================ 7 ALGORITHM
    add(H1("Mamdani Inference Algorithm"))
    add(H2("Processing pipeline"))
    add(P("[[tab:pipeline]] summarises the ten stages of the pipeline and the functions that implement them in `bunk_meter.py`."))
    add(TAB("pipeline", "Processing pipeline and implementing functions.", ["#", "Stage", "Implementation", "Result"], [
        ["1", "Input validation", "`validate_inputs()`", "Raises ValueError or accepts"],
        ["2", "Fuzzification", "`trimf()` over `INPUTS`", "8 membership degrees"],
        ["3", "Rule evaluation", "loop over `RULES` in `infer()`", "18 candidate strengths"],
        ["4", "Firing strength = min", "`min(...)` of three degrees", "fired rules (s > 0)"],
        ["5", "Clipping", "`np.minimum(s, shape)`", "clipped output sets"],
        ["6", "Aggregation = max", "`np.maximum(agg, ...)`", "aggregate on 401 points"],
        ["7", "Centroid defuzzification", "`defuzzify()`", "raw Bunk Score S"],
        ["8", "Raw fuzzy verdict", "`verdict()`", "text and colour (35 / 65)"],
        ["9", "Attendance-policy override", "`final_recommendation()`", "final text and colour"],
        ["10", "Presentation", "`app.py`", "score, card, warning, explanations"],
    ], [0.7, 4.0, 4.4, 4.0], align=["c", "l", "l", "l"], size=9))
    add(H2("Input validation"))
    add(P("`validate_inputs(values)` loops over the three input definitions. For each it raises `ValueError` if the key is missing, "
          "if the value is a boolean or not a real number (`int`, `float` or NumPy scalar), if it is not finite, or if it is outside "
          "its range. The finiteness check is essential because NaN would otherwise pass through `trimf()`: every comparison with NaN "
          "is false, so the NaN would not be caught by the range tests and would end in an invalid result (NaN or a division error). Booleans are rejected explicitly "
          "because `True` is an `int` in Python and would otherwise be accepted as 1."))
    add(H2("Fuzzification, rule evaluation and aggregation"))
    add(P("`infer(values)` first validates, then builds a dictionary `fuzzy[input][set]` of membership degrees with `trimf()`. It "
          "then iterates over `RULES`; for each rule it computes the minimum of the three antecedent degrees. Rules with strength "
          "zero are discarded, and each remaining rule is appended to the list `fired` as `(strength, attendance, credits, "
          "temptation, output)`. A dictionary `out_strength` keeps, for every output set, the largest strength among the rules that "
          "point to it."))
    add(P("The implementation clips and then aggregates once per output set rather than once per rule. This is equivalent to "
          "clipping every rule separately and taking the maximum of all of them, because min distributes over max:"))
    add(EQ("equiv", r"\max_{k}\ \min\left\{\alpha_k,\ \mu_{O_k}(y)\right\}=\max_{o}\ \min\left\{\beta_o,\ \mu_{o}(y)\right\},\qquad \beta_o=\max_{k:\ O_k=o}\alpha_k"))
    add(P("Here o ranges over the three output sets. The output universe is `np.linspace(0, 100, 401)`, and the aggregate is "
          "`np.maximum(agg, np.minimum(s, shape))` accumulated over the output sets."))
    add(H2("Centroid defuzzification and the zero-area fallback"))
    add(P("`defuzzify(xs, agg)` computes `(xs * agg).sum() / agg.sum()`, which is [[eq:centroid_d]]. If the aggregate has zero area "
          "(`agg.sum() == 0`), the centroid is undefined and the function returns the neutral midpoint 50.0. This case cannot arise for "
          "validated inputs, because the input sets cover their universes and therefore at least one rule always fires; the fallback "
          "is a defensive measure that is covered by its own unit test."))
    add(H2("Raw verdict and attendance-policy override"))
    add(P("`verdict(score)` returns the raw fuzzy verdict and a colour: “CANNOT SKIP THE CLASS!!” for scores below 35, “PROCEED WITH "
          "CAUTION” from 35 up to but excluding 65, and “CAN SKIP THE CLASS” from 65. It deliberately ignores attendance. "
          "`final_recommendation(score, attendance)` then applies the policy. It first checks that the score is a finite number between "
          "0 and 100 and that attendance is valid, then returns “ATTEND CLASS — BELOW MINIMUM ATTENDANCE” if "
          "`below_attendance_minimum(attendance)` is true (attendance < 75), and otherwise returns `verdict(score)`. The "
          "raw score is never modified."))
    add(P("The policy is kept outside the fuzzy system on purpose. The 75% requirement is a crisp rule, not a vague concept, so it is "
          "modelled as a hard constraint. Applying it after defuzzification leaves the membership functions and the 18 rules untouched "
          "and makes the override visible and independently testable. The final recommendation is thus a function of two quantities, the "
          "raw score and the attendance, as in the definition of R in Chapter 3."))
    add(H2("Pseudocode"))
    add(CODE("""function BUNK_SCORE(attendance, credits, temptation):
    VALIDATE all three inputs        # present, finite, in range, not boolean
    for each input variable and each of its fuzzy sets (a, b, c):
        degree[variable][set] = TRIMF(value, a, b, c)
    for each output set o: strength[o] = 0
    for each rule (A, C, T, o) in RULES:    # 18 rules
        s = MIN(degree[att][A], degree[cred][C], degree[temp][T])
        if s > 0: record rule as fired; strength[o] = MAX(strength[o], s)
    y = 401 points from 0 to 100 (step 0.25);  agg = 0 at every point
    for each output set o with parameters (a, b, c):
        agg = MAX(agg, MIN(strength[o], TRIMF(y, a, b, c)))   # clip, aggregate
    if SUM(agg) > 0: score = SUM(y * agg) / SUM(agg)      # centroid
    else:            score = 50                           # neutral fallback
    return score

function FINAL_RECOMMENDATION(score, attendance):
    CHECK score is finite and 0 <= score <= 100;  CHECK attendance is valid
    if attendance < 75: return "ATTEND CLASS - BELOW MINIMUM ATTENDANCE"
    if score < 35:      return "CANNOT SKIP THE CLASS!!"
    if score < 65:      return "PROCEED WITH CAUTION"
    return "CAN SKIP THE CLASS"
"""))

    # ================================================================ 8 WORKED EXAMPLES
    add(H1("Worked Numerical Example"))
    add(P("All numbers in this chapter were produced by running `infer()` and `final_recommendation()` when the report was generated. "
          "Two examples are used: the example from the presentation (attendance 78%, credits 2.5, temptation 8) and a scenario "
          "below the mandatory minimum (attendance 72%, credits 2.5, temptation 9)."))
    add(H2("Example 1: attendance 78%, credits 2.5, temptation 8"))
    add(H3("Fuzzification"))
    add(TAB("ex1fuzz", "Fuzzification of the inputs for Example 1.", ["Input", "Value", "Fuzzy set", "Calculation with trimf()", "Membership"], [
        ["Attendance", "78", "danger (0, 0, 75)", "78 > c = 75, outside support", f"{mu['attendance']['danger']:.3f}"],
        ["", "", "ok (70, 78, 85)", "x = b = 78", f"{mu['attendance']['ok']:.3f}"],
        ["", "", "safe (80, 100, 100)", "78 < a = 80, outside support", f"{mu['attendance']['safe']:.3f}"],
        ["Credits", "2.5", "fragile (1, 1, 2.5)", "x = c = 2.5, (c − x)/(c − b) = 0", f"{mu['credits']['fragile']:.3f}"],
        ["", "", "moderate (1.5, 2.5, 3.5)", "x = b = 2.5", f"{mu['credits']['moderate']:.3f}"],
        ["", "", "heavy (2.5, 4, 4)", "x = a = 2.5, (x − a)/(b − a) = 0", f"{mu['credits']['heavy']:.3f}"],
        ["Temptation", "8", "low (0, 0, 6)", "8 > c = 6, outside support", f"{mu['temptation']['low']:.3f}"],
        ["", "", "high (4, 10, 10)", "(8 − 4)/(10 − 4) = 2/3", f"{mu['temptation']['high']:.3f}"],
    ], [2.0, 1.1, 3.4, 4.6, 1.8], align=["l", "c", "l", "l", "c"], size=9))
    add(P("As [[tab:ex1fuzz]] shows, attendance belongs to “ok” with membership 1, credits belong to “moderate” with membership 1, and temptation belongs to "
          "“high” with membership (8 − 4)/(10 − 4) ≈ 0.667 (and to “low” with 0). [[fig:wfuzz]] plots these degrees."))
    add(FIG("wfuzz", F["wfuzz"], "Fuzzification of attendance 78, credits 2.5 and temptation 8. Dashed lines mark the input values; dots mark the non-zero degrees.", 6.2))
    add(H3("Rule firing"))
    add(P("Only one of the 18 rules has a non-zero strength, because for every other rule at least one antecedent degree is zero. "
          "The active rule is:"))
    add(P("**IF** attendance is *ok* **AND** credits are *moderate* **AND** temptation is *high* **THEN** *bunk*."))
    add(EQ("ex1alpha", r"\alpha=\min\{\mu_{\mathrm{ok}}(78),\ \mu_{\mathrm{moderate}}(2.5),\ \mu_{\mathrm{high}}(8)\}=\min\{1,\ 1,\ 0.667\}=0.667"))
    add(P(f"The strengths of the “attend” and “maybe” sets are 0, and that of “bunk” is {e1['out_strength']['bunk']:.3f}."))
    add(H3("Clipping, aggregation and centroid"))
    add(P("Because only “bunk” has a non-zero strength, the aggregate equals the clipped “bunk” set. The “bunk” triangle is "
          "(55, 100, 100), so it rises as (y − 55)/45. It reaches the clip level 2/3 at y = 55 + 45 × 2/3 = 85, after which the clipped "
          "set stays flat at 2/3 up to y = 100:"))
    add(CASES("ex1clip", r"\hat{\mu}_{\mathrm{bunk}}(y)", [(r"0", r"y<55"), (r"\frac{y-55}{45}", r"55\leq y\leq 85"), (r"\frac{2}{3}", r"85<y\leq 100")]))
    add(P("The aggregate is therefore a trapezoid, drawn in [[fig:wagg]]. Its exact (continuous) centroid can be found by splitting it into "
          "a triangle (area A_{1} = ½ × 30 × 2/3 = 10, centroid at y_{1} = (55 + 85 + 85)/3 = 75) and a rectangle (area A_{2} = 15 × 2/3 = 10, "
          "centroid at y_{2} = 92.5):"))
    add(EQ("ex1exact", r"y^{*}=\frac{A_1\,y_1+A_2\,y_2}{A_1+A_2}=\frac{10\times 75+10\times 92.5}{10+10}=83.75"))
    add(FIG("wagg", F["wagg"], "Clipped “bunk” set, aggregate and centroid for Example 1. The solid line is the grid centroid computed by the implementation; the dashed line is the exact continuous value.", 5.8))
    add(P(f"The implementation does not integrate analytically; it applies [[eq:centroid_d]] on the 401-point grid. Running `infer()` gives "
          f"Σ(y·μ) = {e1['sum_xmu']:.3f} and Σμ = {e1['sum_mu']:.3f}, hence"))
    add(EQ("ex1grid", rf"y^{{*}}=\frac{{{e1['sum_xmu']:.3f}}}{{{e1['sum_mu']:.3f}}}={sc1:.4f}\approx {sc1:.2f}"))
    add(P(f"**The authoritative score is the implementation’s {sc1:.2f}.** The presentation gives the hand calculation as “about 83.7”; "
          f"the exact value of that calculation is {e1['exact']:.2f}, and the slide figure is that value truncated. The grid result "
          f"{sc1:.2f} differs from {e1['exact']:.2f} by {sc1 - e1['exact']:.2f}, so the two are not identical. The difference is a "
          "numerical discretisation effect, not an error in either calculation. [[tab:centroids]] compares three ways of computing the centroid of the same trapezoid."))
    add(TAB("centroids", "Centroid of the Example 1 aggregate by different methods.", ["Method", "Σμ (or area)", "Centroid"], [
        ["Exact, continuous (analytic)", "area = 20 (as Σμ·Δy)", f"{e1['exact']:.4f}"],
        ["Trapezoidal rule on the same 401-point grid", f"{e1['trapz_area']:.4f} (area)", f"{e1['trapz']:.4f}"],
        ["Sum on a 40 001-point grid (step 0.0025)", f"{e1['fine_sum'] * 0.0025:.4f} (as Σμ·Δy)", f"{e1['fine']:.4f}"],
        ["Implementation: sum on 401 points (step 0.25)", f"{e1['sum_mu'] * 0.25:.4f} (as Σμ·Δy)", f"{sc1:.4f}"],
    ], [6.5, 3.6, 2.2], align=["l", "c", "c"], size=9))
    add(P(f"The cause is the plain sum used on a coarse grid. On the 401-point grid the sample at y = 100 is counted with full weight, "
          f"whereas the exact integral (and the trapezoidal rule) gives it half weight. This adds 0.5 × 2/3 = 1/3 to Σμ, which is "
          f"why Σμ = {e1['sum_mu']:.3f} rather than 80 (the exact area 20 divided by the step 0.25), and it pulls the centroid slightly "
          f"to the right. Refining the grid to 40 001 points, or using the trapezoidal rule, returns {e1['exact']:.2f}. The grid sum is "
          "an approximation whose error here is 0.07 of a score point, which does not affect the verdict."))
    add(H3("Verdict"))
    add(P(f"Since {sc1:.2f} ≥ 65, the raw fuzzy verdict is “{e1['raw_text']}”. Attendance (78%) is at least 75%, so the final recommendation "
          f"equals the raw verdict: “{e1['final_text']}”. This is a statement about the fuzzy index only; it does not guarantee that missing a class is safe."))

    add(H2("Example 2: the attendance-policy override (attendance 72%, credits 2.5, temptation 9)"))
    m2 = e2["fuzzy"]
    add(TAB("ex2fuzz", "Fuzzification and rule firing for Example 2.", ["Quantity", "Calculation", "Value"], [
        ["μ_{danger}(72)", "(75 − 72)/(75 − 0)", f"{m2['attendance']['danger']:.3f}"],
        ["μ_{ok}(72)", "(72 − 70)/(78 − 70)", f"{m2['attendance']['ok']:.3f}"],
        ["μ_{safe}(72)", "72 < 80", f"{m2['attendance']['safe']:.3f}"],
        ["μ_{moderate}(2.5)", "x = b", f"{m2['credits']['moderate']:.3f}"],
        ["μ_{high}(9)", "(9 − 4)/(10 − 4)", f"{m2['temptation']['high']:.3f}"],
        ["μ_{low}(9)", "9 > 6", f"{m2['temptation']['low']:.3f}"],
        ["Rule: danger, moderate, high → maybe", f"min({m2['attendance']['danger']:.2f}, 1, {m2['temptation']['high']:.3f})", f"{[s for s, a, c, t, o in e2['fired'] if o == 'maybe'][0]:.3f}"],
        ["Rule: ok, moderate, high → bunk", f"min({m2['attendance']['ok']:.2f}, 1, {m2['temptation']['high']:.3f})", f"{[s for s, a, c, t, o in e2['fired'] if o == 'bunk'][0]:.3f}"],
    ], [5.0, 4.6, 1.8], align=["l", "l", "c"], size=9))
    add(P(f"As [[tab:ex2fuzz]] shows, two rules fire: “maybe” is clipped at {e2['out_strength']['maybe']:.2f} and “bunk” at {e2['out_strength']['bunk']:.2f}. The aggregate "
          f"([[fig:oagg]]) is the maximum of the two clipped shapes, and its centroid is **{sc2:.2f}**. This is in the “can skip” "
          f"range (≥ 65), so the raw fuzzy verdict is “{e2['raw_text']}”."))
    add(FIG("oagg", F["oagg"], "Aggregate and centroid for attendance 72, credits 2.5 and temptation 9.", 5.8))
    add(P(f"However, attendance is 72%, which is below the mandatory 75%. `final_recommendation({sc2:.2f}, 72)` therefore returns "
          f"“{e2['final_text']}”. The raw score {sc2:.2f} is displayed unchanged; only the final recommendation is overridden. This "
          "example shows why the policy step is needed: the “danger” set (0, 0, 75) falls away slowly, so at 72% its membership is "
          f"only {m2['attendance']['danger']:.2f}, while the narrow “ok” set already has membership {m2['attendance']['ok']:.2f}. "
          "The fuzzy rules alone would therefore not reproduce a hard 75% rule."))
    add(H2("What the examples demonstrate"))
    add(P("Example 1 shows a single rule driving the output and the difference between an exact and a numerically approximated centroid. "
          "Example 2 shows two rules firing together, the blending of their clipped consequents, and the separation of the raw "
          "fuzzy score from the policy-aware recommendation."))

    # ================================================================ 9 IMPLEMENTATION
    add(H1("Software Implementation"))
    add(H2("Technologies used"))
    add(TAB("tech", "Technologies and their purpose in the project.", ["Technology", "Version used", "Purpose in BunkWise"], [
        ["Python", v["python"], "Implementation language for the engine, interface and tests."],
        ["NumPy", v["numpy"], "Output universe (`np.linspace`), clipping / aggregation (`np.minimum`, `np.maximum`) and the centroid sums in `bunk_meter.py`."],
        ["Streamlit", v["streamlit"], "Web interface: sliders, buttons, tabs, containers, metrics and tables in `app.py`; `AppTest` for headless interface tests."],
        ["Plotly", v["plotly"], "Interactive charts: score gauge, aggregation plot and membership graphs."],
        ["pandas", v["pandas"], "Data frames for the fuzzification, active-rule and full-rule tables shown by Streamlit."],
        ["Matplotlib", v["matplotlib"], "Optional legacy slider viewer in `bunk_meter.py` (imported lazily, not used by the Streamlit app); also used to draw the diagrams and plots of this report."],
        ["unittest", "standard library", "Automated test suite (algorithm and interface tests)."],
    ], [2.4, 2.4, 7.0], align=["l", "l", "l"], size=9))
    add(P("The runtime requirements are `streamlit>=1.50`, `numpy>=1.26`, `plotly>=5.20` and `pandas>=2.0`; the versions in "
          "[[tab:tech]] are those installed on the machine used to prepare this report. [[cite:python,numpy,streamlit,plotly,pandas,matplotlib]]"))
    add(H2("Code organisation"))
    add(P("`bunk_meter.py` holds the fuzzy engine (about 190 lines excluding the legacy viewer): `trimf`, the `INPUTS`, `OUTPUT_SETS` and "
          "`RULES` data, `validate_inputs`, `defuzzify`, `infer`, `verdict`, `below_attendance_minimum` and `final_recommendation`. `app.py` "
          "is the Streamlit interface. `tests/` contains the unit tests and the interface tests. `.streamlit/config.toml` holds the theme. "
          "The original prototype was a Matplotlib slider program; its fuzzy sets, rules, operators and thresholds were kept, and "
          "input validation, the separate `defuzzify()`, and the policy step were added."))
    add(H2("Application layout"))
    add(P("The page uses a wide layout (maximum content width 1180 px). A header shows the BunkWise wordmark, a badge “Educational "
          "decision-support tool” and the tagline “Skip the guesswork. Know your risk.” Below it, the page is split into a left column "
          "for input and a wider right column for results, followed by a full-width explanation section. [[fig:ui1]] shows the default view."))
    add(FIG("ui1", S["overview"], "BunkWise with the default inputs (78%, 2.5 credits, temptation 8). Left: input sliders and demonstration scenarios. Right: raw score gauge, final recommendation and the “Why this score?” summary. Screenshot of the running application.", 6.1))
    add(H3("Input controls"))
    add(P("Three sliders collect the inputs: attendance (0–100, step 0.5), subject credits (1–4, step 0.5) and temptation to skip "
          "(0–10, step 0.5). Each shows its current value in a badge and has a caption explaining it; the attendance badge turns red below 75%. "
          "Because the sliders enforce the ranges, the engine’s validation is a second line of defence rather than the first."))
    add(H3("Score display, gauge and final recommendation"))
    add(P("The “Raw fuzzy Bunk Score” card shows a Plotly gauge from 0 to 100 with three bands (red below 35, amber from 35 to below 65, "
          "green from 65), the numeric score, and the raw fuzzy verdict “before the attendance rule”. The “Final recommendation” card "
          "shows the policy-aware result with a colour-coded border and icon and a one-line supporting statement. At or above 75% a "
          "caption reminds the user that 75% is a minimum and that BunkWise does not know the classes attended or held."))
    add(H3("Attendance warning"))
    add(P("Below 75%, the final-recommendation card additionally shows a red error banner stating the attendance, the raw score and "
          "raw verdict, and that the mandatory attendance constraint overrides the final recommendation. [[fig:ui5]] shows the override "
          "for attendance 72%."))
    add(FIG("ui5", S["override_final"], "Final recommendation card for attendance 72%, credits 2.5, temptation 9: the raw score is 76.8 (“can skip”) but the mandatory attendance constraint overrides the final recommendation. Screenshot of the running application.", 4.6))
    add(H3("Demo presets"))
    add(P("Five illustrative presets set the three sliders and re-run the same inference. They are labelled in the interface as "
          "illustrative examples, not validated recommendations. [[tab:presets]] lists them with the outputs of the real engine."))
    add(TAB("presets", "Demonstration presets and their engine outputs.", ["Preset", "Att.", "Cr.", "Temp.", "Raw score", "Raw verdict", "Final recommendation"],
            ctx["preset_rows"], [3.6, 1.0, 0.9, 1.0, 1.4, 2.6, 3.0], align=["l", "c", "c", "c", "c", "l", "l"], size=8.5))
    add(H3("Explanation tabs"))
    add(P("The section “How the score was calculated” has five tabs. **Fuzzification** lists, for every input, a table of membership "
          "degrees with progress bars and the (a, b, c) parameters of each set. **Active rules** lists the rules with strength above "
          "zero, strongest first, and offers an expander with all 18 rules. **Aggregation & centroid** shows the clip level "
          "of each output set, the centroid computation and a plot of the unclipped sets, the aggregate and the centroid ([[fig:ui3]]). "
          "**Membership graphs** shows one graph per input with the current value marked and the degree labelled. "
          "**Algorithm** gives a short description of the pipeline and its limits."))
    add(FIG("ui3", S["aggregation"], "“Aggregation & centroid” tab for the default inputs, showing the clip levels, the centroid computation and the aggregate. Screenshot of the running application.", 5.6))
    add(H2("Visual theme"))
    add(P("The interface uses a warm light theme defined in `.streamlit/config.toml`: a cream page background (#faf6ef), a slightly "
          "darker secondary background (#f1ebe0), near-black text (#25232b), an indigo primary colour (#5b4bdb), rounded white cards with a "
          "thin warm border, and red (#c5453e), amber (#c98a1b) and green (#2f8f62) as status colours. Minimal custom CSS styles the cards "
          "by their documented `key` class rather than by Streamlit’s internal class names. This report uses a more restrained shade of the "
          "same indigo as its accent colour."))
    add(H2("Input validation and error handling"))
    add(P("Invalid input is handled at two levels. The sliders constrain values to the legal ranges. If a bad value nevertheless "
          "reaches the engine through corrupted session state, `infer()` raises `ValueError`; `app.py` catches it, shows "
          "“Invalid input: …” with `st.error`, and stops the script with `st.stop()`, so no partial or misleading result is displayed. "
          "`final_recommendation()` likewise rejects a non-finite or out-of-range score and an invalid attendance."))

    # ================================================================ 10 TESTING
    add(H1("Testing and Verification"))
    add(H2("Test environment and commands"))
    add(P(f"The tests were run on {v['os']} with Python {v['python']}, NumPy {v['numpy']}, Streamlit {v['streamlit']}, Plotly {v['plotly']} and "
          f"pandas {v['pandas']}. The suite uses the standard-library `unittest` framework plus Streamlit’s headless `AppTest` and is run with:"))
    add(CODE("python -m unittest discover -s tests -v"))
    add(P(f"When this report was generated, the report generator ran the same test discovery programmatically. The result was: **{tests['total']} tests run, "
          f"{tests['failed']} failures or errors, status {'OK' if not tests['failed'] else 'FAILED'}**, in {tests['seconds']:.1f} s. "
          f"The suite consists of {tests['algo']} algorithm tests (`tests/test_bunk_meter.py`) and {tests['ui']} interface tests "
          "(`tests/test_app.py`). Streamlit prints “missing ScriptRunContext” warnings during the interface tests; these are expected "
          "when a script is run in bare mode by `AppTest` and are not failures."))
    add(H2("Test areas and results"))
    add(P("[[tab:tests]] groups the tests by area and records the result of the run described above."))
    add(TAB("tests", "Automated tests by area, with expected behaviour and actual result.", ["Test area", "Objective", "Expected behaviour", "Actual result"],
            ctx["test_rows"], [2.4, 4.2, 4.2, 1.5], align=["l", "l", "l", "c"], size=8.5))
    add(H2("Algorithm tests"))
    add(P("The algorithm tests exercise `bunk_meter.py` directly. Several compare the engine against an independent recomputation, "
          "for example the aggregate against a freshly built maximum of clipped sets, the score against `(xs * agg).sum() / agg.sum()`, "
          "and the firing strength of the default example against `min(1, 1, 2/3)`. The boundary tests include both degenerate "
          "shoulders, and the validation tests include NaN, infinity, strings, booleans, missing keys and out-of-range values. Two "
          "grid tests sweep the valid input space to confirm that scores are finite and within 0–100 and that some rule always fires."))
    add(H2("Interface tests"))
    add(P("The interface tests load `app.py` with `AppTest`, change sliders, click every preset and compare the rendered score, "
          "raw verdict and final recommendation with `bunk_meter.infer()`, `verdict()` and `final_recommendation()`. They check that the "
          "error banner appears if and only if attendance is below 75, that the override preset still displays the unchanged raw score, "
          "that attendance of 75, 80 and 95 follow the fuzzy verdict, that no Streamlit warning appears on load, and that the "
          "active-rule table equals the rules fired by the engine."))
    add(H2("Browser captures"))
    add(P("The application screenshots in Chapter 9 were captured from a running instance of the unmodified application with an "
          "automated headless Microsoft Edge session driven by Playwright [[cite:playwright]]; the script is "
          "`docs/capture_screenshots.py`. The captured images were inspected visually when the report was prepared. This is not a "
          "manual usability test: no formal manual test protocol, cross-browser testing or user study was carried out."))
    add(NOTE("What the tests do and do not show.",
             "Passing software tests show that the implementation behaves as specified and that the interface agrees with the engine. "
             "They do not show that the rule base makes academically optimal or realistic decisions. No accuracy figure, user survey "
             "or experimental validation exists for BunkWise, and none is claimed."))

    # ================================================================ 11 RESULTS
    add(H1("Results and Discussion"))
    add(H2("Interactive behaviour"))
    add(P("The three sliders update every output immediately. The user can therefore explore how the raw Bunk Score changes with "
          "each input, and the explanation tabs show why: which sets are active, which rules fire, and how the clipped consequents "
          "combine. The raw fuzzy verdict and the final recommendation are shown side by side, which makes the contribution of the "
          "attendance policy explicit."))
    add(H2("Tested scenarios"))
    add(P("[[tab:scen]] lists scenarios evaluated by running the real code: the five presets, the two worked examples, the exact "
          "boundary at 75% and a point just below it, and a high-attendance, high-temptation case. The raw verdicts and final "
          "recommendations are abbreviated (CANNOT SKIP = “CANNOT SKIP THE CLASS!!”, CAUTION = “PROCEED WITH CAUTION”, CAN SKIP = “CAN SKIP THE "
          "CLASS”, ATTEND (below 75%) = “ATTEND CLASS — BELOW MINIMUM ATTENDANCE”)."))
    add(TAB("scen", "Scenarios evaluated with the implementation.", ["Scenario", "Att.", "Cr.", "Temp.", "Rules fired", "Raw score", "Raw verdict", "Final recommendation"],
            ctx["scen_rows"], [3.2, 1.0, 0.9, 1.0, 1.1, 1.3, 2.2, 2.7], align=["l", "c", "c", "c", "c", "c", "l", "l"], size=8.5))
    add(H2("Sensitivity of the raw score"))
    add(P("[[fig:sens]] plots the raw score as one input varies and the others are held fixed. These curves are properties of the "
          "hand-built model, produced by the real code; they are not experimental results."))
    add(FIG("sens", F["sens"], "Raw Bunk Score against attendance (left, credits 2.5) and against temptation (right, attendance 78%). "
            "In the right-hand panel the curves for credits 1 and 4 coincide exactly. Dotted lines mark the thresholds 35 and 65.", 6.2))
    t8 = facts["t8"]
    add(P(f"Several observations follow. First, with credits 2.5 and temptation 8 the raw score is {t8[70]:.1f} at 70% attendance but "
          f"{t8[72]:.1f} at 72% and {t8[75]:.1f} at 75%: the narrow “ok” set (70–85) switches on quickly while the “danger” set has "
          f"a membership of at most {facts['danger70']:.3f} at 70%. Second, the raw score first reaches 65 at an attendance of "
          f"{facts['first65']:g}% (checked in steps of 0.5 for temptations 8, 9 and 10), which is below the 75% minimum. This is the quantitative "
          "reason for the separate policy step. Third, the raw score is not monotonic in attendance in every region: for temptation 8 "
          f"it is {t8[80]:.1f} at 80% but {t8[85]:.1f} at 85%, because at 85% only the “safe” set is active and with a smaller "
          "clip level the clipped “bunk” trapezoid has a lower centroid. A centroid score reflects both which output set is active and how "
          "strongly, so it should be read as an index and not as a linear measure of risk. Fourth, the temptation curves show the "
          "intended behaviour that a stronger wish to skip raises the score, but only when attendance and credits allow it: with credits "
          "1 or 4 at 78% attendance the score never exceeds 50."))
    add(H2("Raw fuzzy verdict versus final recommendation"))
    add(P("The two outputs answer different questions. The raw verdict answers “what do the fuzzy rules say about this combination "
          "of inputs?”; the final recommendation answers “what does the mandatory attendance requirement allow?”. They agree whenever "
          "attendance is at least 75%. They can differ only below 75%, where the final recommendation is always to attend, as in "
          "the presets “Low attendance” (raw score 18.9, which already says “cannot skip”) and “Below 75%, score still high” (raw 76.8, “can skip”)."))
    add(H2("Role of the 75% attendance constraint"))
    add(P("The 75% constraint is applied after defuzzification as a hard rule. At exactly 75% the normal thresholds apply; at 75% or "
          "above the interface displays a caution that 75% is a minimum and not a guarantee, since BunkWise does not know the number "
          "of classes attended or held and therefore cannot say whether missing one more class would drop the real percentage below the limit."))
    # ================================================================ 12 LIMITATIONS
    add(H1("Limitations"))
    for title, body in [
        ("Manually chosen membership functions and rules.",
         "Every parameter of every fuzzy set and every rule consequent was chosen by hand. Different but equally plausible choices would "
         "change the scores, and nothing in the project determines which choice is better."),
        ("No training data and no empirical validation.",
         "No dataset was collected, no model was trained, and BunkWise was never compared with actual student decisions or outcomes. "
         "The test suite verifies the implementation, not the realism of the rules."),
        ("Subjective inputs.",
         "Temptation is self-reported and has no objective scale; two users may rate the same feeling differently. Credits are chosen "
         "from a slider and are only a rough proxy for how important one class is."),
        ("Credits as a proxy for importance.",
         "A one-credit subject is treated as “fragile” and a four-credit subject as “heavy”, but the importance of a class also depends on "
         "its content, the instructor, assessments and the exam schedule, none of which is modelled."),
        ("The score is not a probability.",
         "The Bunk Score is a fuzzy index. It does not estimate the chance of any event, and a value of 80 does not mean an 80% probability "
         "that skipping is safe."),
        ("No knowledge of classes attended or held.",
         "The system sees only an attendance percentage. It cannot compute how many further classes may be missed before the percentage "
         "falls below the limit, because that depends on the number of classes already held and still to come."),
        ("75% is a minimum, not a safety margin.",
         "At 75% or more the recommendation follows the fuzzy verdict, yet an attendance just above 75% may still be one missed class away "
         "from falling below the limit. The interface says so, but the fuzzy rules do not model this distance explicitly."),
        ("Small, fixed rule base and shape of the score.",
         "Eighteen rules over three coarse input variables give a coarse model. Because the score is a centroid, it depends on both the "
         "active output set and its clip level, so it is not monotonic in every input (Chapter 11). The “danger” set falls slowly, "
         "which is why the policy rule had to be added separately. The 75% rule itself was taken from the course handout; no other "
         "institutional policy is modelled."),
    ]:
        add(P(f"**{title}** {body}"))

    # ================================================================ 13 FUTURE SCOPE
    add(H1("Future Scope"))
    add(P("All items in this chapter are **proposed work**. None of them is implemented in the current version of BunkWise."))
    add(BUL("**Expert review.** Ask faculty members or student advisers to review and adjust the membership functions and rules.",
            "**Survey-based tuning and evaluation.** Collect structured responses from students about how they would judge example "
            "situations, compare them with the Bunk Score, and tune the sets and rules accordingly, with appropriate consent.",
            "**Trapezoidal membership functions.** Replace some triangles by trapezoids to obtain plateaus of full membership, for example for a "
            "broad “safe” attendance range.",
            "**Additional contextual inputs.** Add variables such as proximity of examinations, importance of the particular class, or the "
            "number of classes remaining, which would need new sets and a larger rule base.",
            "**Real attendance records.** Integrate the number of classes attended and held, so that the tool can reason about how many "
            "further classes may be missed. This would require privacy protections for personal records.",
            "**ANFIS or hybrid fuzzy-neural approaches.** Once data exist, an adaptive neuro-fuzzy inference system [[cite:jang93]] could learn "
            "membership parameters; this is a research direction, not an existing feature.",
            "**More systematic evaluation.** Gather user feedback and define measurable criteria for the quality of the recommendations."))

    # ================================================================ 14 CONCLUSION
    add(H1("Conclusion"))
    add(P("BunkWise implements a complete Mamdani fuzzy inference system for a small, relatable decision. Three inputs are "
          "fuzzified with triangular membership functions, 18 hand-written rules are evaluated with the minimum operator, the clipped "
          "consequents are merged by maximum aggregation, and the centroid gives a raw Bunk Score between 0 and 100. A separate, "
          "crisp policy step enforces the mandatory 75% attendance requirement without altering that raw score. A Streamlit interface "
          "exposes the whole process, from membership degrees to the aggregated output, and an automated suite of "
          f"{tests['total']} tests, all passing, checks that the engine behaves as specified and that the interface agrees with it."))
    add(P(f"The project demonstrates how fuzzy logic can turn linguistic knowledge into a graded, explainable computation, and how a "
          f"numerical centroid ({sc1:.2f}) relates to its analytic value ({e1['exact']:.2f}) in the worked example. What it does not "
          "demonstrate is that the rules are right: the membership functions and rules are subjective, the score has not been "
          "validated against real decisions, and the tool knows nothing about actual classes attended or held. BunkWise should "
          "therefore be regarded as an educational decision-support tool and a demonstration of soft-computing technique, not as an "
          "authority on attendance decisions."))

    # ================================================================ REFERENCES
    add(H1("References", num=False, page_break=True))
    add(REFS([]))

    # ================================================================ APPENDICES
    add(H1("Complete Rule Base", num="appendix", page_break=True))
    add(P("[[tab:rules]] lists the 18 rules in the order in which they appear in `RULES` in `bunk_meter.py`. The weakest consequent is “attend” and the "
          "strongest is “bunk”."))
    add(TAB("rules", "All 18 rules.", ["#", "Attendance", "Credits", "Temptation", "THEN (Bunk Score is)"],
            [[f"R{i}", a, c, t, o] for i, (a, c, t, o) in enumerate(bm.RULES, 1)], [0.8, 2.4, 2.4, 2.4, 3.2],
            align=["c", "l", "l", "l", "l"], size=9))
    add(H1("Important Parameters", num="appendix"))
    add(P("[[tab:consts]] collects the constants that control the behaviour of the implementation."))
    add(TAB("consts", "Constants used by the implementation.", ["Parameter", "Value", "Where"], [
        ["Mandatory attendance minimum", f"{bm.ATTENDANCE_MIN}%", "`ATTENDANCE_MIN`, `below_attendance_minimum()`"],
        ["Output universe", "0–100, 401 points (step 0.25)", "`np.linspace(0, 100, 401)` in `infer()`"],
        ["Verdict thresholds", "below 35; 35 to below 65; 65 and above", "`verdict()`"],
        ["Zero-area fallback score", "50.0", "`defuzzify()`"],
        ["Input ranges", "attendance 0–100; credits 1–4; temptation 0–10", "`INPUTS`, `validate_inputs()`"],
        ["Default inputs (interface)", "attendance 78, credits 2.5, temptation 8", "`DEFAULTS` in `app.py`"],
        ["Slider steps", "0.5 for all three inputs", "`st.slider` in `app.py`"],
        ["Number of rules", "18 = 3 × 3 × 2", "`RULES`"],
        ["Fuzzy operators", "AND = min; rules sharing a consequent = max; implication = clip; aggregation = max", "`infer()`"],
        ["Defuzzification", "centroid, Σ(y·μ)/Σμ", "`defuzzify()`"],
    ], [3.8, 5.0, 4.2], size=9))
    add(H1("Setup, Run and Test Instructions", num="appendix"))
    add(P("On Windows with PowerShell (from the project README):"))
    add(CODE("""git clone https://github.com/AryanRajguru22/Bunkwise.git
cd Bunkwise
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
streamlit run app.py"""))
    add(P("The application opens in the browser, by default at http://localhost:8501. The optional legacy Matplotlib viewer can be "
          "started with `python bunk_meter.py` (requires Matplotlib). The tests are run with:"))
    add(CODE("""python -m unittest discover -s tests -v        # all 38 tests
python -m unittest tests.test_bunk_meter -v     # 31 algorithm tests
python -m unittest tests.test_app -v            # 7 interface tests"""))
    add(H1("Regenerating This Report", num="appendix"))
    add(P("The report is produced by `docs/generate_final_report.py`, which runs the real `infer()` code and the real test suite, "
          "draws the figures with Matplotlib, writes the Markdown and Word versions from a single content definition "
          "(`docs/final_report_content.py`), and then asks Microsoft Word to update the table of contents and list fields and to export "
          "the PDF. Additional dependencies beyond `requirements.txt` are listed in `requirements-docs.txt` (python-docx, "
          "Matplotlib; Playwright only for the screenshots). Word is needed on the machine for the PDF export. The cover-page "
          "placeholders are set in the `COVER` dictionary at the top of that script. [[cite:pythondocx]]"))
    add(H1("Glossary", num="appendix"))
    add(P("[[tab:glossary]] defines the technical terms used in this report."))
    add(TAB("glossary", "Glossary of technical terms.", ["Term", "Meaning"], [
        ["Aggregation", "Combining the clipped consequents of all rules into one fuzzy set (here by pointwise maximum)."],
        ["Antecedent / consequent", "The IF part and the THEN part of a rule."],
        ["Bunk Score", "BunkWise’s raw output index, 0–100; higher means skipping is more tolerable under the rules. Not a probability."],
        ["Centroid", "Centre of area of a fuzzy set; used here to defuzzify the aggregate."],
        ["Clipping", "Truncating a consequent fuzzy set at the firing strength of its rule (Mamdani min implication)."],
        ["Crisp value", "An ordinary number or a Boolean, as opposed to a degree of membership."],
        ["Defuzzification", "Converting a fuzzy set into a single crisp number."],
        ["Firing strength", "The degree to which a rule’s antecedent is satisfied; here the minimum of three membership degrees."],
        ["Fuzzification", "Converting a crisp input into membership degrees in fuzzy sets."],
        ["Fuzzy inference system", "A system that maps crisp inputs to outputs through fuzzification, rules, aggregation and defuzzification."],
        ["Fuzzy set", "A set in which each element has a degree of membership between 0 and 1."],
        ["Linguistic variable", "A variable whose values are words, each defined by a fuzzy set."],
        ["Mamdani inference", "A fuzzy inference style in which rule consequents are fuzzy sets, combined and then defuzzified."],
        ["Membership function", "A function giving the degree of membership of a value in a fuzzy set."],
        ["Soft computing", "A family of methods (fuzzy logic, neural networks, probabilistic reasoning) tolerant of imprecision and uncertainty."],
        ["t-norm", "A fuzzy AND operator; the minimum is the one used here."],
        ["Triangular membership function", "A membership function defined by start a, peak b and end c."],
    ], [3.6, 9.4], size=9))
    return B
