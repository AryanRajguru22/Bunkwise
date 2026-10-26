"""Generate the BunkWise project report / AISC viva guide.

Writes BOTH docs/BunkWise_Viva_Guide.md and docs/BunkWise_Project_Report_and_AISC_Viva_Guide.pdf
from the same content, and computes every worked-example number by calling bunk_meter.infer(),
so the guide cannot drift from the code.

    pip install -r requirements-docs.txt
    python docs/generate_viva_guide.py
"""
import os
import re
import sys
from xml.sax.saxutils import escape

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import bunk_meter as bm  # noqa: E402

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, PageBreak,  # noqa: E402
                                PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402

PDF_PATH = os.path.join(HERE, "BunkWise_Project_Report_and_AISC_Viva_Guide.pdf")
MD_PATH = os.path.join(HERE, "BunkWise_Viva_Guide.md")

NAVY, ACCENT, LIGHT = colors.HexColor("#1f2a5a"), colors.HexColor("#6c5ce7"), colors.HexColor("#f1f2fb")

# ------------------------------------------------------------------ fonts
def register_fonts():
    """Arial + Consolas on Windows; DejaVu (ships with matplotlib) elsewhere; Helvetica as last resort."""
    win = r"C:\Windows\Fonts"
    sets = [
        ((os.path.join(win, "arial.ttf"), os.path.join(win, "arialbd.ttf"), os.path.join(win, "ariali.ttf"),
          os.path.join(win, "arialbi.ttf")), (os.path.join(win, "consola.ttf"), os.path.join(win, "consolab.ttf"))),
    ]
    try:
        import matplotlib
        d = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
        sets.append(((os.path.join(d, "DejaVuSans.ttf"), os.path.join(d, "DejaVuSans-Bold.ttf"),
                      os.path.join(d, "DejaVuSans-Oblique.ttf"), os.path.join(d, "DejaVuSans-BoldOblique.ttf")),
                     (os.path.join(d, "DejaVuSansMono.ttf"), os.path.join(d, "DejaVuSansMono-Bold.ttf"))))
    except ImportError:
        pass
    for (r, b, i, bi), (m, mb) in sets:
        if all(os.path.exists(p) for p in (r, b, i, bi, m, mb)):
            for name, path in (("Body", r), ("Body-B", b), ("Body-I", i), ("Body-BI", bi), ("Mono", m), ("Mono-B", mb)):
                pdfmetrics.registerFont(TTFont(name, path))
            pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-B", italic="Body-I", boldItalic="Body-BI")
            pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-B", italic="Mono", boldItalic="Mono-B")
            return
    raise SystemExit("No suitable TrueType fonts found (need Arial/Consolas or matplotlib's DejaVu).")


def register_fallback():
    """DejaVu Sans (ships with matplotlib) covers math symbols that Arial lacks, e.g. the quantifiers."""
    try:
        import matplotlib
        path = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf", "DejaVuSans.ttf")
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("Fallback", path))
            return True
    except ImportError:
        pass
    return False


HAS_FALLBACK = False


def _in_font(ch, font="Body"):
    return ord(ch) in pdfmetrics.getFont(font).face.charToGlyph


def fallback_wrap(markup):
    """Wrap characters missing from the body font in the fallback font instead of printing a blank box."""
    out = []
    for ch in markup:
        if ord(ch) > 127 and not _in_font(ch) and HAS_FALLBACK:
            out.append(f'<font name="Fallback">{ch}</font>')
        else:
            out.append(ch)
    return "".join(out)


