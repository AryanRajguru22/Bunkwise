"""Generate the BunkWise final project report (Markdown, editable DOCX and PDF).

    pip install -r requirements-docs.txt
    python docs/generate_final_report.py

Everything numerical in the report is computed here by running the real bunk_meter code and the real test suite.
The script fails loudly if the code no longer matches what the report documents (parameter tables, rule base,
the 83.82 and 76.77 scores pinned by the tests).  The DOCX is written with python-docx; the PDF is exported from
that DOCX by Microsoft Word (COM automation), which also fills in the table of contents and lists of figures
and tables.  Cover-page details that are not known are placeholders: set them in COVER below and regenerate.
"""
import ast
import io
import os
import platform
import subprocess
import sys
import tempfile
import time
import unittest
from importlib import metadata

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import bunk_meter as bm  # noqa: E402
import final_report_content as content  # noqa: E402
import final_report_figures as figures  # noqa: E402
import final_report_render as render  # noqa: E402

ASSETS = os.path.join(HERE, "report_assets")
BASENAME = "BunkWise_Final_Project_Report"
DOCX_PATH = os.path.join(HERE, BASENAME + ".docx")
PDF_PATH = os.path.join(HERE, BASENAME + ".pdf")
MD_PATH = os.path.join(HERE, BASENAME + ".md")

PLACEHOLDER = "[to be added by the students]"
COVER = {
    "title": content.TITLE,
    "course": "Artificial Intelligence and Soft Computing (AISC)",
    "students": [("Anvi Tiwari", "2427030706"), ("Aryan Rajguru", "2427030355")],
    "faculty": PLACEHOLDER,       # faculty name: not known, do not invent
    "institution": PLACEHOLDER,   # department / programme / university: not known
    "date": PLACEHOLDER,          # submission date: not known
}

# What the report documents; the script asserts the code still says the same.
EXPECTED_SETS = {
    "attendance": {"danger": (0, 0, 75), "ok": (70, 78, 85), "safe": (80, 100, 100)},
    "credits": {"fragile": (1, 1, 2.5), "moderate": (1.5, 2.5, 3.5), "heavy": (2.5, 4, 4)},
    "temptation": {"low": (0, 0, 6), "high": (4, 10, 10)},
}
EXPECTED_OUTPUT = {"attend": (0, 0, 45), "maybe": (30, 50, 70), "bunk": (55, 100, 100)}
EXPECTED_MATRIX = [  # rule summary table of the presentation (slide 4)
    ["Danger", "attend / attend", "attend / maybe", "attend / attend"],
    ["Ok", "attend / maybe", "maybe / bunk", "attend / maybe"],
    ["Safe", "maybe / maybe", "maybe / bunk", "maybe / bunk"],
]


def run_infer(a, c, t):
    return bm.infer({"attendance": a, "credits": c, "temptation": t})


def score_of(a, c, t):
    return run_infer(a, c, t)[-1]


# ----------------------------------------------------------------------------- computed facts
def check_code_matches_report():
    for name, sets in EXPECTED_SETS.items():
        assert {k: tuple(v) for k, v in bm.INPUTS[name]["sets"].items()} == sets, f"{name} sets changed"
    assert {k: tuple(v) for k, v in bm.OUTPUT_SETS.items()} == EXPECTED_OUTPUT, "output sets changed"
    assert len(bm.RULES) == 18 and bm.ATTENDANCE_MIN == 75
    assert [bm.INPUTS[n]["range"] for n in ("attendance", "credits", "temptation")] == [(0, 100), (1, 4), (0, 10)]


def rule_matrix():
    lookup = {(a, c, t): o for a, c, t, o in bm.RULES}
    rows = []
    for att in bm.INPUTS["attendance"]["sets"]:
        row = [att.capitalize()]
        for cred in bm.INPUTS["credits"]["sets"]:
            row.append(f"{lookup[(att, cred, 'low')]} / {lookup[(att, cred, 'high')]}")
        rows.append(row)
    assert rows == EXPECTED_MATRIX, "rule base differs from the presentation's rule table"
    return rows


def example(a, c, t):
    fuzzy, fired, out_strength, xs, agg, score = run_infer(a, c, t)
    raw_text, _ = bm.verdict(score)
    final_text, _ = bm.final_recommendation(score, a)
    return dict(fuzzy=fuzzy, fired=fired, out_strength=out_strength, xs=xs, agg=agg, score=score,
                raw_text=raw_text, final_text=final_text, sum_mu=agg.sum(), sum_xmu=(xs * agg).sum())


