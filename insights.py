"""BunkWise - presentation helpers that sit between the fuzzy engine and the UI.

Pure Python (no Streamlit), so everything here is unit-testable. Every number comes from
bunk_meter.evaluate(); nothing here re-implements fuzzy maths.
"""
import math

import bunk_meter as bm

DISCLAIMER = ("BunkWise is an educational decision-support tool built on a hand-designed fuzzy system. "
              "The Bunk Score is a fuzzy index, not a probability, and it does not guarantee eligibility "
              "under your institution's attendance rules.")

MAX_SUBJECTS = 8
MAX_NAME_LENGTH = 40


# ---------------------------------------------------------------- what the inputs mean
def dominant_sets(memberships, threshold=0.0):
    """[(set name, degree)] for sets with degree above `threshold`, strongest first."""
    items = [(s, mu) for s, mu in memberships.items() if mu > threshold]
    return sorted(items, key=lambda kv: -kv[1])


def describe_membership(memberships):
    """'ok (1.00)' or 'ok (0.62) and safe (0.38)' - the fuzzy sets an input belongs to."""
    parts = [f"*{s}* ({mu:.2f})" for s, mu in dominant_sets(memberships)]
    return parts[0] if len(parts) == 1 else " and ".join(parts) if parts else "no set"


def explain(ev):
    """Plain-English steps explaining the result, built from the real inference results."""
    steps = [
        f"**1. What the rules see.** Attendance {ev.attendance:g}% is {describe_membership(ev.fuzzy['attendance'])}; "
        f"{ev.credits:g} credits is {describe_membership(ev.fuzzy['credits'])}; "
        f"temptation {ev.temptation:g}/10 is {describe_membership(ev.fuzzy['temptation'])}.",
    ]
    if ev.fired:
        s, a, c, t, out = ev.fired[0]
        rule = (f"**2. Rules that fired.** {len(ev.fired)} of {len(bm.RULES)} rules are active. The strongest is "
                f"IF attendance is *{a}* AND credits are *{c}* AND temptation is *{t}* THEN *{out}* "
                f"(strength {s:.2f}).")
    else:  # unreachable for valid inputs (checked by a test); kept so the UI never crashes
        rule = "**2. Rules that fired.** None, so the neutral fallback score of 50 was used."
    steps.append(rule)
    steps.append(f"**3. Raw fuzzy score.** The clipped output sets are merged and their centroid is "
                 f"**{ev.score:.1f} / 100**, which the fuzzy verdict reads as **{ev.raw_verdict}**.")
    if ev.below_minimum:
        steps.append(f"**4. Attendance policy.** Attendance {ev.attendance:g}% is below the mandatory "
                     f"{bm.ATTENDANCE_MIN}%, so the policy step overrides the fuzzy verdict: "
                     f"**{ev.final_text}**. The raw score above is unchanged.")
    else:
        steps.append(f"**4. Attendance policy.** Attendance {ev.attendance:g}% is at or above the mandatory "
                     f"{bm.ATTENDANCE_MIN}%, so the final recommendation follows the fuzzy verdict: "
                     f"**{ev.final_text}**. Meeting the minimum is not proof that skipping is safe.")
    return steps


# ---------------------------------------------------------------- what-if sweep
def attendance_sweep(credits, temptation, step=1.0):
    """Raw score and final recommendation for attendance 0..100, other inputs fixed.

    Returns a list of dicts with keys attendance, score, final.
    """
    points = int(round(100 / step))
    rows = []
    for i in range(points + 1):
        att = min(100.0, i * step)
        ev = bm.evaluate(att, credits, temptation)
        rows.append({"attendance": att, "score": ev.score, "final": ev.final_text})
    return rows


