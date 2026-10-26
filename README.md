# BunkWise

**Skip the guesswork. Know your risk.**

BunkWise is an interactive, fuzzy-logic attendance decision-support tool for college students, built for the
*Artificial Intelligence and Soft Computing* course (CSE3121). You enter your attendance, a subject's credits
and how tempted you are to skip; BunkWise runs a Mamdani fuzzy inference system and shows a **Bunk Score
(0–100)**, a verdict, and a step-by-step explanation of how it got there.

> Educational decision-support tool. The score is a fuzzy index, **not a probability**, and it is not an
> institutional attendance policy. The mandatory 75% attendance threshold is shown as a separate warning.

## Features

- Three sliders (attendance 0–100 %, credits 1–4, temptation 0–10) with live results.
- Bunk Score, verdict, gauge, plain-English explanation built from the real inference.
- Prominent warning whenever attendance is below 75 %, independent of the fuzzy score.
- Explainability tabs: membership degrees per input, active rules with firing strengths, aggregated
  output and centroid, interactive membership graphs, short "how it works" text.
- Five illustrative demo scenarios (they set the sliders and re-run the same inference).

## Tech stack

Python · Streamlit (UI) · NumPy (output universe and centroid) · Plotly (charts) · pandas (tables).
Tests use the standard-library `unittest` (plus Streamlit's `AppTest`).

## Project structure

```
app.py                 Streamlit interface (displays results of bunk_meter.infer)
bunk_meter.py          Fuzzy core: trimf, INPUTS, OUTPUT_SETS, RULES, infer, defuzzify, verdict
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
5. **Verdict** – below 35: `CANNOT SKIP THE CLASS!!`; 35 to below 65: `PROCEED WITH CAUTION`;
   65 or above: `CAN SKIP THE CLASS`.

`validate_inputs()` rejects missing, non-finite or out-of-range inputs. If the aggregate output had zero
area, `defuzzify()` returns 50 (neutral); this cannot happen for valid inputs because the input sets cover
their whole ranges (checked by a test).

## Changes from the original prototype

The original matplotlib program is in the first Git commit. The fuzzy sets, 18 rules, min/max operators,
centroid and verdict thresholds are unchanged. Added: input validation (NaN would otherwise slip through
`trimf`), `defuzzify()` split out for testing, `below_attendance_minimum()`, lazy matplotlib import (the
core no longer needs matplotlib). Cosmetic: one consistent "temptation to skip" wording, rule-zone comments
corrected to match the real set bounds, verdict colours (red = cannot skip, green = can skip).

## Known limitations and assumptions

- Membership functions and rules are hand-written and subjective; nothing is learned from data and the
  system is not empirically validated.
- Credits are only a proxy for a class's importance.
- The attendance set `danger = (0, 0, 75)` falls off slowly, so a student slightly below 75 % can still get
  a high score (see the "Below 75%, score still high" scenario). That is why the 75 % warning is separate.
- The 75 % rule is taken from the course handout; no other college policy is modelled.

## Contributing

Clone the repo, create a branch (`git checkout -b feature/my-change`), run the tests before and after
your change, then open a pull request.
