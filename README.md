# BunkWise

**Skip the guesswork. Know your risk.**

BunkWise is an interactive, fuzzy-logic attendance decision-support tool for college students, built for the
*Artificial Intelligence and Soft Computing* course (CSE3121). You enter your attendance, a subject's credits
and how tempted you are to skip; BunkWise runs a Mamdani fuzzy inference system and shows a **Bunk Score
(0–100)**, a fuzzy verdict, a **final recommendation** that respects the mandatory 75% attendance rule, and a
step-by-step explanation of how it got there.

> Educational decision-support tool. The score is a fuzzy index, **not a probability**, and it is not an
> institutional attendance policy. The mandatory 75% attendance requirement is a hard constraint applied after
> the fuzzy inference; it never changes the raw score.

## Features

- Three sliders (attendance 0–100 %, credits 1–4, temptation 0–10) with live results.
- Raw fuzzy Bunk Score, fuzzy verdict, gauge and a plain-English explanation built from the real inference.
- A separate **final recommendation**: below 75 % attendance it is always `ATTEND CLASS — BELOW MINIMUM ATTENDANCE`,
  with a banner explaining the override; at 75 % or above it follows the fuzzy verdict.
- Explainability tabs: membership degrees per input, active rules with firing strengths, aggregated
  output and centroid, interactive membership graphs, short "how it works" text.
- Five illustrative demo scenarios (they set the sliders and re-run the same inference).

## Tech stack

Python · Streamlit (UI) · NumPy (output universe and centroid) · Plotly (charts) · pandas (tables).
Tests use the standard-library `unittest` (plus Streamlit's `AppTest`).

## Project structure

```
app.py                 Streamlit interface (displays results of bunk_meter.infer)
bunk_meter.py          Fuzzy core: trimf, INPUTS, OUTPUT_SETS, RULES, infer, defuzzify, verdict,
                       final_recommendation (75% policy step)
tests/                 unittest suite (algorithm + UI consistency)
docs/                  Project report and AISC viva guide (PDF, Markdown, generator script)
requirements.txt       Runtime dependencies
requirements-docs.txt  Only needed to regenerate the PDF
.streamlit/config.toml Theme
```

## Setup (Windows, PowerShell)

```powershell
git clone https://github.com/AryanRajguru22/Bunkwise.git
cd Bunkwise
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Run the tests:

```powershell
python -m unittest discover -s tests -v
```

Rebuild the viva guide PDF (optional): `pip install -r requirements-docs.txt` (ReportLab, plus matplotlib for a
fallback font) then `python docs/generate_viva_guide.py`. It writes the PDF and the Markdown together.

## How the inference works

1. **Fuzzification** – triangular membership functions `trimf(x; a, b, c)` give each input a degree in
   every fuzzy set (attendance: danger/ok/safe, credits: fragile/moderate/heavy, temptation: low/high).
2. **Rule evaluation** – 18 IF–THEN rules (3 × 3 × 2). Firing strength = `min` of the three degrees
   (fuzzy AND). Rules with strength 0 do nothing.
3. **Aggregation** – each output set (attend/maybe/bunk) is clipped at its strongest rule; the clipped
   sets are merged with `max`.
4. **Defuzzification** – centroid `Σ(x·μ)/Σμ` over 401 points of the 0–100 output universe.
5. **Raw fuzzy verdict** – below 35: `CANNOT SKIP THE CLASS!!`; 35 to below 65: `PROCEED WITH CAUTION`;
   65 or above: `CAN SKIP THE CLASS`.
6. **Final recommendation (policy step, not fuzzy)** – `final_recommendation(score, attendance)`: if attendance is
   below 75 % the result is `ATTEND CLASS — BELOW MINIMUM ATTENDANCE` whatever the score; otherwise it equals the
   raw fuzzy verdict.

`validate_inputs()` rejects missing, non-finite or out-of-range inputs. If the aggregate output had zero
area, `defuzzify()` returns 50 (neutral); this cannot happen for valid inputs because the input sets cover
their whole ranges (checked by a test).

### Raw fuzzy score vs final recommendation

The raw score and verdict come only from the fuzzy engine and are always shown unchanged. The mandatory 75 %
attendance rule is applied **after** defuzzification as a hard constraint: it is a crisp policy, not a vague
concept, and applying it afterwards keeps the membership functions and the 18 rules untouched while making
the override visible and testable. Example: attendance 72, credits 2.5, temptation 9 → raw score 76.8
(`CAN SKIP THE CLASS`) but final recommendation `ATTEND CLASS — BELOW MINIMUM ATTENDANCE`. At exactly 75 % or
above the normal thresholds apply, but 75 % is only a minimum: BunkWise does not know how many classes you
attended or were held, so it makes no claim about future eligibility. The score is an index, not a
probability, and nothing is trained: it is a hand-built fuzzy system, not a machine-learning model.

## Changes from the original prototype

The original matplotlib program is in the first Git commit. The fuzzy sets, 18 rules, min/max operators,
centroid and verdict thresholds are unchanged. Added: input validation (NaN would otherwise slip through
`trimf`), `defuzzify()` split out for testing, `below_attendance_minimum()`, `final_recommendation()`, lazy
matplotlib import (the core no longer needs matplotlib). Cosmetic: one consistent "temptation to skip" wording, rule-zone comments
corrected to match the real set bounds, verdict colours (red = cannot skip, green = can skip).

## Known limitations and assumptions

- Membership functions and rules are hand-written and subjective; nothing is learned from data and the
  system is not empirically validated.
- Credits are only a proxy for a class's importance.
- The attendance set `danger = (0, 0, 75)` falls off slowly, so a student slightly below 75 % can still get
  a high *raw* score (see the "Below 75%, score still high" scenario). That is why the 75 % rule is applied
  afterwards as a hard constraint in `final_recommendation()` instead of altering the fuzzy algorithm.
- The 75 % rule is taken from the course handout; no other college policy is modelled.

## Contributing

Clone the repo, create a branch (`git checkout -b feature/my-change`), run the tests before and after
your change, then open a pull request.