# ------------------------------------------------------------------ inline markup
def pdf_inline(text):
    """**bold**, `code`, _{sub}, ^{sup}; everything else is XML-escaped (so <, >, & are safe)."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f'<font name="Mono" size="8.2">{escape(part[1:-1])}</font>')
            continue
        s = escape(part)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s)
        s = re.sub(r"_\{(.+?)\}", r"<sub>\1</sub>", s)
        s = re.sub(r"\^\{(.+?)\}", r"<super>\1</super>", s)
        out.append(s.replace("\n", "<br/>"))
    return fallback_wrap("".join(out))


def md_inline(text):
    text = re.sub(r"_\{(.+?)\}", r"_\1", text)
    return re.sub(r"\^\{(.+?)\}", r"^\1", text)


# ------------------------------------------------------------------ diagrams / plots
FONT_NAME = "Body"


def _box(c, x, y, w, h, text, fill=LIGHT, stroke=NAVY, size=7.6, bold=False):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, 4, fill=1, stroke=1)
    c.setFillColor(colors.black)
    lines = text.split("\n")
    c.setFont("Body-B" if bold else "Body", size)
    top = y + h / 2 + (len(lines) - 1) * (size + 1.5) / 2 - size * 0.3
    for i, ln in enumerate(lines):
        c.drawCentredString(x + w / 2, top - i * (size + 1.5), ln)


def _arrow(c, x1, y1, x2, y2, color=NAVY):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(1)
    c.line(x1, y1, x2, y2)
    ang = np.arctan2(y2 - y1, x2 - x1)
    for s in (+1, -1):
        c.line(x2, y2, x2 - 6 * np.cos(ang - s * 0.4), y2 - 6 * np.sin(ang - s * 0.4))


class ArchDiagram(Flowable):
    """Architecture: user -> app.py -> bunk_meter.infer -> result tuple -> UI parts (+ tests)."""
    W, H = 500, 262

    def wrap(self, aw, ah):
        return self.W, self.H

    def draw(self):
        c = self.canv
        _box(c, 150, 226, 200, 30, "USER\nmoves 3 sliders / clicks a demo scenario", size=7.6, bold=True)
        _box(c, 150, 170, 200, 40, "app.py  (Streamlit)\nslider keys in st.session_state,\npreset buttons use on_click callbacks")
        _box(c, 150, 100, 200, 56, "bunk_meter.infer(values)\nvalidate_inputs  →  fuzzify  →  18 rules (min)\n→ clip + max-aggregate  →  defuzzify()",
             fill=colors.HexColor("#e6e3ff"), bold=False)
        _box(c, 380, 100, 118, 56, "bunk_meter.py data\nINPUTS (fuzzy sets)\nOUTPUT_SETS\nRULES (18)", size=7.2)
        _box(c, 0, 100, 118, 56, "tests/ (29 tests)\nunittest + Streamlit\nAppTest check app\nmatches infer()", size=7.2)
        _box(c, 100, 58, 300, 28, "result tuple: fuzzy, fired, out_strength, xs, agg, score", size=7.6, bold=True)
        outs = ["Score +\nverdict()", "Gauge\n(Plotly)", "75% warning\nbelow_attendance\n_minimum()", "Active-rule\ntable +\nexplanation", "Membership\n& aggregate\ncharts"]
        for i, t in enumerate(outs):
            _box(c, i * 101, 0, 94, 40, t, size=7)
            _arrow(c, 250, 58, i * 101 + 47, 40)
        _arrow(c, 250, 226, 250, 210)
        _arrow(c, 250, 170, 250, 156)
        _arrow(c, 250, 100, 250, 86)
        _arrow(c, 380, 128, 350, 128)
        c.setDash(3, 2)
        _arrow(c, 118, 128, 150, 128, color=ACCENT)
        c.setDash()
        c.setFont("Body", 6.8)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(360, 168, "app.py only displays; no fuzzy maths in it")


class PipeDiagram(Flowable):
    """Inference pipeline flowchart (two rows of four boxes)."""
    W, H = 500, 168

    def wrap(self, aw, ah):
        return self.W, self.H

    def draw(self):
        c = self.canv
        row1 = ["1  Crisp inputs\nattendance, credits,\ntemptation", "validate_inputs()\nfinite, in range\nelse ValueError",
                "2  Fuzzification\ntrimf → degree 0..1\nfor every set", "3  Rule evaluation\nstrength = min(att, cred,\ntemp) for 18 rules"]
        row2 = ["4  Implication\nclip each output set at\nits strongest rule", "5  Aggregation\nmax of clipped sets\n(401-point grid)",
                "6  Defuzzification\ncentroid Σxμ / Σμ\n→ Bunk Score", "7  verdict(score)\n<35 / <65 / ≥65"]
        w, h, gap = 112, 52, 17
        for i, t in enumerate(row1):
            _box(c, i * (w + gap), 108, w, h - 4, t, fill=LIGHT if i != 1 else colors.HexColor("#fff4d6"))
            if i:
                _arrow(c, i * (w + gap) - gap, 134, i * (w + gap), 134)
        for i, t in enumerate(row2):
            _box(c, i * (w + gap), 28, w, h - 4, t, fill=colors.HexColor("#e6e3ff") if i == 3 else LIGHT)
            if i:
                _arrow(c, i * (w + gap) - gap, 54, i * (w + gap), 54)
        c.setStrokeColor(NAVY)
        c.setLineWidth(1)
        c.line(3 * (w + gap) + w / 2, 108, 3 * (w + gap) + w / 2, 94)
        c.line(3 * (w + gap) + w / 2, 94, w / 2, 94)
        _arrow(c, w / 2, 94, w / 2, 76)
        c.setFont("Body", 7)
        c.setFillColor(colors.HexColor("#8a1f1f"))
        c.drawString(0, 10, "Separate check, never merged into the score:  attendance < 75  →  red warning banner "
                            "(below_attendance_minimum)")
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(0, 0, "Steps 2-6 are implemented in infer(); step 6 in defuzzify(); step 7 in verdict().")


class Plot(Flowable):
    """Tiny line plot: series = [(points, color, dashed, fill, label)], vlines = [(x, color, label)]."""

    def __init__(self, series, xmax=100, ymax=1.0, vlines=(), width=480, height=125, xlabel=""):
        super().__init__()
        self.series, self.xmax, self.ymax, self.vlines = series, xmax, ymax, vlines
        self.width, self.height, self.xlabel = width, height, xlabel

    def wrap(self, aw, ah):
        return self.width, self.height + 12

    def draw(self):
        c = self.canv
        x0, y0, pw, ph = 28, 18, self.width - 40, self.height - 14

        def px(x):
            return x0 + x / self.xmax * pw

        def py(y):
            return y0 + y / self.ymax * ph
        c.setStrokeColor(colors.HexColor("#999999"))
        c.setLineWidth(0.6)
        c.line(x0, y0, x0 + pw, y0)
        c.line(x0, y0, x0, y0 + ph)
        c.setFont("Body", 6.5)
        c.setFillColor(colors.HexColor("#555555"))
        for v in (0, 0.5, 1.0):
            if v <= self.ymax:
                c.drawRightString(x0 - 3, py(v) - 2, f"{v:g}")
        step = self.xmax / 5
        for i in range(6):
            c.drawCentredString(px(i * step), y0 - 9, f"{i * step:g}")
        c.drawCentredString(x0 + pw / 2, y0 - 17, self.xlabel)
        for pts, col, dashed, fill, label in self.series:
            if fill:
                p = c.beginPath()
                p.moveTo(px(pts[0][0]), py(0))
                for x, y in pts:
                    p.lineTo(px(x), py(y))
                p.lineTo(px(pts[-1][0]), py(0))
                p.close()
                c.setFillColor(col)
                c.setFillAlpha(0.3)
                c.drawPath(p, fill=1, stroke=0)
                c.setFillAlpha(1)
            c.setStrokeColor(col)
            c.setLineWidth(1.3)
            c.setDash(3, 2) if dashed else c.setDash()
            p = c.beginPath()
            p.moveTo(px(pts[0][0]), py(pts[0][1]))
            for x, y in pts[1:]:
                p.lineTo(px(x), py(y))
            c.drawPath(p, fill=0, stroke=1)
            c.setDash()
        lx = x0 + 6
        for pts, col, dashed, fill, label in self.series:
            if label:
                c.setFillColor(col)
                c.setFont("Body-B", 7)
                c.drawString(lx, y0 + ph + 1, "■ " + label)
                lx += 14 + 4.2 * len(label)
        for x, col, label in self.vlines:
            c.setStrokeColor(col)
            c.setLineWidth(1)
            c.setDash(2, 2)
            c.line(px(x), y0, px(x), y0 + ph)
            c.setDash()
            c.setFillColor(col)
            c.setFont("Body-B", 7)
            c.drawString(px(x) + 2, y0 + ph - 8, label)


def tri_points(abc, lo, hi, n=200):
    xs = np.linspace(lo, hi, n + 1)
    return [(float(x), bm.trimf(float(x), *abc)) for x in xs]


# ------------------------------------------------------------------ computed example data
def trace(att, cred, temp):
    fuzzy, fired, out_strength, xs, agg, score = bm.infer({"attendance": att, "credits": cred, "temptation": temp})
    return dict(inp=(att, cred, temp), fuzzy=fuzzy, fired=sorted(fired, reverse=True), out=out_strength, xs=xs,
                agg=agg, score=score, verdict=bm.verdict(score)[0], warn=bm.below_attendance_minimum(att))


def explain_trimf(x, a, b, c):
    """Human-readable evaluation of trimf for the worked example (mirrors the code branches)."""
    if x < a or x > c:
        return f"x={x:g} outside [{a:g}, {c:g}] → 0"
    if x == b:
        return f"x = b = {b:g} → 1"
    if x < b:
        return f"(x−a)/(b−a) = ({x:g}−{a:g})/({b:g}−{a:g}) = {bm.trimf(x, a, b, c):.3f}"
    return f"(c−x)/(c−b) = ({c:g}−{x:g})/({c:g}−{b:g}) = {bm.trimf(x, a, b, c):.3f}"


def exact_centroid(out_strength):
    """Same clipped-max aggregate on a 100,001-point grid, to show the 401-point grid is a good approximation."""
    xs = np.linspace(0, 100, 100001)
    agg = np.zeros_like(xs)
    for name, s in out_strength.items():
        shape = np.array([bm.trimf(float(x), *bm.OUTPUT_SETS[name]) for x in xs])
        agg = np.maximum(agg, np.minimum(s, shape))
    return float((xs * agg).sum() / agg.sum())


# ------------------------------------------------------------------ content
def build_content():
    B = []
    add = B.append
    ex = trace(78, 2.5, 8)
    exact = exact_centroid(ex["out"])
    extra = [trace(90, 2, 9), trace(90, 4, 2), trace(60, 3, 9), trace(72, 2.5, 9)]

    # ---------------------------------------------------------------- how to use
    add(("toc",))
    add(("h1", "About this guide"))
    add(("p", "This guide explains our project **BunkWise** and prepares both of us for the AISC viva. It is written to be "
              "studied, not skimmed: Sections A–E explain the project and the fuzzy-logic theory, Section F is the "
              "product-specific question bank, Section G covers the rest of the syllabus, and Section H is for last-minute revision."))
    add(("ul", [
        "**Source of the syllabus:** we read the official course handout (Manipal University Jaipur, CSE3121 "
        "*Artificial Intelligence and Soft Computing*, Semester V, July–Nov 2026). Topic names follow its syllabus and lecture plan.",
        "**†** marks explanatory material that is *not* named in the handout (for example Sugeno inference, product t-norm, "
        "SHAP/LIME). It is useful for understanding but is extra knowledge, not an official syllabus item.",
        "**All numbers in Sections C–D** (memberships, firing strengths, scores) were produced by running the real "
        "`bunk_meter.infer()` when this guide was generated by `docs/generate_viva_guide.py`.",
        "**Handout rubric that matters to us:** *Algorithmic Implementation of AI approaches with Viva* carries 10 marks "
        "(implementation 5, viva 5) and lists fuzzy logic as one of the approaches. A minimum of 75 % attendance is required "
        "for the end-semester exam, and the 25 % allowance includes all leaves, medical leave too.",
    ]))

    # ---------------------------------------------------------------- A
    add(("h1", "A. Project overview"))
    add(("h2", "A1. What BunkWise is and the problem it addresses"))
    add(("p", "**BunkWise** — tagline *“Skip the guesswork. Know your risk.”* — is a web application that helps a college student "
              "think about skipping one class. The student sets three sliders; BunkWise runs a Mamdani fuzzy inference "
              "system and shows a **Bunk Score (0–100)**, a verdict, and a full explanation of how the score was produced."))
    add(("p", "The problem: attendance is a limited budget (75 % is mandatory), yet the decision is not a sharp yes/no. "
              "Is 79 % “safe”? Is a 2.5-credit class “important”? How much does temptation matter? These words are vague, the "
              "categories overlap, and several factors interact. Fuzzy logic was designed for exactly this: it lets a value "
              "belong *partly* to several categories and combines human-style rules."))
    add(("p", "**Intended users / use cases:** a student weighing a leave; a classmate seeing *why* a recommendation was made; and us, "
              "demonstrating fuzzification, rule evaluation, aggregation and defuzzification live in the viva. "
              "It is an **educational decision-support tool**, not an institutional attendance policy."))
    add(("h2", "A2. Inputs, output and verdicts"))
    rows = []
    for name, cfg in bm.INPUTS.items():
        lo, hi = cfg["range"]
        sets = "; ".join(f"{s} {abc}" for s, abc in cfg["sets"].items())
        rows.append([name, f"{lo:g} – {hi:g}", sets])
    meaning = {"attendance": "Current attendance in the subject (%). 75 % is the mandatory minimum.",
               "credits": "Proxy for how much one class matters: 1 = fragile (one miss hurts fast), 4 = heavy (lots of syllabus).",
               "temptation": "How strongly the student wants to skip: 0 = none, 10 = very strong."}
    for r, name in zip(rows, bm.INPUTS):
        r.append(meaning[name])
    add(("table", ["Input", "Range", "Fuzzy sets (a, b, c)", "Meaning"], rows, [0.13, 0.1, 0.42, 0.35]))
    add(("p", "**Output:** Bunk Score in [0, 100] built from three output sets "
              f"{', '.join(f'{k} {v}' for k, v in bm.OUTPUT_SETS.items())}. Higher = skipping is more tolerable. "
              "It is a fuzzy index, **not a probability**."))
    add(("table", ["Bunk Score", "Verdict (from `verdict()`)", "Colour in app"],
         [["below 35", "CANNOT SKIP THE CLASS!!", "red"], ["35 to below 65", "PROCEED WITH CAUTION", "orange"],
          ["65 or above", "CAN SKIP THE CLASS", "green"]], [0.25, 0.5, 0.25]))
    add(("h2", "A3. Frontend features and why each exists"))
    add(("table", ["Feature", "Purpose"], [
        ["Three sliders (attendance, credits, temptation)", "The only inputs; every change re-runs `infer()` and updates everything."],
        ["Bunk Score, verdict, gauge", "Immediate answer; gauge zones match the 35 / 65 thresholds."],
        ["Red 75 % warning banner", "Attendance policy is a separate constraint; a high score must never hide it."],
        ["Plain-English explanation", "Names the strongest active rule and centroid, built from real results."],
        ["Tab 1 Fuzzification", "Membership degree of the input in every fuzzy set (with (a, b, c))."],
        ["Tab 2 Active rules", "Rules with strength > 0, ranked by firing strength; expander shows all 18 rules."],
        ["Tab 3 Aggregation & centroid", "Clip levels, Σxμ / Σμ, and the aggregated output graph with the centroid line."],
        ["Membership graphs tab", "Input sets with the current value and degrees marked."],
        ["Five demo scenarios", "Set the sliders and call the same `infer()`; labelled illustrative, not recommendations."],
    ], [0.34, 0.66]))
    add(("h2", "A4. Fuzzy decision support versus machine learning; why fuzzy here"))
    add(("table", ["", "BunkWise (fuzzy system)", "Machine-learning model"], [
        ["Knowledge source", "Hand-written membership functions and rules", "Learned from labelled data"],
        ["Training", "None", "Needs a dataset and a training phase"],
        ["Output meaning", "Degree-based index from rules", "Prediction (often a probability) fitted to data"],
        ["Explainability", "Every step visible (memberships, rules, centroid)", "Often a black box"],
        ["Risk", "Subjective choices; not validated", "Data bias, overfitting"],
    ], [0.2, 0.42, 0.38]))
    add(("p", "**Why fuzzy logic:** (1) we have no attendance-outcome dataset, only common-sense rules; (2) the concepts are linguistic and "
              "overlapping; (3) every decision can be explained step by step, ideal for a viva; (4) fuzzy logic is a named syllabus topic "
              "and one of the approaches in the handout's implementation rubric."))
    add(("h2", "A5. Objectives, scope, stack and structure"))
    add(("ul", ["**Objectives:** implement a correct Mamdani FIS; make it interactive and explainable; test it; document it.",
                "**In scope:** three inputs, 18 rules, centroid output, web UI, tests. **Out of scope:** learning from data, database, "
                "login, API server, predicting real exam eligibility."]))
    add(("table", ["Library", "Purpose in BunkWise"], [
        ["Python 3.11", "Language of the fuzzy core and the app."],
        ["NumPy", "Output universe `np.linspace(0, 100, 401)`, element-wise max/min, centroid sums."],
        ["Streamlit", "Turns `app.py` into a web app with sliders, tabs, buttons; re-runs the script on every change."],
        ["Plotly", "Interactive gauge, membership graphs and aggregated-output chart."],
        ["pandas", "Tables for memberships and active rules (with progress bars)."],
        ["unittest + AppTest", "Algorithm tests and headless UI-consistency tests (standard library + Streamlit)."],
        ["ReportLab (docs only)", "Builds this PDF; not needed to run the app."],
    ], [0.22, 0.78]))
    add(("table", ["File", "Role"], [
        ["`bunk_meter.py`", "Fuzzy core: `trimf`, `INPUTS`, `OUTPUT_SETS`, `RULES`, `validate_inputs`, `infer`, `defuzzify`, `verdict`, "
                            "`below_attendance_minimum`; original matplotlib viewer kept at the bottom."],
        ["`app.py`", "Streamlit interface; calls `infer()` once per run and only displays the results."],
        ["`tests/test_bunk_meter.py`, `tests/test_app.py`", "24 algorithm tests and 5 UI-consistency tests (29 total)."],
        ["`requirements.txt`, `.streamlit/config.toml`, `.gitignore`, `README.md`", "Dependencies, dark theme, ignored files, instructions."],
        ["`docs/`", "This guide: PDF, Markdown and the generator script."],
    ], [0.34, 0.66]))
    add(("h2", "A6. Architecture and data flow"))
    add(("diagram", "arch"))
    add(("ol", ["The student moves a slider (or clicks a demo scenario, whose callback writes the slider values into `st.session_state`).",
                "Streamlit re-runs `app.py`; the three values are collected in one dict.",
                "`bunk_meter.infer(values)` validates them and runs the whole Mamdani pipeline.",
                "It returns one tuple `(fuzzy, fired, out_strength, xs, agg, score)`.",
                "`app.py` displays *that same tuple* everywhere: score, verdict, gauge, tables, charts. `below_attendance_minimum()` drives the warning."]))
    add(("h2", "A7. Install, run, test, demonstrate"))
    add(("code", "python -m venv .venv\n.venv\\Scripts\\Activate.ps1\npip install -r requirements.txt\n"
                 "streamlit run app.py                          # launch the app\n"
                 "python -m unittest discover -s tests -v       # run all 29 tests\n"
                 "pip install -r requirements-docs.txt ; python docs/generate_viva_guide.py   # rebuild this guide"))
    add(("h2", "A8. Limitations, assumptions, future improvements"))
    add(("ul", ["Membership functions and rules are hand-chosen and subjective; the system is **not empirically validated** and does not learn.",
                "Credits are only a proxy for importance; temptation is self-reported; no timetable, exam dates or class counts are modelled.",
                "Only the 75 % rule from the handout is modelled; no other college policy is assumed.",
                "The slow-falling `danger` set lets a student slightly under 75 % still get a high score; hence the separate warning (Section E).",
                "**Future (still simple):** classes-remaining and buffer calculator; tune sets with real feedback; try product instead of min; "
                "add a Sugeno variant to compare; sensitivity plots; neuro-fuzzy tuning with data †."]))

    # ---------------------------------------------------------------- B
    add(("h1", "B. Our code, explained"))
    add(("p", "This is the *final* code. Compared with the original prototype, the fuzzy sets, 18 rules, min/max operators, "
              "centroid and verdict thresholds are **unchanged**. Added: `validate_inputs()` (NaN would slip through `trimf` because every "
              "comparison with NaN is False), `defuzzify()` (split out so the zero-area fallback can be tested), "
              "`below_attendance_minimum()`, and matplotlib imported lazily so the core does not need it. Cosmetic: one wording for "
              "temptation, zone comments corrected to the real set bounds, verdict colours (red = cannot skip)."))
    add(("pipe",))
    add(("h2", "B1. trimf() — the triangular membership function"))
    add(("code", "def trimf(x, a, b, c):\n    if x < a or x > c:   return 0.0          # outside the triangle\n"
                 "    if x == b:           return 1.0          # the peak (also the flat edge of a shoulder)\n"
                 "    if x < b:            return (x - a) / (b - a)   # rising edge\n"
                 "    return (c - x) / (c - b)                        # falling edge"))
    add(("p", "Each division happens only when x is strictly between a and b (so b−a > 0) or strictly between b and c (so c−b > 0). "
              "That is why the **degenerate triangles** `(0, 0, 75)` and `(80, 100, 100)` need no special case: at the flat edge `x == b` "
              "returns 1 before any division. `(0,0,75)` is a left shoulder (full membership at 0, falling to 0 at 75); `(80,100,100)` is a "
              "right shoulder. No bug was found here; tests prove it."))
    add(("h2", "B2. INPUTS, OUTPUT_SETS, RULES"))
    add(("p", "`INPUTS` is a dict: input name → label, allowed range and a dict of fuzzy sets `{name: (a, b, c)}`. `infer()` loops over it, "
              "so adding a set needs no new code. `OUTPUT_SETS = {attend (0,0,45), maybe (30,50,70), bunk (55,100,100)}` are triangles on the "
              "0–100 score axis. `RULES` is a list of 18 tuples `(attendance set, credits set, temptation set, output set)`, for example "
              "`(\"ok\", \"moderate\", \"high\", \"bunk\")` means *IF attendance is ok AND credits are moderate AND temptation is high THEN bunk*. "
              "3 × 3 × 2 = 18 covers every combination exactly once."))
    add(("h2", "B3. infer() — the four stages"))
    add(("code", "fuzzy = {name: {s: trimf(values[name], *abc) ...}}            # 1 fuzzification\n"
                 "for a, c, t, out in RULES:\n    s = min(fuzzy['attendance'][a], fuzzy['credits'][c], fuzzy['temptation'][t])   # 2 fuzzy AND\n"
                 "    if s > 0: fired.append(...); out_strength[out] = max(out_strength[out], s)\n"
                 "xs = np.linspace(0, 100, 401); agg = np.zeros_like(xs)\n"
                 "for name, s in out_strength.items():                                   # 3 clip + aggregate\n"
                 "    agg = np.maximum(agg, np.minimum(s, shape_of(name)))\n"
                 "score = defuzzify(xs, agg)                                              # 4 centroid"))
    add(("ul", [
        "**Min = fuzzy AND:** a rule is only as true as its weakest condition. That value is the rule's **firing strength**.",
        "**Zero-strength rules** (`s == 0`) do not fire and do not change `out_strength`, so they cannot affect the output.",
        "**Clipping (implication):** each output triangle is cut off at the strongest rule pointing at it, `np.minimum(s, shape)`.",
        "**Max aggregation:** `np.maximum` merges the clipped shapes: the output is as true as its most-supported rule. "
        "Taking max per consequent first, then clipping, equals clipping each rule then taking max, because max_{i} min(s_{i}, f) = min(max_{i} s_{i}, f).",
        "**Centroid:** `defuzzify(xs, agg) = Σ(x·μ) / Σμ` on the 401-point grid (step 0.25). If the area were zero it returns the neutral 50; "
        "for valid inputs this cannot happen because the input sets cover every range (a test sweeps the whole input space).",
        "**Score and verdict:** `verdict(score)` maps to the three texts at the 35 and 65 thresholds; the score is always finite and in [0, 100] (tested).",
    ]))
    add(("h2", "B4. How the frontend, charts, validation and tests use it"))
    add(("ul", [
        "**Sliders** have `key`s (`attendance`, `credits`, `temptation`) in `st.session_state`. Moving one makes Streamlit re-run `app.py`, which calls `infer()` again. "
        "Session state is also what lets a preset button set the sliders (via an `on_click` callback that runs before the sliders are drawn).",
        "**Warning:** `below_attendance_minimum(attendance)` is `attendance < 75`; it never looks at the score. It renders `st.error`.",
        "**Charts and tables** are drawn from `fuzzy`, `fired`, `out_strength`, `xs`, `agg` — no recomputation, no hard-coded values.",
        "**Validation:** `validate_inputs()` raises `ValueError` for missing, non-numeric, NaN/inf or out-of-range values; `app.py` catches it and shows `st.error` "
        "(the sliders already keep values valid, so this guards against bad state). Programming errors are not hidden.",
        "**Tests (29):** `trimf` peaks/edges/degenerate shapes; degrees in [0,1]; validation; rule count and min-strength; "
        "max aggregation recomputed independently; centroid; zero-area fallback; scores finite in [0,100] over a grid; verdict thresholds; "
        "scenarios; and `AppTest` checks that the displayed score, verdict, warning and rule table match `infer()` after slider and preset changes.",
    ]))

    # ---------------------------------------------------------------- C
    add(("h1", "C. Fuzzy logic: theory from first principles"))
    add(("p", "Handout topics: *fuzzy sets, set-theoretic operations, membership functions, union, intersection and complement, fuzzy rules, reasoning and inference*. "
              "Everything else here is marked †."))
    add(("h2", "C1. Fuzzy sets, membership and fuzzification"))
    add(("ul", [
        "**Classical (Boolean) logic:** an element is in a set or not: μ ∈ {0, 1}. “Attendance ≥ 75” is true or false. "
        "**Fuzzy logic** (Zadeh, 1965): membership is a degree μ_{A}(x) ∈ [0, 1], so 74 % can be *partly* “ok” and *partly* “danger”.",
        "**Fuzzy set** A on a universe X: the pairs (x, μ_{A}(x)). **Universe of discourse:** the range of the variable (attendance 0–100; output score 0–100).",
        "**Linguistic variable** = a variable whose values are words (attendance); **linguistic terms** are those words (danger, ok, safe), each a fuzzy set.",
        "**Membership vs probability:** probability measures uncertainty about whether a *crisp* event will occur and must sum to 1 over exclusive outcomes. "
        "Membership measures *how much* something fits a vague concept; there is no randomness and degrees need not sum to 1. "
        "Example: attendance 78 % is “ok” to degree 1.0 and “safe” to 0 — not “100 % likely to be ok”. At 72 % the degrees are danger 0.04 and ok 0.25 (sum 0.29).",
        "**Fuzzification:** turning a crisp number into membership degrees in each set. Our `trimf` does this.",
    ]))
    add(("h2", "C2. Triangular membership function"))
    add(("p", "Parameters: **a** = where membership starts rising (feet), **b** = the peak (μ = 1), **c** = where it returns to 0."))
    add(("eq", "μ(x; a, b, c) =  0  if x < a or x > c;   (x − a)/(b − a)  if a ≤ x < b;   1  if x = b;   (c − x)/(c − b)  if b < x ≤ c"))
    add(("plot", "tri"))
    add(("p", "At the peak μ = 1; at a and c, μ = 0; in between it is linear. If a = b (left shoulder, e.g. `(0,0,75)`) or b = c (right shoulder, "
              "e.g. `(80,100,100)`), one side is vertical, so the formula's denominator would be 0 — the code avoids it because that branch is "
              "never reached (see B1). **Overlapping sets** give a smooth hand-over between categories (no cliff at 75 or 80) and make the output change gradually."))
    add(("plot", "att"))
    add(("h2", "C3. Fuzzy operations"))
    add(("table", ["Operation", "Standard (Zadeh) definition", "Other common choices †"], [
        ["Intersection / AND", "μ_{A∩B}(x) = min(μ_{A}(x), μ_{B}(x))  (**our code**)", "Product μ_{A}·μ_{B}; Łukasiewicz max(0, μ_{A}+μ_{B}−1)"],
        ["Union / OR", "μ_{A∪B}(x) = max(μ_{A}(x), μ_{B}(x))  (used in aggregation)", "Probabilistic sum μ_{A}+μ_{B}−μ_{A}μ_{B}; bounded sum min(1, μ_{A}+μ_{B})"],
        ["Complement / NOT", "μ_{Ā}(x) = 1 − μ_{A}(x)", "Sugeno / Yager complements"],
    ], [0.2, 0.42, 0.38]))
    add(("p", "Min is a **t-norm** (a valid fuzzy AND: commutative, associative, monotone, with 1 as identity) and max is its dual **t-conorm**. "
              "Example: μ_{A}=0.7, μ_{B}=0.4 → AND = 0.4, OR = 0.7, NOT A = 0.3; product AND would give 0.28."))
    add(("h2", "C4. Rules, inference and Mamdani"))
    add(("ul", [
        "**Fuzzy IF–THEN rule:** IF *antecedent* THEN *consequent*, e.g. IF attendance is ok AND credits are moderate AND temptation is high THEN bunk. "
        "A **rule base** is the set of rules; a **fuzzy inference system (FIS)** is fuzzifier + rule base + inference engine + defuzzifier.",
        "**Firing strength** = degree to which the antecedent is true = min of the antecedent degrees. **Implication:** the consequent is limited by that strength "
        "— Mamdani *clips* the output set at the strength (min); Larsen *scales* it (product †).",
        "**Aggregation:** combine all clipped consequents into one fuzzy set, using max.",
        "**Mamdani inference:** fuzzify → evaluate antecedents (AND = min) → clip consequents → aggregate (max) → defuzzify. Output sets are fuzzy sets, so the system is intuitive. **This is what BunkWise implements.**",
        "**Sugeno (Takagi–Sugeno) †:** the consequent is a crisp constant or linear function, z_{i} = p·x + q·y + r; the output is the weighted average z = Σ w_{i}z_{i} / Σ w_{i}, "
        "with w_{i} the firing strengths. No output sets and no integral, so it is faster and suits tuning, but is less linguistic.",
    ]))
    add(("table", ["", "Mamdani", "Sugeno †"], [
        ["Consequent", "Fuzzy set (e.g. bunk)", "Constant or linear function of inputs"],
        ["Aggregation", "Max of clipped sets", "Not needed; weighted average"],
        ["Defuzzification", "Centroid etc. over a curve", "Weighted average (already crisp)"],
        ["Strength", "Intuitive, human-readable", "Efficient, good for optimisation/neuro-fuzzy"],
    ], [0.2, 0.4, 0.4]))
    add(("h2", "C5. Defuzzification, the centroid, and the sampling grid"))
    add(("p", "**Defuzzification** converts the aggregated fuzzy set back to one crisp number. **Centroid (centre of area)** returns the x-coordinate of the "
              "balance point of the aggregated shape:"))
    add(("eq", "z* = ∫ z·μ(z) dz / ∫ μ(z) dz   ≈   Σ x_{k}·μ(x_{k}) / Σ μ(x_{k})   (our discrete version)"))
    add(("p", "We use it because it uses the *whole* shape: every active rule pulls the answer a little, so the score moves smoothly when an input moves (a "
              "mean-of-maxima or max-membership method would jump). The integral is replaced by a sum over a **numerical grid** `np.linspace(0, 100, 401)` (step 0.25): "
              "a computer cannot integrate a function symbolically, but a fine grid gives an error far below any displayed digit. "
              "Other methods †: bisector, mean/smallest/largest of maxima."))
    add(("h2", "C6. Strengths, limitations, applications, link to ML"))
    add(("ul", [
        "**Advantages:** handles vague/linguistic knowledge, transparent rules, no training data, smooth output, cheap to compute.",
        "**Limitations:** rules and membership shapes are subjective; many inputs cause **rule explosion** (BunkWise: 3·3·2 = 18; four 3-set inputs = 81); "
        "no learning; results depend on the choice of operators and defuzzifier.",
        "**Applications †:** washing machines, air-conditioners, anti-lock brakes, camera autofocus, train control, medical decision support, credit scoring.",
        "**With machine learning †:** *neuro-fuzzy* systems (e.g. ANFIS) use a neural network or gradient descent to tune membership parameters from data; "
        "genetic algorithms can also tune rules and sets."]))

    # ---------------------------------------------------------------- D
    add(("h1", "D. A complete numerical example"))
    a_, c_, t_ = ex["inp"]
    add(("p", f"Input: attendance = **{a_} %**, credits = **{c_}**, temptation = **{t_}**. All values below come from `infer()`."))
    add(("h2", "D1. Fuzzification (step 2)"))
    rows = []
    for name, cfg in bm.INPUTS.items():
        x = ex["inp"][list(bm.INPUTS).index(name)]
        for s, abc in cfg["sets"].items():
            rows.append([name, s, str(abc), explain_trimf(x, *abc), f"{ex['fuzzy'][name][s]:.3f}"])
    add(("table", ["Input", "Set", "(a, b, c)", "Evaluation of trimf", "μ"], rows, [0.13, 0.12, 0.17, 0.5, 0.08]))
    add(("h2", "D2. Rule evaluation (step 3)"))
    fr = ex["fired"]
    add(("p", f"Only **{len(fr)}** of the 18 rules has all three antecedent degrees above zero; every other rule contains at least one set with μ = 0, so "
              f"min = 0 and it does not fire."))
    add(("table", ["Rule", "Antecedents (attendance, credits, temptation)", "min(...)", "Strength", "Consequent"],
         [[str(bm.RULES.index((a, c, t, o)) + 1), f"{a} ({ex['fuzzy']['attendance'][a]:.3f}), {c} ({ex['fuzzy']['credits'][c]:.3f}), {t} ({ex['fuzzy']['temptation'][t]:.3f})",
           f"min({ex['fuzzy']['attendance'][a]:.3f}, {ex['fuzzy']['credits'][c]:.3f}, {ex['fuzzy']['temptation'][t]:.3f})", f"{s:.3f}", o]
          for s, a, c, t, o in fr], [0.07, 0.4, 0.28, 0.12, 0.13]))
    add(("h2", "D3. Implication, aggregation and centroid (steps 4–6)"))
    st = ex["out"]["bunk"]
    add(("p", f"The consequent **bunk** `(55, 100, 100)` is clipped at {st:.3f}: its rising edge μ = (x − 55)/45 reaches {st:.3f} at x = 55 + 45·{st:.3f} = {55 + 45 * st:.2f}, "
              f"so the aggregate is a ramp from 55 to {55 + 45 * st:.0f} and a flat top of {st:.3f} up to 100. The 'attend' and 'maybe' clip levels are "
              f"{ex['out']['attend']:.0f} and {ex['out']['maybe']:.0f}, so they contribute nothing (max with 0)."))
    add(("plot", "agg"))
    num, den = float((ex["xs"] * ex["agg"]).sum()), float(ex["agg"].sum())
    add(("eq", f"Score = Σ x·μ / Σ μ = {num:.2f} / {den:.2f} = {ex['score']:.2f}"))
    add(("p", f"**Numerical approximation:** the exact (analytic) centroid of this trapezoid is 83.75 (ramp area 10 centred at 75, rectangle area 10 centred at 92.5: "
              f"(10·75 + 10·92.5)/20). A 100,001-point grid gives {exact:.2f}; our 401-point grid gives {ex['score']:.2f}. The small difference is "
              f"grid discretisation (the end points are counted as full samples), far too small to change any verdict."))
    add(("h2", "D4. Verdict and interpretation (step 7)"))
    add(("p", f"{ex['score']:.2f} ≥ 65 → **{ex['verdict']}**. Attendance {a_} % ≥ 75, so no warning. Interpretation: with 78 % attendance, a 2.5-credit subject and strong "
              f"temptation, the one matching rule (*ok, moderate, high → bunk*) is two-thirds true, which pulls the score into the 'bunk' region. "
              f"It does **not** mean skipping is safe or that the student will be eligible — every absence still lowers attendance."))
    add(("h2", "D5. Four more scenarios"))
    rows = []
    for k, e in enumerate(extra):
        att, cr, tm = e["inp"]
        f = e["fuzzy"]
        mem = (f"att: " + ", ".join(f"{s} {v:.2f}" for s, v in f["attendance"].items() if v > 0) + "\ncred: " +
               ", ".join(f"{s} {v:.2f}" for s, v in f["credits"].items() if v > 0) + "\ntemp: " +
               ", ".join(f"{s} {v:.2f}" for s, v in f["temptation"].items() if v > 0))
        rl = "\n".join(f"{a}/{c}/{t} → {o} ({s:.2f})" for s, a, c, t, o in e["fired"])
        rows.append([f"{'ABCD'[k]}  ({att:g}, {cr:g}, {tm:g})", mem, rl, f"{e['score']:.2f}", e["verdict"] + ("\n+ 75% WARNING" if e["warn"] else "")])
    add(("table", ["Scenario (att, cred, temp)", "Non-zero memberships", "Rules fired (strength)", "Score", "Verdict"], rows, [0.17, 0.25, 0.28, 0.09, 0.21]))
    A, Bs, Cc, D = extra
    add(("ul", [
        f"**A (90, 2, 9) → {A['score']:.1f}:** two rules fire: *safe/moderate/high → bunk* (0.50) and *safe/fragile/high → maybe* (0.33). The merged shape leans towards bunk but "
        f"'maybe' pulls it back, so the score ({A['score']:.1f}) is above 65 but not extreme.",
        f"**B (90, 4, 2) → {Bs['score']:.2f}:** only *safe/heavy/low → maybe* fires. The 'maybe' triangle is symmetric, so any clipped version has its centroid exactly at 50: "
        "**a single active 'maybe' rule always gives 50, whatever its strength.** Heavy subject + low temptation = caution.",
        f"**C (60, 3, 9) → {Cc['score']:.2f}:** `danger` is only 0.20 at 60 % (the set falls slowly from 0 to 75), so both firing rules have strength 0.20 "
        f"(*maybe* and *attend*). The result sits just under the 35 threshold → cannot skip. Small changes could flip the verdict: thresholds are sharp even though the sets are fuzzy.",
        f"**D (72, 2.5, 9) → {D['score']:.2f}:** attendance 72 % is mostly 'ok' (0.25) with a little 'danger' (0.04); *ok/moderate/high → bunk* dominates, giving a high score "
        "**while attendance is below 75 %**. The red warning appears anyway. This is the case that shows why the policy check is separate from the fuzzy score.",
    ]))

    # ---------------------------------------------------------------- E
    add(("h1", "E. Design decisions, correctness and honest limitations"))
    add(("table", ["Question", "Answer"], [
        ["Why do the membership functions overlap?", "Real categories blur. Overlap makes the output change smoothly and lets several rules share the decision. Without overlap the system degenerates into crisp thresholds."],
        ["Why are the rules manual? Why no dataset?", "We have no labelled attendance outcomes; the rules encode common-sense reasoning. Fuzzy systems are knowledge-driven, so nothing is trained and nothing is claimed to be statistically validated."],
        ["Why 18 rules?", "3 attendance sets × 3 credit sets × 2 temptation sets = 18, one rule per combination, so the rule base is complete (tested: 18 distinct combinations)."],
        ["Why can a rule have zero strength?", "Because min(...) = 0 whenever any antecedent set has μ = 0, e.g. attendance 78 % has μ = 0 in 'danger' and 'safe'. Such rules are skipped."],
        ["Why max aggregation? Why not sum?", "Max is the standard Mamdani union: the output is as true as its best-supported rule. Sum could exceed 1 and double-count rules that point to the same set."],
        ["Why is the score not a probability?", "It is a centroid of fuzzy sets, a degree-based index. It has no frequency interpretation and does not predict an outcome."],
        ["Why is credit only a proxy?", "Credits say nothing about the actual teacher, topic, test dates or how many classes remain; it is a rough indicator of importance."],
        ["How subjective are the sets and rules?", "Very. The positions (70/78/85, 75, 80…) and consequents were chosen by judgement. Moving a set or editing a rule changes scores; that is why we call it a demo of method, not a validated model."],
        ["What if the sets or rules change?", "The pipeline is unchanged but outputs shift. Few sets = coarse behaviour; many sets = more rules (rule explosion). The 29 tests would flag unexpected changes."],
        ["Why might the centroid not match intuition for a verdict?", "Two different active rule sets can give the same centroid (e.g. any single 'maybe' → 50), and thresholds 35/65 are sharp cuts of a smooth number (scenario C)."],
        ["How is the zero-area case handled?", "`defuzzify` returns 50 (neutral) if Σμ = 0. It is unreachable for valid inputs because every range is covered by at least one set (tested by sweeping the input space), but is kept as a safe fallback."],
        ["Why show the 75 % rule separately?", "It is a policy constraint from the handout, not a fuzzy concept. A high score (scenario D) must never imply eligibility, so the banner depends only on attendance < 75."],
        ["How could we improve it simply?", "Add a classes-remaining buffer calculator, sensitivity plots, a product-vs-min toggle, a Sugeno variant for comparison, and tune sets using real student feedback."],
    ], [0.3, 0.7]))
    add(("callout", "**Honesty:** BunkWise is not empirically validated, not statistically trained and cannot predict academic outcomes. It demonstrates fuzzy inference on a relatable problem."))

    # ---------------------------------------------------------------- F
    add(("h1", "F. Product viva questions (F1–F20 are the most likely)"))
    F = [
        ("What problem does BunkWise solve?", "It helps a student reason about skipping one class when attendance is a limited budget (75 % mandatory). Instead of a yes/no cut-off it combines attendance, subject credits and temptation with fuzzy rules and explains the result."),
        ("Why did you choose fuzzy logic?", "The inputs are vague and overlapping (“safe”, “heavy”), we have no dataset to train on, and fuzzy rules are human-readable so every decision can be explained. It is also a named topic in our syllabus."),
        ("What are the inputs and output?", "Inputs: attendance 0–100 %, credits 1–4, temptation 0–10. Output: Bunk Score 0–100 with a verdict below 35, 35 to below 65, and 65 or above."),
        ("What is fuzzification?", "Converting a crisp input into membership degrees in each fuzzy set. For attendance 78 %: danger 0, ok 1, safe 0."),
        ("What is a triangular membership function?", "A function defined by (a, b, c): 0 outside [a, c], rising linearly to 1 at b and falling linearly to 0 at c."),
        ("How is `trimf()` implemented? What about degenerate triangles?", "It returns 0 outside [a, c], 1 at x = b, otherwise a linear ratio. The `x == b` check comes before any division, so (0,0,75) and (80,100,100) never divide by zero."),
        ("What is the `INPUTS` dictionary?", "A configuration of each input's label, range and fuzzy sets with their (a, b, c) parameters. `infer()` loops over it, so the code stays generic."),
        ("Why are there 18 rules?", "One rule for every combination of 3 attendance sets × 3 credit sets × 2 temptation sets (3·3·2 = 18), so every situation is covered."),
        ("What does the `min()` operation represent?", "Fuzzy AND: a rule is only as true as its least true condition. It is the minimum t-norm."),
        ("How do you calculate rule firing strength?", "Strength = min(attendance degree, credits degree, temptation degree). Example: min(1.0, 1.0, 0.667) = 0.667 for ok/moderate/high."),
        ("What is Mamdani inference?", "A fuzzy inference style whose rule consequents are fuzzy sets: fuzzify, evaluate rules with min, clip consequents, aggregate with max, defuzzify with centroid."),
        ("How does aggregation work?", "Each output set is clipped at the strength of its strongest rule, and the clipped shapes are merged point by point with `np.maximum` into one curve."),
        ("Why maximum aggregation?", "It is the fuzzy union: the output is as true as its best-supported rule, and it never exceeds 1 or double-counts rules pointing to the same set."),
        ("What is centroid defuzzification?", "The balance point of the aggregated shape: Σ(x·μ)/Σμ. It uses the whole curve, so the score changes smoothly with the inputs."),
        ("Why does the program use `np.linspace()`?", "To sample the 0–100 output universe at 401 evenly spaced points (step 0.25) so the centroid integral can be approximated by a sum."),
        ("What is NumPy used for?", "Building the output grid, element-wise `minimum`/`maximum` for clipping and aggregation, and the centroid sums."),
        ("What is Streamlit and why did we use it?", "A Python library that turns a script into a web app with sliders and tabs. It keeps everything in Python, so the UI calls our algorithm directly with no backend."),
        ("What does Plotly do in the project?", "It draws the interactive gauge, the input membership graphs with the current value marked, and the aggregated-output chart with the centroid line."),
        ("How do the sliders update the output?", "A slider change makes Streamlit re-run `app.py`; the script reads the slider values, calls `infer()`, and redraws every section from the returned results."),
        ("How do you know the displayed score is correct?", "Tests recompute min, max, clipping and the centroid independently; a regression test pins the default case at 83.82, which agrees with the hand-calculated centroid 83.75 up to grid error; and AppTest confirms the UI shows exactly what `infer()` returns."),
        ("How do the tests validate the implementation?", "29 tests cover membership boundaries and degenerate sets, validation, rule strengths, aggregation, centroid, zero-area fallback, score range, verdict thresholds, scenarios and UI/inference consistency."),
        ("What are the limitations?", "Hand-made sets and rules, not validated, no learning, credits only a proxy, and only the 75 % policy modelled."),
        ("How would you improve it with real attendance data?", "Use data to tune membership parameters (neuro-fuzzy or genetic tuning) or compare against a learned model, and validate against actual outcomes. That would be a new, data-driven project."),
        ("What happens when attendance is below 75 %?", "A red banner appears whatever the score. The score is still computed because it answers a different question."),
        ("Is BunkWise a machine-learning model?", "No. Nothing is trained; the membership functions and rules are written by hand. It is a knowledge-based fuzzy system."),
        ("Is the Bunk Score a probability?", "No. It is a centroid of fuzzy sets on a 0–100 scale; a score of 84 does not mean an 84 % chance of anything."),
        ("What happens if the membership functions change?", "The pipeline is the same but memberships, firing strengths and the score change. This is why the choice of sets is a design decision."),
        ("How would you explain the output to a non-technical user?", "“Based on your attendance, how important the subject is and how tempted you are, the rules say skipping is more or less tolerable. Higher means more tolerable, but you must still meet 75 %.”"),
        ("What is the most important function in the code?", "`infer()`: it runs the whole pipeline. Within it, the min/max logic and `defuzzify()` decide the score."),
        ("What was the most challenging part?", "Keeping the UI honest: one inference result feeding every display, presets going through the same path, and keeping the 75 % policy separate from the fuzzy score. (Say your own experience here too.)"),
        ("Why does (78, 2.5, 8) give 83.8 with only one rule firing?", "That rule is ok/moderate/high → bunk at strength 0.667. The clipped 'bunk' shape (ramp 55→85, flat to 100) has its centroid near 83.8."),
        ("Why is the score exactly 50.0 for (90, 4, 2)?", "Only a 'maybe' rule fires. The 'maybe' triangle (30, 50, 70) is symmetric, so any clipped version balances at 50."),
        ("Why can 72 % attendance still give “CAN SKIP”?", "72 % is mostly in 'ok' (0.25) and barely in 'danger' (0.04) because 'danger' falls slowly to 0 at 75. It shows a rule-base weakness, which is why the policy warning is separate."),
        ("What does `validate_inputs()` do and why is it needed?", "It rejects missing, non-numeric, NaN/inf or out-of-range values. NaN would otherwise fall through all comparisons in `trimf` and return NaN."),
        ("What if no rule fires?", "The aggregate would have zero area and `defuzzify` returns the neutral 50. This cannot happen for valid inputs because the input sets cover every range (tested)."),
        ("Why separate the 75 % warning from the score?", "Eligibility is a rule from the handout, not a fuzzy concept. A high score must never hide a policy breach."),
        ("How do demo presets avoid fake results?", "A preset's callback only writes its three values into the slider state. The normal flow then runs `infer()`, so presets use the same code as manual input."),
        ("What changed from the original code?", "Same sets, rules, operators, centroid and thresholds. Added validation, `defuzzify`, `below_attendance_minimum`, lazy matplotlib import, tests and the web UI; cosmetic fixes to labels/comments/colours."),
        ("Why is `danger` only 0.2 at 60 %?", "`danger` is (0, 0, 75): a ramp from 1 at 0 % to 0 at 75 %, so at 60 % it is (75−60)/75 = 0.2. A steeper set would be a design change we deliberately did not make."),
        ("Why are thresholds 35 and 65 not the set boundaries?", "They are verdict cut-offs on the final score, kept from the original design. The output sets overlap; the verdict simply bins the crisp centroid."),
        ("What is `st.session_state` used for here?", "Only to hold the slider values so a preset button can set them. It is the one place the app uses state."),
    ]
    add(("qa", F, 1, "F"))

    # ---------------------------------------------------------------- G
    add(("h1", "G. Rest of the AISC syllabus: map and question bank"))
    add(("p", "Topics below follow the handout's syllabus and lecture plan. The handout's introduction also mentions basic NLP and logic-based agents, "
              "but its lecture plan has no separate NLP lecture, so NLP gets a brief mention only."))
    add(("table", ["Handout block (lectures)", "Topics", "CO"], [
        ["Intelligent agents (2–6)", "AI, agents and environments, rational agent, PEAS, agent vs software program, classes of agents, single/multi-agent, performance evaluation, architecture", "1"],
        ["Problem solving, production systems (7–10)", "Problem definition and characteristics, production system, forward/backward, state space", "1"],
        ["Heuristic search (11–16)", "Blind vs heuristic, generate-and-test, hill climbing, best-first, A*, problem reduction, constraint satisfaction, means-ends analysis", "2"],
        ["Game playing (17–20)", "AO*, minimax, constraint propagation, alpha-beta pruning", "2"],
        ["Knowledge & logic (21–30)", "KR issues, propositional and predicate logic, quantifiers, nested quantifiers, inference rules, resolution", "3"],
        ["Uncertainty & decisions (29–32)", "Bayesian networks, decision theory, sequential decisions, elementary game theory", "3"],
        ["Soft computing (33–38)", "Neuron model, perceptron, back-propagation; fuzzy sets, operations, membership functions, rules, reasoning", "4"],
        ["Evolutionary & emerging (39–48)", "Genetic algorithms, swarm, ant colony; XAI, GANs, transfer/meta-learning, AI for social good; ethics and bias", "5"],
    ], [0.3, 0.6, 0.1]))
    G = []
    # fuzzy comparisons (most important)
    G += [
        ("Classical logic vs fuzzy logic?", "Classical: truth is 0 or 1 and sets have sharp boundaries. Fuzzy: truth/membership is any value in [0, 1], so boundaries are gradual and vague concepts can be modelled."),
        ("Fuzzy logic vs probability?", "Probability = chance of a crisp event (sums to 1 over outcomes). Fuzzy membership = degree of fit to a vague set; no randomness, no sum-to-1 rule."),
        ("Fuzzy systems vs neural networks?", "Fuzzy: human-written rules, interpretable, no training. Neural: learns weights from data, black box. Neuro-fuzzy combines them †."),
        ("Mamdani vs Sugeno?", "Mamdani consequents are fuzzy sets and need defuzzification (centroid); Sugeno consequents are constants/linear functions and the output is a weighted average †."),
        ("Union, intersection, complement of fuzzy sets?", "μ_{A∪B} = max, μ_{A∩B} = min, μ_{Ā} = 1 − μ_{A}. Example μ_{A}=0.6, μ_{B}=0.3 → 0.6, 0.3, 0.4."),
        ("Give a triangular membership calculation.", "For (70, 78, 85) at x = 74: (74−70)/(78−70) = 0.5. At x = 81.5: (85−81.5)/(85−78) = 0.5."),
        ("What is α-cut? †", "The crisp set of elements with μ ≥ α. For α = 0.5 on 'ok' (70,78,85): x ∈ [74, 81.5]."),
        ("Name two defuzzification methods besides centroid. †", "Mean of maxima and bisector (also smallest/largest of maxima). Centroid is the most common but costs most."),
        ("What is a fuzzy relation / fuzzy inference with a compositional rule? †", "A fuzzy relation assigns a degree to pairs; compositional inference (max–min composition) derives the output from input and rule relation. Mamdani's min/max scheme is a practical version."),
        ("When is fuzzy logic a poor choice?", "When abundant data and a precise objective exist (use ML), when rules would explode in number, or when guarantees/validation are essential."),
        ("Name membership-function shapes other than triangular. †", "Trapezoidal (flat top), Gaussian (smooth bell) and sigmoidal (S-shaped). Triangular is simplest: three parameters and easy to explain."),
        ("How do you choose membership functions?", "From expert knowledge and domain meaning, then test; sets should cover the whole universe with overlap. Ours were chosen by judgement, e.g. 'ok' peaks at 78 %, just above the 75 % limit."),
        ("Support and core of a fuzzy set? †", "Support: all x with μ > 0. Core: all x with μ = 1. For 'ok' (70, 78, 85): support (70, 85), core {78}."),
        ("Crisp control vs fuzzy control? †", "A crisp thermostat switches at one threshold; a fuzzy controller blends rules for cool/warm/hot into a smooth output, the same idea as BunkWise's soft zones."),
    ]
    # agents
    G += [
        ("What is AI?", "Building systems that act or think rationally or like humans; in Russell & Norvig's framing, designing rational agents that perceive and act to achieve goals."),
        ("What is an intelligent / rational agent?", "An agent perceives through sensors and acts through actuators; a rational agent picks the action expected to maximise its performance measure given its percepts and knowledge."),
        ("What is PEAS? Give an example.", "Performance measure, Environment, Actuators, Sensors. Taxi: safe/fast trips; roads and traffic; steering, brakes; cameras, GPS."),
        ("Agent vs ordinary software program?", "An agent senses its environment and acts autonomously towards goals over time; an ordinary program just maps given input to output. (BunkWise is a decision-support function, not an autonomous agent.)"),
        ("Types of agents?", "Simple reflex, model-based reflex, goal-based, utility-based, and learning agents; they differ in memory, goals and ability to improve."),
        ("Properties of environments?", "Fully/partially observable, deterministic/stochastic, episodic/sequential, static/dynamic, discrete/continuous, single/multi-agent."),
        ("Goal-based vs utility-based agent?", "A goal-based agent only separates goal from not-goal; a utility-based agent scores how good each state is, so it can trade off conflicting goals and uncertainty."),
        ("How is an agent's performance evaluated?", "By an external performance measure applied to the environment's states over time (e.g. trips completed safely), not by the agent's own opinion; a rational design maximises its expected value."),
    ]
    # search
    G += [
        ("How do you formulate a search problem?", "Initial state, actions, transition model, goal test, and path cost; together they define the state space."),
        ("Blind vs heuristic search?", "Blind (BFS, DFS, uniform-cost) uses no problem knowledge; heuristic search uses h(n), an estimate of cost to the goal, to guide the search."),
        ("BFS vs DFS?", "BFS (queue) is complete and optimal for unit costs but uses O(b^{d}) memory; DFS (stack) uses O(bm) memory but can get stuck deep and is not optimal."),
        ("Forward vs backward search?", "Forward starts at the initial state and applies actions; backward starts at the goal and works back. Pick the direction with the smaller branching factor."),
        ("What is generate-and-test? Hill climbing?", "Generate-and-test creates candidates and tests each. Hill climbing moves to the best neighbour and stops when none is better; it can stall at local maxima, plateaus, ridges."),
        ("Greedy best-first vs A*?", "Greedy uses f(n) = h(n): fast but not optimal. A* uses f(n) = g(n) + h(n): optimal when h is admissible (tree) or consistent (graph)."),
        ("Admissible and consistent heuristics?", "Admissible: h(n) ≤ true cost to goal (never overestimates). Consistent: h(n) ≤ c(n, n′) + h(n′). Consistent implies admissible."),
        ("What is AO* / problem reduction?", "Search over AND–OR graphs: an AND arc needs all sub-problems solved; an OR arc needs one. AO* expands the best partial solution graph and revises costs."),
        ("What is a constraint satisfaction problem?", "Variables with domains and constraints (e.g. map colouring). Solved by backtracking with constraint propagation such as forward checking or arc consistency."),
        ("What is means-ends analysis?", "Repeatedly reduce the difference between the current and goal state by choosing an operator that removes the biggest difference, creating sub-goals as needed."),
        ("What is a production system?", "A set of IF–THEN rules, a working memory (database) and a control strategy that chooses which rule fires."),
        ("Uniform-cost search?", "Expands the node with the lowest path cost g(n); complete and optimal when step costs are positive."),
        ("Heuristics for the 8-puzzle?", "Misplaced tiles and total Manhattan distance; both are admissible and Manhattan dominates (is at least as large), so it expands fewer nodes."),
        ("What is best-first search?", "Always expand the most promising open node according to an evaluation function f(n): greedy uses h(n), A* uses g(n) + h(n)."),
        ("Why does A* want a consistent heuristic?", "With a consistent h, the first time A* expands a state it has already found the cheapest path to it, so a closed list never discards a better path."),
        ("Local maximum, plateau, ridge?", "Local maximum: better than its neighbours but not the best. Plateau: flat region with no uphill direction. Ridge: a narrow slope single moves cannot climb. Remedies: random restarts, simulated annealing †."),
    ]
    # games
    G += [
        ("Explain minimax.", "Two-player zero-sum game tree: MAX picks the child with the highest value, MIN the lowest, values propagate up from leaves scored by an evaluation function."),
        ("What is alpha-beta pruning?", "Minimax that keeps α (best value MAX can already guarantee) and β (best MIN can guarantee) and prunes a branch when α ≥ β."),
        ("Does alpha-beta change the result?", "No. It returns the same minimax value; it only skips branches that cannot influence it. Best case it searches about O(b^{m/2}) nodes."),
        ("Worked example of pruning.", "MAX node, first child value 3 → α = 3. In the second child MIN sees a leaf 2 → β = 2 ≤ α, so the remaining children are pruned: MIN will give at most 2, which MAX will never choose over 3."),
        ("Give an evaluation-function example.", "For chess: weighted material count plus mobility and king safety. It estimates the value of non-terminal positions when the search depth is cut off."),
    ]
    # logic
    G += [
        ("Propositional vs predicate (first-order) logic?", "Propositional logic has atomic true/false statements and connectives. Predicate logic adds objects, predicates, functions and quantifiers (∀, ∃), expressing relations and generalisations."),
        ("Truth table for p → q?", "False only when p is true and q is false. Equivalent to ¬p ∨ q."),
        ("Limitations of propositional logic?", "Cannot express relations or generalise (“all students…”) without one proposition per case; no quantifiers."),
        ("Universal and existential quantifiers? Nested?", "∀x P(x): P holds for all x. ∃x P(x): for some x. Order matters: ∀x ∃y Loves(x, y) (everyone loves someone) ≠ ∃y ∀x Loves(x, y) (someone is loved by all). ¬∀x P ≡ ∃x ¬P."),
        ("State modus ponens and the resolution principle.", "Modus ponens: from p and p → q infer q. Resolution: from (A ∨ B) and (¬B ∨ C) infer (A ∨ C); to prove a goal, add its negation to the knowledge base in CNF and derive the empty clause."),
        ("What is knowledge representation?", "Encoding facts about objects, relations, events, actions, time and space so that a system can reason with them."),
        ("Convert p → q to CNF.", "p → q ≡ ¬p ∨ q, which is already a single clause. In resolution, clauses like this are resolved against the negated goal."),
        ("Write “every student with 75 % attendance is eligible” in first-order logic.", "∀x (Student(x) ∧ Attends75(x) → Eligible(x))."),
        ("Inference rules vs resolution?", "Inference rules (modus ponens, and-elimination) derive conclusions step by step; resolution is a single rule used with refutation, and with unification † it is complete for first-order logic."),
    ]
    # uncertainty
    G += [
        ("What is a Bayesian network?", "A directed acyclic graph whose nodes are random variables and edges are direct influences, each node with a conditional probability table. The joint is Π P(x_{i} | parents(x_{i}))."),
        ("State Bayes' theorem.", "P(A | B) = P(B | A)·P(A) / P(B). Example: P(disease) = 0.01, test sensitivity 0.9, false-positive rate 0.05 → P(disease | +) = 0.009 / (0.009 + 0.0495) ≈ 0.15."),
        ("What is expected utility / decision theory?", "Choose the action with maximum expected utility: EU(a) = Σ P(outcome | a)·U(outcome). It combines probabilities with preferences."),
        ("What is a sequential decision problem?", "Decisions made one after another where each affects later states, modelled for example as a Markov decision process †."),
        ("What is elementary game theory?", "Analysis of decisions where payoffs depend on others' choices. A payoff matrix and Nash equilibrium (no player gains by changing alone) are the basics; prisoner's dilemma is the classic example."),
        ("What does conditional independence give a Bayesian network?", "A node is independent of its non-descendants given its parents, so the joint distribution factorises into small conditional tables."),
    ]
    # NN
    G += [
        ("Artificial neuron model?", "y = f(Σ w_{i}x_{i} + b): weighted sum of inputs plus bias passed through an activation function (step, sigmoid, tanh, ReLU)."),
        ("What is a perceptron? Its limit?", "A single neuron with a step activation, trained by w ← w + η(t − y)x. It only solves linearly separable problems; XOR needs a hidden layer."),
        ("Explain backpropagation.", "Forward pass computes outputs and loss; the backward pass uses the chain rule to get ∂Loss/∂w for every weight; gradient descent updates w ← w − η·∂L/∂w."),
        ("Role of the learning rate and loss function?", "Loss measures error (e.g. mean squared error). The learning rate η scales each update: too large diverges, too small learns slowly."),
        ("Perceptron vs multilayer network?", "The perceptron is one layer and linear in decision boundary; a multilayer network with non-linear hidden units can represent non-linear functions and is trained with backpropagation."),
        ("Neural networks vs fuzzy systems?", "NN learn from data but are opaque; fuzzy systems use explicit rules but do not learn on their own. Biological inspiration: neurons (NN) vs human linguistic reasoning (fuzzy)."),
        ("Supervised learning in one line?", "Learn a mapping from inputs to known target outputs by minimising error on labelled examples."),
        ("Compare sigmoid, tanh and ReLU.", "Sigmoid squashes to (0, 1) and tanh to (−1, 1); both saturate (tiny gradients). ReLU = max(0, z) is cheap and does not saturate for z > 0."),
        ("What is overfitting and how is it reduced?", "The network memorises the training data and generalises badly. Remedies: more data, a validation set with early stopping, regularisation, a simpler model."),
    ]
    # evolutionary
    G += [
        ("Explain a genetic algorithm.", "Keep a population of chromosomes (encoded solutions); score each with a fitness function; select fitter ones, apply crossover and mutation to make the next generation; repeat until termination."),
        ("Selection, crossover, mutation?", "Selection (roulette/tournament) favours fit parents; crossover swaps parts of two chromosomes (e.g. 1101|001 × 0110|110 → 1101110); mutation flips bits with small probability to keep diversity."),
        ("Termination criteria?", "Maximum generations, fitness threshold reached, or no improvement (convergence) for several generations."),
        ("Exploration vs exploitation?", "Exploration searches new regions (mutation, high diversity); exploitation refines good solutions (selection, crossover). GAs must balance both."),
        ("GA vs gradient-based optimisation?", "GA needs no derivatives, handles discrete/non-differentiable problems and is population-based, but is stochastic, slower and gives no optimality guarantee; gradient methods are fast on smooth problems but can stall in local minima."),
        ("Swarm algorithms and ant colony optimisation?", "Swarm methods (e.g. particle swarm †) use many simple agents sharing information. ACO: ants deposit pheromone on good paths, pheromone evaporates, later ants prefer stronger trails; used for routing/TSP."),
        ("Roulette-wheel selection example?", "Fitness 1, 2, 7 → selection probabilities 10 %, 20 %, 70 %: fitter chromosomes are favoured but weak ones keep a chance."),
        ("What is elitism?", "Copying the best individual(s) unchanged into the next generation so the best fitness never decreases."),
    ]
    # emerging
    G += [
        ("What is explainable AI vs interpretable models?", "Interpretable models are understandable by design (rules, decision trees, fuzzy rule bases). XAI also explains opaque models after the fact (e.g. LIME, SHAP †). There is often a trade-off with accuracy; BunkWise sits on the interpretable side."),
        ("What is a GAN?", "Two networks play a minimax game: a generator makes fake data, a discriminator tells real from fake; training makes the fakes increasingly realistic."),
        ("Transfer learning vs meta-learning?", "Transfer learning reuses a model trained on one task for another with little data. Meta-learning is “learning to learn”: training across many tasks so new ones are learned quickly."),
        ("AI for sustainable development and social good?", "Applying AI to goals such as healthcare access, climate, agriculture and education, while weighing environmental cost and fairness."),
        ("Ethical issues in AI?", "Bias from data or design, lack of transparency, privacy, accountability and misuse. Responsible AI means fairness checks, explainability, human oversight and honest claims about limits."),
        ("Give an example of bias in AI and a mitigation.", "A hiring model trained on historically biased decisions repeats them. Mitigation: audit data and outcomes by group, rebalance data, keep human review."),
    ]
    add(("qa", G, 1, "G"))

    # ---------------------------------------------------------------- H
    add(("h1", "H. Rapid revision and oral preparation"))
    add(("h2", "H1. One-page project summary"))
    add(("ul", [
        "**What:** BunkWise, a Streamlit app + Python fuzzy core that scores how tolerable skipping one class is (0–100) and explains why.",
        "**Inputs:** attendance 0–100 (danger/ok/safe), credits 1–4 (fragile/moderate/heavy), temptation 0–10 (low/high). **Output sets:** attend, maybe, bunk.",
        "**Algorithm:** Mamdani. Triangular MFs → 18 rules, strength = min → clip + max-aggregate → centroid on 401 points → verdict (<35, <65, ≥65).",
        "**Safety rule:** attendance < 75 % always shows a red warning, separate from the score.",
        "**Numbers to remember:** 3 inputs, 18 rules, 3 output sets, 401 grid points, 29 tests; default (78, 2.5, 8) → 83.8 CAN SKIP.",
        "**Honest limits:** hand-made, unvalidated, not a probability, not ML.",
    ]))
    add(("h2", "H2. Formula sheet"))
    add(("table", ["Concept", "Formula"], [
        ["Triangular MF", "μ = 0 (x<a or x>c); (x−a)/(b−a) (a≤x<b); 1 (x=b); (c−x)/(c−b) (b<x≤c)"],
        ["AND / OR / NOT", "min(μ_{A}, μ_{B});  max(μ_{A}, μ_{B});  1 − μ_{A}   († product μ_{A}μ_{B}, prob. sum μ_{A}+μ_{B}−μ_{A}μ_{B})"],
        ["Firing strength", "w = min(μ_{att}, μ_{cred}, μ_{temp})"],
        ["Clipping (Mamdani)", "μ′_{out}(y) = min(w, μ_{out}(y))   († Larsen: w·μ_{out}(y))"],
        ["Aggregation", "μ_{agg}(y) = max_{rules} μ′_{out}(y)"],
        ["Centroid", "z* = ∫ zμ(z)dz / ∫ μ(z)dz  ≈  Σ x_{k}μ_{k} / Σ μ_{k}"],
        ["Sugeno †", "z = Σ w_{i}z_{i} / Σ w_{i}"],
        ["A*", "f(n) = g(n) + h(n);  admissible: h ≤ h*;  consistent: h(n) ≤ c(n,n′)+h(n′)"],
        ["Bayes", "P(A|B) = P(B|A)P(A)/P(B);  joint = Π P(x_{i}|parents)"],
        ["Neuron / update", "y = f(Σ w_{i}x_{i}+b);  w ← w − η ∂L/∂w;  perceptron w ← w + η(t−y)x"],
        ["Expected utility", "EU(a) = Σ P(s′|a) U(s′)"],
    ], [0.22, 0.78]))
    add(("h2", "H3. Glossary and Python function roles"))
    add(("table", ["Term", "Meaning", "Term", "Meaning"], [
        ["Universe of discourse", "Range of a variable", "Linguistic variable", "Variable whose values are words"],
        ["Membership degree", "Degree 0–1 of belonging", "Fuzzification", "Crisp value → degrees"],
        ["Antecedent / consequent", "IF part / THEN part", "Firing strength", "Truth of a rule's IF part"],
        ["Implication", "Limiting consequent by strength", "Aggregation", "Merging rule outputs (max)"],
        ["Defuzzification", "Fuzzy set → crisp number", "Centroid", "Balance point of the curve"],
        ["t-norm / t-conorm", "Generalised AND / OR", "Rule explosion", "Rules grow exponentially with sets"],
        ["Admissible heuristic", "Never overestimates", "Fitness function", "Scores a GA solution"],
    ], [0.2, 0.3, 0.2, 0.3]))
    add(("table", ["Function", "Role"], [
        ["`trimf(x,a,b,c)`", "Triangular membership degree."], ["`validate_inputs(values)`", "Reject missing / non-finite / out-of-range inputs."],
        ["`infer(values)`", "Whole Mamdani pipeline; returns `(fuzzy, fired, out_strength, xs, agg, score)`."],
        ["`defuzzify(xs, agg)`", "Centroid Σxμ/Σμ with the 50 fallback."], ["`verdict(score)`", "Text and colour from the 35 / 65 thresholds."],
        ["`below_attendance_minimum(att)`", "True if attendance < 75."], ["`apply_preset(...)` (app.py)", "Callback writing demo values into slider state."],
    ], [0.34, 0.66]))
    add(("h2", "H4. Common mistakes and the “never say” list"))
    add(("callout", "**Things we must never say incorrectly:**\n"
                    "• “The membership degree is a probability.” — It is a degree of belonging; no randomness.\n"
                    "• “The system was trained on a dataset.” — It was not; rules and sets are hand-written.\n"
                    "• “Firing strength is the final score.” — Strength is per rule (min); the score is the centroid of the aggregate.\n"
                    "• “The score is the chance I can skip safely.” — It is an index; skipping is never guaranteed safe.\n"
                    "• “A high score means I am eligible.” — Eligibility needs ≥ 75 % attendance, checked separately.\n"
                    "• “BunkWise is machine learning / AI that predicts results.” — It is a knowledge-based fuzzy system.\n"
                    "• “We validated it on real students.” — We did not.\n"
                    "• “Sugeno is what we use.” — We use Mamdani."))
    add(("ul", ["Confusing fuzzification (inputs → degrees) with defuzzification (output curve → number).",
                "Saying AND is `max` (it is `min`; OR is `max`).",
                "Forgetting that zero-strength rules are ignored, and that one 'maybe' rule alone gives exactly 50.",
                "Claiming the 401 points are “the output”: they are only the sampling grid of the output universe."]))
    add(("h2", "H5. Ten tough follow-up questions"))
    follow = [
        ("If min is AND, why not product?", "Both are valid t-norms. Min is simple, gives results bounded by the weakest condition and is the standard Mamdani choice; product would make strengths smaller when several conditions are partly true. Switching would change scores."),
        ("Can the centroid be outside the range of the active sets?", "No. It is a weighted mean of x, so it lies within the support of the aggregate; here always in [0, 100]."),
        ("Would more sets give a better system?", "Not automatically: finer control but more rules (rule explosion) and more subjective parameters; quality depends on correct rules."),
        ("Why not just use if-else on attendance?", "That creates cliffs (74.9 → warning, 75 → fine) and cannot combine several soft factors; fuzzy gives graded output and explanations. We still use a crisp check for the policy because it is a crisp rule."),
        ("How would you validate BunkWise?", "Collect real cases with expert/student judgements, compare scores to labels, check sensitivity, adjust sets. We have not done this."),
        ("Is 83.8 'more risky' than 76.8?", "No: higher means skipping is more tolerable. It is a tolerance index, not a risk probability, and the two are not interval-precise."),
        ("What if two rules give the same output set?", "Only the strongest counts (max). Equivalent to clipping each rule's consequent then taking max."),
        ("What is the time complexity of infer()?", "O(R + G·S) with R = 18 rules, G = 401 grid points and S = 3 output sets: constant for our fixed sizes."),
        ("What if temptation were negative?", "`validate_inputs` raises ValueError; the slider cannot produce it, but direct calls are rejected."),
        ("Is fuzzy logic AI?", "Yes, it is a soft-computing technique in the handout: it represents vague knowledge and reasons with it, though it does not learn by itself."),
    ]
    add(("qa", follow, 1, "H"))
    add(("h2", "H6. Two-minute explanation (either of us can say this)"))
    add(("p", "“BunkWise is a fuzzy-logic web app that helps a student think about skipping one class. We need 75 % attendance, but the decision isn't black and white, "
              "so we model three inputs: attendance, subject credits and temptation. Each input is *fuzzified* with triangular membership functions: for example 78 % attendance "
              "is fully ‘ok’ and not ‘danger’ or ‘safe’. We wrote 18 IF–THEN rules, one for every combination, such as IF attendance is ok AND credits are moderate AND temptation is high THEN bunk. "
              "Each rule's strength is the minimum of its three degrees. Then we clip the output sets at those strengths, merge them with maximum, and take the *centroid* of the merged shape. "
              "That gives a Bunk Score from 0 to 100, and a verdict: below 35 cannot skip, up to 65 caution, above that can skip. "
              "The app shows every step — memberships, active rules, the aggregated curve — so it is fully explainable. The score is an index, not a probability, and below 75 % attendance "
              "we always show a separate warning. Nothing is trained: it is a hand-built Mamdani system, tested with 29 automated tests.”"))
    add(("h2", "H7. Five-minute demo script and live-demo checklist"))
    add(("ol", [
        "(0:00) Open the app: say the tagline; point to the three sliders and the *Educational decision-support tool* label.",
        "(0:30) Default 78 / 2.5 / 8: score 83.8, CAN SKIP. Open **1 Fuzzification**: ok = 1, high temptation = 0.667.",
        "(1:30) **2 Active rules**: exactly one rule fires, strength 0.667 (min of 1, 1, 0.667). Open the full 18-rule expander.",
        "(2:15) **3 Aggregation & centroid**: clip level 0.667 on 'bunk', Σxμ/Σμ = 83.8; mention exact analytic centroid 83.75.",
        "(3:00) Click “Low attendance” (50 / 4 / 3): score falls to the 'cannot skip' zone and the red warning appears. Show the membership graphs tab.",
        "(3:45) Click “Below 75%, score still high”: score 76.8 but warning stays. Explain why the policy check is separate and the rule-base weakness.",
        "(4:30) Move a slider live to show results and graphs update together. Close: not a probability, not ML, not validated; mention 29 tests.",
    ]))
    add(("ul", ["[ ] `streamlit run app.py` works from a fresh terminal; browser opens on localhost.",
                "[ ] Tests pass: `python -m unittest discover -s tests -v`.",
                "[ ] Both of us can explain min, max, centroid and the default example numbers without notes.",
                "[ ] GitHub repo up to date (`git status` clean); PDF and README open correctly.",
                "[ ] Know the answers to: probability vs membership, Mamdani vs Sugeno, why separate warning, limitations."]))
    return B


# ------------------------------------------------------------------ markdown writer
def write_markdown(blocks):
    L = ["# BunkWise: Project Report and AISC Viva Guide", "",
         "*Fuzzy-logic attendance decision support · CSE3121 Artificial Intelligence and Soft Computing · Semester V, "
         "Manipal University Jaipur, July–Nov 2026.*  ",
         "*Generated by `docs/generate_viva_guide.py` together with the PDF; numbers come from `bunk_meter.infer()`.*", ""]
    for b in blocks:
        k = b[0]
        if k == "h1":
            L += ["", f"## {md_inline(b[1])}", ""]
        elif k == "h2":
            L += ["", f"### {md_inline(b[1])}", ""]
        elif k == "p":
            L += [md_inline(b[1]), ""]
        elif k == "ul":
            L += [f"- {md_inline(t)}" for t in b[1]] + [""]
        elif k == "ol":
            L += [f"{i}. {md_inline(t)}" for i, t in enumerate(b[1], 1)] + [""]
        elif k == "table":
            hdr, rows = b[1], b[2]
            L.append("| " + " | ".join(h or " " for h in hdr) + " |")
            L.append("|" + "---|" * len(hdr))
            for r in rows:
                L.append("| " + " | ".join(md_inline(str(c)).replace("\n", "<br>").replace("|", "\\|") for c in r) + " |")
            L.append("")
        elif k == "code":
            L += ["```", b[1], "```", ""]
        elif k == "eq":
            L += [f"> {md_inline(b[1])}", ""]
        elif k == "callout":
            L += ["> " + md_inline(b[1]).replace("\n", "  \n> "), ""]
        elif k == "qa":
            for i, (q, a) in enumerate(b[1], b[2]):
                L += [f"**{b[3]}{i}. {md_inline(q)}**  ", md_inline(a), ""]
        elif k == "diagram":
            L += ["*[Diagram: architecture — user → app.py (Streamlit) → `bunk_meter.infer()` → result tuple → score/verdict, gauge, 75 % warning, "
                  "rule table, charts; tests check both. See the PDF for the picture.]*", ""]
        elif k == "pipe":
            L += ["*[Flowchart: crisp inputs → `validate_inputs` → fuzzification → rule evaluation (min) → implication (clip) → aggregation (max) → "
                  "centroid → `verdict`; the 75 % warning is a separate check.]*", ""]
        elif k == "plot":
            L += [f"*[Plot: {dict(tri='triangular membership function', att='attendance fuzzy sets with the worked-example input', agg='aggregated output of the worked example')[b[1]]} — see the PDF.]*", ""]
        elif k == "toc":
            pass
    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# ------------------------------------------------------------------ PDF writer
class GuideDoc(BaseDocTemplate):
    def __init__(self, path, **kw):
        super().__init__(path, pagesize=A4, leftMargin=1.7 * cm, rightMargin=1.7 * cm, topMargin=1.9 * cm,
                         bottomMargin=1.6 * cm, title="BunkWise: Project Report and AISC Viva Guide",
                         author="BunkWise team", **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f", leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=self._cover),
                               PageTemplate(id="body", frames=[frame], onPage=self._decor)])

    def _cover(self, c, d):
        w, h = A4
        c.setFillColor(NAVY)
        c.rect(0, h * 0.42, w, h * 0.58, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.rect(0, h * 0.42 - 6, w, 6, fill=1, stroke=0)

    def _decor(self, c, d):
        w, h = A4
        c.setFont("Body", 7.5)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(1.7 * cm, h - 1.15 * cm, "BunkWise · Project Report & AISC Viva Guide")
        c.drawRightString(w - 1.7 * cm, h - 1.15 * cm, "CSE3121 · Manipal University Jaipur")
        c.setStrokeColor(ACCENT)
        c.setLineWidth(0.7)
        c.line(1.7 * cm, h - 1.3 * cm, w - 1.7 * cm, h - 1.3 * cm)
        c.drawCentredString(w / 2, 0.85 * cm, f"Page {d.page}")
        c.drawString(1.7 * cm, 0.85 * cm, "Educational use")

    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph):
            name = fl.style.name
            if name in ("H1", "H2"):
                self.notify("TOCEntry", (0 if name == "H1" else 1, fl.getPlainText(), self.page))


def make_styles():
    base = dict(fontName="Body", fontSize=8.8, leading=11.6, spaceAfter=3.5, textColor=colors.HexColor("#1b1b24"))
    S = {
        "body": ParagraphStyle("body", **base),
        "bullet": ParagraphStyle("bullet", **{**base, "leftIndent": 11, "bulletIndent": 2, "spaceAfter": 2}),
        "cell": ParagraphStyle("cell", **{**base, "fontSize": 7.9, "leading": 10, "spaceAfter": 0}),
        "cellh": ParagraphStyle("cellh", **{**base, "fontSize": 7.9, "leading": 10, "spaceAfter": 0, "fontName": "Body-B",
                                            "textColor": colors.white}),
        "H1": ParagraphStyle("H1", **{**base, "fontName": "Body-B", "fontSize": 14.5, "leading": 18, "textColor": NAVY,
                                      "spaceBefore": 8, "spaceAfter": 5}),
        "H1x": ParagraphStyle("H1x", **{**base, "fontName": "Body-B", "fontSize": 14.5, "leading": 18, "textColor": NAVY,
                                        "spaceAfter": 5}),
        "H2": ParagraphStyle("H2", **{**base, "fontName": "Body-B", "fontSize": 10.2, "leading": 13, "textColor": ACCENT,
                                      "spaceBefore": 6, "spaceAfter": 3}),
        "qa": ParagraphStyle("qa", **{**base, "spaceAfter": 4.5}),
        "eq": ParagraphStyle("eq", **{**base, "alignment": TA_CENTER, "fontName": "Body-I", "fontSize": 9, "spaceBefore": 2,
                                      "spaceAfter": 5, "backColor": LIGHT, "borderPadding": 4}),
        "callout": ParagraphStyle("callout", **{**base, "backColor": colors.HexColor("#fff4d6"), "borderColor": colors.HexColor("#e3a03a"),
                                                "borderWidth": 0.8, "borderPadding": 6, "spaceBefore": 4, "spaceAfter": 8}),
    }
    return S


def make_table(hdr, rows, widths, S, total):
    data = [[Paragraph(pdf_inline(h), S["cellh"]) for h in hdr]]
    for r in rows:
        data.append([Paragraph(pdf_inline(str(c)), S["cell"]) for c in r])
    cw = [w * total for w in widths] if widths else None
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c4c7e0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    return t


def build_plot(kind, ex_cache):
    if kind == "tri":
        pts = [(2, 0), (5, 1), (8, 0)]
        return Plot([(pts, ACCENT, False, True, "μ(x; a=2, b=5, c=8)")], xmax=10, vlines=[(2, colors.gray, "a"), (5, colors.gray, "b"), (8, colors.gray, "c")],
                    height=95, xlabel="x")
    if kind == "att":
        cfg = bm.INPUTS["attendance"]
        cols = [colors.HexColor("#d63031"), colors.HexColor("#e17f00"), colors.HexColor("#00a37a")]
        ser = [(tri_points(abc, 0, 100), col, False, False, f"{n} {abc}") for (n, abc), col in zip(cfg["sets"].items(), cols)]
        return Plot(ser, xmax=100, vlines=[(78, NAVY, "78 %")], height=100, xlabel="attendance (%) — the overlaps are where categories blend")
    ex = ex_cache
    cols = {"attend": colors.HexColor("#d63031"), "maybe": colors.HexColor("#e17f00"), "bunk": colors.HexColor("#00a37a")}
    ser = [([(float(x), bm.trimf(float(x), *abc)) for x in np.linspace(0, 100, 201)], cols[n], True, False, n) for n, abc in bm.OUTPUT_SETS.items()]
    ser.append(([(float(x), float(y)) for x, y in zip(ex["xs"], ex["agg"])], ACCENT, False, True, "aggregated output"))
    return Plot(ser, xmax=100, vlines=[(ex["score"], NAVY, f"centroid {ex['score']:.1f}")], height=105, xlabel="Bunk Score")


def check_glyphs(blocks):
    """Fail loudly if any character in the content is missing from both the body and fallback fonts."""
    real = "".join(str(x) for b in blocks for x in b[1:])
    missing = sorted({ch for ch in real if ord(ch) > 127 and not _in_font(ch)
                      and not (HAS_FALLBACK and _in_font(ch, "Fallback"))})
    if missing:
        raise SystemExit(f"Glyphs missing from all fonts: {missing}")
    via_fallback = sorted({ch for ch in real if ord(ch) > 127 and not _in_font(ch)})
    if via_fallback:
        print("characters drawn with the fallback font:", " ".join(f"U+{ord(c):04X}" for c in via_fallback))


def write_pdf(blocks):
    global HAS_FALLBACK
    register_fonts()
    HAS_FALLBACK = register_fallback()
    check_glyphs(blocks)
    S = make_styles()
    doc = GuideDoc(PDF_PATH)
    total = doc.width
    ex_cache = trace(78, 2.5, 8)
    st = []
    # cover
    st += [Spacer(1, 3.3 * cm),
           Paragraph("BunkWise", ParagraphStyle("t", fontName="Body-B", fontSize=44, leading=50, textColor=colors.white)),
           Paragraph("Skip the guesswork. Know your risk.", ParagraphStyle("t2", fontName="Body-I", fontSize=15, leading=20,
                                                                           textColor=colors.HexColor("#cfc9ff"))),
           Spacer(1, 1.2 * cm),
           Paragraph("Project Report and AISC Viva Guide", ParagraphStyle("t3", fontName="Body-B", fontSize=22, leading=28, textColor=colors.white)),
           Paragraph("A fuzzy-logic (Mamdani) attendance decision-support tool", ParagraphStyle("t4", fontName="Body", fontSize=12, leading=16,
                                                                                               textColor=colors.HexColor("#e8eaf6"))),
           Spacer(1, 8.6 * cm)]
    meta = ParagraphStyle("m", fontName="Body", fontSize=10.5, leading=16, textColor=colors.HexColor("#1b1b24"))
    for line in ["<b>Course:</b> CSE3121 Artificial Intelligence and Soft Computing, B.Tech Semester V",
                 "<b>Institution:</b> Manipal University Jaipur, Dept. of Computer Science and Engineering · July–Nov 2026",
                 "<b>Team:</b> Aryan Rajguru · Anvi",
                 "<b>Code:</b> github.com/AryanRajguru22/Bunkwise",
                 "<b>Stack:</b> Python · Streamlit · NumPy · Plotly",
                 "<i>Educational decision-support tool; not validated, not an institutional policy.</i>"]:
        st.append(Paragraph(line, meta))
    from reportlab.platypus import NextPageTemplate
    st += [NextPageTemplate("body"), PageBreak()]
    toc_added = False
    for idx, b in enumerate(blocks):
        k = b[0]
        nxt = blocks[idx + 1][0] if idx + 1 < len(blocks) else ""
        if k == "h1":
            st += [CondPageBreak(4.5 * cm), Paragraph(pdf_inline(b[1]), S["H1"])]
        elif k == "h2":
            # keep a heading with a following unsplittable-looking box (callout) instead of orphaning it
            st += [CondPageBreak(6.5 * cm if nxt == "callout" else 3 * cm), Paragraph(pdf_inline(b[1]), S["H2"])]
        elif k == "p":
            st.append(Paragraph(pdf_inline(b[1]), S["body"]))
        elif k == "ul":
            st += [Paragraph(pdf_inline(t), S["bullet"], bulletText="•") for t in b[1]]
            st.append(Spacer(1, 2))
        elif k == "ol":
            st += [Paragraph(pdf_inline(t), S["bullet"], bulletText=f"{i}.") for i, t in enumerate(b[1], 1)]
            st.append(Spacer(1, 2))
        elif k == "table":
            st += [make_table(b[1], b[2], b[3] if len(b) > 3 else None, S, total), Spacer(1, 6)]
        elif k == "code":
            st += [Preformatted(b[1], ParagraphStyle("code", fontName="Mono", fontSize=7.6, leading=9.6, backColor=colors.HexColor("#f4f4f8"),
                                                     borderPadding=5, leftIndent=4, spaceAfter=8, spaceBefore=2)), Spacer(1, 3)]
        elif k == "eq":
            st.append(Paragraph(pdf_inline(b[1]), S["eq"]))
        elif k == "callout":
            st.append(Paragraph(pdf_inline(b[1]), S["callout"]))
        elif k == "qa":
            for i, (q, a) in enumerate(b[1], b[2]):
                st.append(Paragraph(f"<b>{b[3]}{i}. {pdf_inline(q)}</b><br/>{pdf_inline(a)}", S["qa"]))
        elif k == "diagram":
            st += [ArchDiagram(), Spacer(1, 6)]
        elif k == "pipe":
            st += [PipeDiagram(), Spacer(1, 8)]
        elif k == "plot":
            st += [build_plot(b[1], ex_cache), Spacer(1, 6)]
        elif k == "toc":
            toc = TableOfContents()
            toc.levelStyles = [ParagraphStyle("t0", fontName="Body-B", fontSize=9, leading=11, leftIndent=0, spaceBefore=2),
                               ParagraphStyle("t1", fontName="Body", fontSize=7.8, leading=9.4, leftIndent=14)]
            toc.dotsMinLevel = 0
            st += [Paragraph("Contents", S["H1x"]), toc, Spacer(1, 8)]
            toc_added = True
    assert toc_added
    doc.multiBuild(st)


if __name__ == "__main__":
    content = build_content()
    write_markdown(content)
    write_pdf(content)
    print("wrote", MD_PATH)
    print("wrote", PDF_PATH)