def worked_examples():
    e1 = example(78, 2.5, 8)
    e2 = example(72, 2.5, 9)
    assert round(e1["score"], 2) == 83.82 and round(e2["score"], 2) == 76.77  # pinned by the test suite
    assert len(e1["fired"]) == 1 and abs(e1["fired"][0][0] - 2 / 3) < 1e-12
    assert len(e2["fired"]) == 2 and e2["raw_text"] == "CAN SKIP THE CLASS" and e2["final_text"] == bm.BELOW_MINIMUM_TEXT
    # exact continuous centroid of the clipped 'bunk' trapezoid: triangle (area 10, y=75) + rectangle (area 10, y=92.5)
    h = 2 / 3
    x_knee = 55 + 45 * h
    a1, y1 = 0.5 * (x_knee - 55) * h, (55 + 2 * x_knee) / 3
    a2, y2 = (100 - x_knee) * h, (x_knee + 100) / 2
    exact = (a1 * y1 + a2 * y2) / (a1 + a2)
    assert abs(a1 - 10) < 1e-9 and abs(a2 - 10) < 1e-9 and abs(exact - 83.75) < 1e-9
    xs, agg = e1["xs"], e1["agg"]
    trapz = getattr(np, "trapezoid", None) or np.trapz
    e1["exact"] = exact
    e1["trapz_area"] = float(trapz(agg, xs))
    e1["trapz"] = float(trapz(xs * agg, xs) / trapz(agg, xs))
    fine_x = np.linspace(0, 100, 40001)
    fine_agg = np.minimum(h, np.array([bm.trimf(x, *bm.OUTPUT_SETS["bunk"]) for x in fine_x]))
    e1["fine_sum"] = float(fine_agg.sum())
    e1["fine"] = float((fine_x * fine_agg).sum() / fine_agg.sum())
    # the claims made in Chapter 8 about the three alternatives
    assert abs(e1["sum_mu"] - (80 + 1 / 3)) < 1e-9
    assert round(e1["trapz"], 2) == 83.75 and round(e1["fine"], 2) == 83.75, (e1["trapz"], e1["fine"])
    return e1, e2


def sensitivity_facts():
    atts = np.arange(0, 100.01, 0.5)
    firsts = []
    for t in (8, 9, 10):
        firsts.append(next(a for a in atts if score_of(a, 2.5, t) >= 65))
    assert len(set(firsts)) == 1
    t8 = {a: score_of(a, 2.5, 8) for a in (70, 72, 75, 80, 85)}
    temps = np.linspace(0, 10, 201)
    for c in (1, 4):
        assert max(score_of(78, c, t) for t in temps) <= 50.0 + 1e-9
    return {"first65": firsts[0], "t8": t8, "danger70": bm.trimf(70, *bm.INPUTS["attendance"]["sets"]["danger"])}


def short(text):
    return content.SHORT_VERDICT[text]


def preset_and_scenario_rows():
    with open(os.path.join(ROOT, "app.py"), encoding="utf-8") as f:
        tree = ast.parse(f.read())
    presets = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "PRESETS")
    assert len(presets) == 5
    preset_rows, scen_rows = [], []
    for label, a, c, t, _note in presets:
        _, fired, _, _, _, s = run_infer(a, c, t)
        raw, final = bm.verdict(s)[0], bm.final_recommendation(s, a)[0]
        preset_rows.append([label, f"{a:g}", f"{c:g}", f"{t:g}", f"{s:.2f}", short(raw), short(final)])
        scen_rows.append([label, f"{a:g}", f"{c:g}", f"{t:g}", str(len(fired)), f"{s:.2f}", short(raw), short(final)])
    extra = [("Boundary: exactly 75%", 75, 2.5, 8), ("Just below 75%", 74.9, 2.5, 8), ("Very high attendance and temptation", 100, 2.5, 10)]
    for label, a, c, t in extra:
        _, fired, _, _, _, s = run_infer(a, c, t)
        raw, final = bm.verdict(s)[0], bm.final_recommendation(s, a)[0]
        scen_rows.append([label, f"{a:g}", f"{c:g}", f"{t:g}", str(len(fired)), f"{s:.2f}", short(raw), short(final)])
    return preset_rows, scen_rows


def run_test_suite():
    """Run the project's own unittest suite (same discovery as `python -m unittest discover -s tests`)."""
    tests_dir = os.path.join(ROOT, "tests")
    suite = unittest.defaultTestLoader.discover(tests_dir, top_level_dir=tests_dir)

    def flatten(s):
        for item in s:
            if isinstance(item, unittest.TestSuite):
                yield from flatten(item)
            else:
                yield item

    ids = [t.id() for t in flatten(suite)]
    stream = io.StringIO()
    t0 = time.time()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    seconds = time.time() - t0
    bad = {t.id() for t, _ in result.failures + result.errors}
    outcome = {i.split(".")[-1]: ("fail" if i in bad else "pass") for i in ids}
    algo = sum(1 for i in ids if i.startswith("test_bunk_meter."))
    ui = sum(1 for i in ids if i.startswith("test_app."))
    return {"total": result.testsRun, "failed": len(bad), "seconds": seconds, "outcome": outcome, "algo": algo, "ui": ui}