def attendance_for_verdict(credits, temptation, target_score=65.0, step=0.5):
    """Lowest attendance (at or above the 75% minimum) whose RAW score reaches `target_score`.

    Returns None if no attendance in [75, 100] reaches it. This reads the engine; it is not a promise.
    """
    att = float(bm.ATTENDANCE_MIN)
    while att <= 100.0:
        if bm.evaluate(att, credits, temptation).score >= target_score:
            return att
        att += step
    return None


# ---------------------------------------------------------------- multi-subject comparison
def _clean_number(value, lo, hi):
    """Return float(value) when it is a finite number inside [lo, hi], else None."""
    if value is None or isinstance(value, bool):
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) and lo <= x <= hi else None


def compare_subjects(records):
    """Run the engine for several subjects.

    records: iterable of dicts with keys name, attendance, credits, temptation (as typed by the user).
    Returns a list of result dicts; an incomplete or invalid row gets status 'Check inputs' instead of
    raising, so one bad row never hides the others. At most MAX_SUBJECTS rows are evaluated.
    """
    rows = []
    for i, rec in enumerate(list(records)[:MAX_SUBJECTS], start=1):
        raw_name = rec.get("name")  # NaN/None from an empty table cell is not a string
        name = (raw_name.strip()[:MAX_NAME_LENGTH] if isinstance(raw_name, str) else "") or f"Subject {i}"
        vals = {k: _clean_number(rec.get(k), *bm.INPUTS[k]["range"]) for k in bm.INPUTS}
        if any(v is None for v in vals.values()):
            rows.append({"name": name, **{k: rec.get(k) for k in bm.INPUTS}, "score": None,
                         "raw_verdict": "-", "final": "Check inputs", "overridden": False, "valid": False})
            continue
        ev = bm.evaluate(vals["attendance"], vals["credits"], vals["temptation"])
        rows.append({"name": name, **vals, "score": ev.score, "raw_verdict": ev.raw_verdict,
                     "final": ev.final_text, "overridden": ev.overridden, "valid": True})
    return rows


# ---------------------------------------------------------------- downloadable report
def build_report(ev):
    """Markdown decision report for one evaluation. Contains only the numbers the user entered."""
    lines = [
        "# BunkWise decision report", "",
        "## Inputs", "",
        f"- Attendance: {ev.attendance:g}% (mandatory minimum {bm.ATTENDANCE_MIN}%)",
        f"- Subject credits: {ev.credits:g}",
        f"- Temptation to skip: {ev.temptation:g} / 10", "",
        "## Result", "",
        f"- Raw fuzzy Bunk Score: {ev.score:.1f} / 100",
        f"- Raw fuzzy verdict: {ev.raw_verdict}",
        f"- Final recommendation: {ev.final_text}",
    ]
    if ev.below_minimum:
        lines.append(f"- Attendance policy: attendance is below {bm.ATTENDANCE_MIN}%, so the final recommendation "
                     "overrides the fuzzy verdict. The raw score is unchanged.")
    lines += ["", "## Membership degrees", ""]
    for name, cfg in bm.INPUTS.items():
        lines.append(f"- {name}: " + ", ".join(f"{s} {ev.fuzzy[name][s]:.3f}" for s in cfg["sets"]))
    lines += ["", f"## Active rules ({len(ev.fired)} of {len(bm.RULES)})", ""]
    for s, a, c, t, out in ev.fired:
        lines.append(f"- [{s:.3f}] IF attendance={a} AND credits={c} AND temptation={t} THEN {out}")
    lines += ["", "## Output clip levels", ""]
    lines += [f"- {name}: {level:.3f}" for name, level in ev.out_strength.items()]
    lines += ["", "## Method", "",
              "Mamdani fuzzy inference: triangular membership functions, 18 IF-THEN rules, min for AND, "
              "max aggregation, centroid defuzzification over 401 points. Thresholds: below 35 cannot skip, "
              "35 to below 65 proceed with caution, 65 and above can skip. The 75% attendance rule is a "
              "separate crisp policy applied after inference.", "",
              f"> {DISCLAIMER}", ""]
    return "\n".join(lines)