def test_rows(tests):
    rows, covered = [], set()
    for area, objective, expected, names in content.TEST_AREAS:
        for n in names:
            assert n in tests["outcome"], f"test {n} no longer exists"
        covered.update(names)
        passed = sum(tests["outcome"][n] == "pass" for n in names)
        rows.append([area, objective, expected, f"{passed} / {len(names)} passed"])
    assert covered == set(tests["outcome"]), f"tests missing from the report table: {set(tests['outcome']) - covered}"
    return rows


def versions():
    v = {k: metadata.version(k) for k in ("numpy", "streamlit", "plotly", "pandas", "matplotlib")}
    v["python"] = platform.python_version()
    v["os"] = f"Windows 11 (build {platform.version()})" if platform.system() == "Windows" else platform.platform()
    return v


# ----------------------------------------------------------------------------- Word export
WORD_SCRIPT = r"""
param([string]$Docx, [string]$Pdf)
$ErrorActionPreference = 'Stop'
$hadWord = [bool](Get-Process WINWORD -ErrorAction SilentlyContinue)
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx)
    foreach ($name in 'TOC 1', 'TOC 2', 'Table of Figures') {
        try {
            $s = $doc.Styles.Item($name)
            $s.ParagraphFormat.SpaceAfter = 2; $s.ParagraphFormat.SpaceBefore = 0
            $s.ParagraphFormat.LineSpacingRule = 0; $s.ParagraphFormat.Alignment = 0
            $s.Font.Name = 'Times New Roman'; $s.Font.Size = 10.5
        } catch { }
    }
    try { $doc.Styles.Item('TOC 1').Font.Bold = $true; $doc.Styles.Item('TOC 2').ParagraphFormat.LeftIndent = 14 } catch { }
    for ($i = 0; $i -lt 3; $i++) {
        $doc.Repaginate()
        foreach ($t in $doc.TablesOfContents) { $t.Update() }
        $doc.Fields.Update() | Out-Null
    }
    $doc.Save()
    $doc.ExportAsFixedFormat($Pdf, 17, $false, 0, 0, 1, 1, 0, $true, $true, 1, $true, $true, $false)
    Write-Output ("PAGES=" + $doc.ComputeStatistics(2))
    $doc.Close(0)
} finally {
    if (-not $hadWord) { $word.Quit() }
}
"""


def export_pdf_with_word(docx, pdf):
    if os.path.exists(pdf):
        os.remove(pdf)
    with tempfile.TemporaryDirectory() as tmp:
        ps1 = os.path.join(tmp, "export.ps1")
        with open(ps1, "w", encoding="utf-8-sig") as f:
            f.write(WORD_SCRIPT)
        proc = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1, docx, pdf],
                              capture_output=True, text=True, timeout=420)
    print(proc.stdout.strip())
    if proc.returncode != 0 or not os.path.exists(pdf):
        raise RuntimeError(f"Word export failed:\n{proc.stdout}\n{proc.stderr}")


# ----------------------------------------------------------------------------- main
def main():
    check_code_matches_report()
    e1, e2 = worked_examples()
    ctx = {
        "bm": bm, "cover": COVER, "E1": e1, "E2": e2, "facts": sensitivity_facts(), "versions": versions(),
        "exact_centroid": e1["exact"], "rule_matrix": rule_matrix(),
        "screens": {k: os.path.join(ASSETS, f) for k, f in {
            "overview": "app_default_top.png", "aggregation": "app_tab_aggregation.png",
            "override_final": "app_override_final.png"}.items()},
    }
    for p in ctx["screens"].values():
        assert os.path.exists(p), f"missing screenshot {p}; run docs/capture_screenshots.py"
    ctx["preset_rows"], ctx["scen_rows"] = preset_and_scenario_rows()
    print("running the project's test suite ...")
    ctx["tests"] = run_test_suite()
    t = ctx["tests"]
    print(f"tests: {t['total']} run, {t['failed']} failed, {t['seconds']:.1f}s ({t['algo']} algorithm + {t['ui']} UI)")
    assert t["failed"] == 0, "test suite is failing; not generating a report that says otherwise"
    assert (t["total"], t["algo"], t["ui"]) == (38, 31, 7), "test counts changed; review Chapter 10 and the abstract"
    ctx["test_rows"] = test_rows(t)

    print("drawing figures ...")
    ctx["figs"] = figures.make_all(ASSETS, ctx)

    blocks = content.build(ctx)
    ctx["numbering"] = render.prepare(blocks, content.REFERENCES)
    with tempfile.TemporaryDirectory() as eq_dir:
        render.write_markdown(blocks, ctx, MD_PATH)
        render.write_docx(blocks, ctx, DOCX_PATH, eq_dir)
    print("wrote", MD_PATH)
    print("wrote", DOCX_PATH)
    export_pdf_with_word(DOCX_PATH, PDF_PATH)
    print("wrote", PDF_PATH)


if __name__ == "__main__":
    main()
