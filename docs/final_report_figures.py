"""Figures for the final project report (matplotlib).

Every curve is computed with the real bunk_meter functions; nothing is drawn by hand except the
architecture and flowchart diagrams, which follow the structure of bunk_meter.py / app.py.
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon  # noqa: E402

import bunk_meter as bm  # noqa: E402

INDIGO, AMBER, TEAL = "#5b4bdb", "#d08a1d", "#2a9d8f"
RED, GREEN, INK, MUTED, GRID = "#c5453e", "#2f8f62", "#25232b", "#6b6760", "#e4dccf"
OUT_COLORS = {"attend": RED, "maybe": AMBER, "bunk": GREEN}
SET_COLORS = [INDIGO, AMBER, TEAL]

plt.rcParams.update({
    "font.family": "Arial", "font.size": 9, "axes.edgecolor": "#8a857c", "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "figure.dpi": 100,
    "mathtext.fontset": "stix", "savefig.facecolor": "white",
})


def _save(fig, path):
    fig.savefig(path, dpi=250, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    return path


def _curve(abc, lo, hi, n=801):
    xs = np.linspace(lo, hi, n)
    return xs, np.array([bm.trimf(x, *abc) for x in xs])


# ---------------------------------------------------------------- theory figure
def fig_trimf_shapes(out):
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.3), sharey=True)
    cases = [("(a) general triangle  $(a,b,c)=(70,78,85)$", (70, 78, 85), (60, 95)),
             ("(b) left shoulder  $(0,0,75)$", (0, 0, 75), (0, 100)),
             ("(c) right shoulder  $(80,100,100)$", (80, 100, 100), (60, 100))]
    for ax, (title, abc, (lo, hi)) in zip(axes, cases):
        xs, ys = _curve(abc, lo, hi)
        ax.plot(xs, ys, color=INDIGO, lw=2.2)
        ax.fill_between(xs, ys, color=INDIGO, alpha=0.12)
        ax.set_title(title, fontsize=8.5)
        ax.set_xlim(lo, hi)
        ax.set_ylim(0, 1.18)
        ax.set_xlabel("x")
    axes[0].set_ylabel(r"membership $\mu(x)$")
    a, b, c = 70, 78, 85
    axes[0].annotate("a", (a, 0), (a - 0.5, 0.06), ha="right", color=MUTED)
    axes[0].annotate("b", (b, 1), (b, 1.06), ha="center", color=MUTED)
    axes[0].annotate("c", (c, 0), (c + 0.5, 0.06), ha="left", color=MUTED)
    return _save(fig, out)


# ---------------------------------------------------------------- membership functions
def fig_membership_functions(out):
    fig, axes = plt.subplots(2, 2, figsize=(7.0, 4.9))
    panels = [(bm.INPUTS["attendance"], "Attendance (%)", axes[0, 0]),
              (bm.INPUTS["credits"], "Subject credits", axes[0, 1]),
              (bm.INPUTS["temptation"], "Temptation to skip (0-10)", axes[1, 0])]
    for cfg, title, ax in panels:
        lo, hi = cfg["range"]
        for (name, abc), col in zip(cfg["sets"].items(), SET_COLORS):
            xs, ys = _curve(abc, lo, hi)
            ax.plot(xs, ys, color=col, lw=2.2, label=f"{name} {abc}")
        ax.set_title(title, fontsize=9.5, fontweight="bold")
        ax.set_xlim(lo, hi)
        ax.set_ylim(0, 1.55)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.legend(fontsize=7.5, loc="upper center", borderaxespad=0.2, ncol=1, frameon=True, framealpha=0.9, edgecolor=GRID)
        ax.set_ylabel(r"$\mu$")
    ax = axes[1, 1]
    for name, abc in bm.OUTPUT_SETS.items():
        xs, ys = _curve(abc, 0, 100)
        ax.plot(xs, ys, color=OUT_COLORS[name], lw=2.2, label=f"{name} {abc}")
    for t in (35, 65):
        ax.axvline(t, color=MUTED, ls=":", lw=1)
    ax.text(36, 1.04, "35", ha="left", fontsize=7.5, color=MUTED)
    ax.text(66, 1.04, "65", ha="left", fontsize=7.5, color=MUTED)
    ax.set_title("Output: Bunk Score (0-100)", fontsize=9.5, fontweight="bold")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.55)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.legend(fontsize=7.5, loc="upper center", borderaxespad=0.2, frameon=True, framealpha=0.9, edgecolor=GRID)
    ax.set_ylabel(r"$\mu$")
    fig.tight_layout(h_pad=1.6, w_pad=1.4)
    return _save(fig, out)


# ---------------------------------------------------------------- worked example
def fig_worked_fuzzification(out, values):
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.5), sharey=True)
    for ax, (name, cfg) in zip(axes, bm.INPUTS.items()):
        lo, hi = cfg["range"]
        x0 = values[name]
        for (sname, abc), col in zip(cfg["sets"].items(), SET_COLORS):
            xs, ys = _curve(abc, lo, hi)
            ax.plot(xs, ys, color=col, lw=2, label=sname)
            mu = bm.trimf(x0, *abc)
            if mu > 0:
                ax.plot([x0], [mu], "o", color=col, ms=7, zorder=5)
                ax.annotate(f"{mu:.3f}", (x0, mu), (0, 7), textcoords="offset points", ha="center",
                            fontsize=8.5, color=col, fontweight="bold")
        ax.axvline(x0, color=INK, ls="--", lw=1.1)
        ax.set_title(f"{name.capitalize()} = {x0:g}", fontsize=9, fontweight="bold")
        ax.set_xlim(lo, hi)
        ax.set_ylim(0, 1.2)
        ax.legend(fontsize=7, loc="upper left", ncol=3 if name != "temptation" else 2, frameon=False,
                  columnspacing=0.8, handlelength=1.2)
    axes[0].set_ylabel(r"membership $\mu$")
    fig.tight_layout(w_pad=1.0)
    return _save(fig, out)


def fig_aggregate(out, values, title_note, exact=None):
    fuzzy, fired, out_strength, xs, agg, score = bm.infer(values)
    fig, ax = plt.subplots(figsize=(6.6, 3.1))
    for name, abc in bm.OUTPUT_SETS.items():
        x2, y2 = _curve(abc, 0, 100)
        ax.plot(x2, y2, color=OUT_COLORS[name], lw=1.2, ls=":", label=f"{name} (unclipped)")
    ax.fill_between(xs, agg, color=INDIGO, alpha=0.22, label="aggregated output")
    ax.plot(xs, agg, color=INDIGO, lw=2.4)
    for name, s in out_strength.items():
        if s > 0:
            ax.axhline(s, color=OUT_COLORS[name], lw=0.9, ls="--", alpha=0.8)
            label = f"{name} clipped at {s:.3f}"
            if score > 80:  # keep the label left of the centroid line
                ax.text(score - 1.5, s + 0.03, label, fontsize=8, color=OUT_COLORS[name], ha="right", va="bottom")
            else:
                ax.text(99, s + 0.02 if s < 0.1 else s - 0.04, label, fontsize=8, color=OUT_COLORS[name],
                        ha="right", va="bottom" if s < 0.1 else "top")
    ax.axvline(score, color=INK, lw=2)
    ax.text(score - 1.2, 1.3, f"centroid = {score:.2f}", ha="right", fontsize=9, fontweight="bold")
    if exact is not None:
        ax.axvline(exact, color=INK, lw=1, ls=(0, (2, 2)))
        ax.text(exact + 1.2, 1.3, f"exact continuous = {exact:.2f}", ha="left", fontsize=8, color=MUTED)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 1.45)
    ax.set_xlabel("Bunk Score")
    ax.set_ylabel(r"membership $\mu$")
    ax.set_title(title_note, fontsize=9.5, fontweight="bold")
    ax.legend(fontsize=7.5, loc="upper left", bbox_to_anchor=(0.0, 0.8), frameon=True, framealpha=0.92, edgecolor=GRID)
    return _save(fig, out)


# ---------------------------------------------------------------- sensitivity
def fig_sensitivity(out):
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), sharey=True)
    att = np.linspace(0, 100, 401)
    for t, col in zip((2, 5, 8), (TEAL, AMBER, INDIGO)):
        axes[0].plot(att, [bm.infer({"attendance": a, "credits": 2.5, "temptation": t})[-1] for a in att],
                     color=col, lw=2, label=f"temptation = {t}")
    axes[0].axvline(bm.ATTENDANCE_MIN, color=RED, lw=1.2, ls="--")
    axes[0].text(bm.ATTENDANCE_MIN - 1.5, 3, "75% minimum", color=RED, fontsize=8, ha="right")
    axes[0].set_xlabel("Attendance (%)  (credits = 2.5)")
    axes[0].set_ylabel("Raw Bunk Score")
    axes[0].legend(fontsize=7.5, loc="upper left", frameon=True, framealpha=0.92, edgecolor=GRID)
    temp = np.linspace(0, 10, 201)
    for c, col, lw, ls in ((1, TEAL, 4.5, "-"), (2.5, INDIGO, 2, "-"), (4, AMBER, 2, (0, (3, 3)))):
        axes[1].plot(temp, [bm.infer({"attendance": 78, "credits": c, "temptation": t})[-1] for t in temp],
                     color=col, lw=lw, ls=ls, label=f"credits = {c:g}")
    axes[1].set_xlabel("Temptation to skip  (attendance = 78%)")
    axes[1].legend(fontsize=7.5, loc="upper left", frameon=True, framealpha=0.92, edgecolor=GRID)
    for ax in axes:
        ax.set_ylim(0, 100)
        for y in (35, 65):
            ax.axhline(y, color=MUTED, ls=":", lw=1)
        ax.text(ax.get_xlim()[1], 36, " 35", fontsize=7.5, color=MUTED, va="bottom", ha="right")
        ax.text(ax.get_xlim()[1], 66, " 65", fontsize=7.5, color=MUTED, va="bottom", ha="right")
    fig.tight_layout(w_pad=1.0)
    return _save(fig, out)


# ---------------------------------------------------------------- diagrams
def _box(ax, x, y, w, h, text, fc="#f4f2fd", ec=INDIGO, fs=8, bold=False, lw=1.2, tc=INK, style="round,pad=0.02,rounding_size=1.2"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style, fc=fc, ec=ec, lw=lw, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", zorder=3, linespacing=1.25)


def _arrow(ax, p, q, text=None, tpos=None, color=INK, ls="-", rad=0.0, fs=7.2, ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=10, color=color, lw=1.2, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}", zorder=4, shrinkA=0, shrinkB=0))
    if text:
        ax.text(*(tpos or ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 1)), text, fontsize=fs, color=color,
                ha=ha, va="bottom", zorder=5, linespacing=1.2)





def fig_architecture(out):
    fig, ax = plt.subplots(figsize=(7.0, 5.2))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 74)
    ax.axis("off")
    ax.grid(False)
    ax.add_patch(FancyBboxPatch((1, 2), 36, 66, boxstyle="round,pad=0.02,rounding_size=1.5", fc="#fbf8f2",
                                ec="#b9b1a2", lw=1.2, zorder=1))
    ax.text(19, 65.2, "Presentation layer", ha="center", fontsize=9.5, fontweight="bold", color=INK)
    ax.text(19, 62.2, "app.py (Streamlit + Plotly)", ha="center", fontsize=8, color=MUTED)
    ax.add_patch(FancyBboxPatch((58, 2), 41, 66, boxstyle="round,pad=0.02,rounding_size=1.5", fc="#f4f2fd",
                                ec=INDIGO, lw=1.4, zorder=1))
    ax.text(78.5, 65.2, "Fuzzy engine", ha="center", fontsize=9.5, fontweight="bold", color=INDIGO)
    ax.text(78.5, 62.2, "bunk_meter.py (NumPy)", ha="center", fontsize=8, color=MUTED)
    _box(ax, 6.5, 70, 25, 3.6, "Student (browser)", fc="white", ec="#8a857c", fs=8)
    _arrow(ax, (19, 70), (19, 68), color="#8a857c")
    _box(ax, 3.5, 45, 31, 13, "Input controls\nattendance, credits,\ntemptation sliders\n5 demo presets (session state)", fs=7.4)
    _box(ax, 3.5, 25, 31, 14, "Explainability tabs\nFuzzification, Active rules,\nAggregation & centroid,\nMembership graphs, Algorithm", fs=7.4)
    _box(ax, 3.5, 5, 31, 14, "Result views\nraw-score gauge, raw verdict,\nfinal-recommendation card,\n75% warning, explanation", fs=7.4)
    steps = ["validate_inputs()\nrange / NaN / type checks",
             "Fuzzification: trimf() over INPUTS\n8 input fuzzy sets",
             "Rule evaluation: 18 RULES\nstrength = min(att, cred, temp)",
             "Clip + aggregate (max)\nOUTPUT_SETS on 401-point grid",
             "defuzzify(): centroid\nzero-area fallback = 50",
             "verdict(): raw score to 3 bands\n(<35, 35 to <65, >=65)",
             "final_recommendation()\nhard 75% attendance rule"]
    h, gap, y0 = 6.2, 1.9, 54.0
    ys = []
    for i, s in enumerate(steps):
        y = y0 - i * (h + gap)
        ys.append(y)
        fc = "#fff3e6" if i == 6 else "white"
        ec = AMBER if i == 6 else INDIGO
        _box(ax, 60, y, 37, h, s, fc=fc, ec=ec, fs=7.1)
        if i:
            _arrow(ax, (78.5, ys[i - 1]), (78.5, y + h), color=INDIGO)
    _arrow(ax, (34.5, 51.5), (60, ys[0] + h / 2), text="values dict", tpos=(47.2, 57.0), color=INK)
    _arrow(ax, (60, ys[3] + h / 2), (34.5, 33), text="fuzzy, fired,\nout_strength,\nxs, agg", tpos=(47.2, 33.6), color=INK, ls="--")
    _arrow(ax, (60, ys[6] + h / 2), (34.5, 12), text="score, final\nrecommendation", tpos=(47.2, 3.6), color=INK)
    return _save(fig, out)


def fig_flowchart(out):
    fig, ax = plt.subplots(figsize=(6.6, 8.6))
    ax.set_xlim(0, 100)
    ax.axis("off")
    ax.grid(False)
    cx, w = 36, 52
    right_x, right_w = 70, 29
    gap = 3.4
    kinds = [  # (kind, height, text)
        ("term", 5, "START: attendance, credits, temptation"),
        ("dec", 11, "validate_inputs():\nall present, finite, in range?"),
        ("proc", 8, "1. Fuzzification\n8 membership degrees via trimf()"),
        ("proc", 9, "2. Rule evaluation, for each of the 18 rules:\ns = min(attendance, credits, temptation degrees)"),
        ("dec", 8, "s > 0 ?"),
        ("proc", 7.5, "Rule has fired: out_strength[output] =\nmax(out_strength[output], s)"),
        ("proc", 8, "3. Clip each output set at its strength;\naggregate by max on 401-point grid"),
        ("dec", 9, "aggregate area > 0 ?"),
        ("proc", 7, "4. Centroid: score = sum(x * mu) / sum(mu)"),
        ("dec", 9, "attendance < 75 ?"),
        ("proc", 7.5, "Raw verdict from score:\n<35 cannot skip | 35 to <65 caution | >=65 can skip"),
        ("term", 6, "Show raw score, raw verdict\nand final recommendation"),
    ]
    total = sum(k[1] for k in kinds) + gap * (len(kinds) - 1) + 2
    ax.set_ylim(0, total)
    y = total - 1
    pos = []
    for kind, h, text in kinds:
        y -= h
        pos.append((y, h))
        if kind == "term":
            _box(ax, cx - w / 2, y, w, h, text, fc="#ece9fb", ec=INDIGO, fs=7.8, bold=True, style="round,pad=0.02,rounding_size=2.5")
        elif kind == "proc":
            _box(ax, cx - w / 2, y, w, h, text, fc="white", ec=INDIGO, fs=7.5, style="square,pad=0.02")
        else:
            ww = 56 if h > 8.5 else 28
            ax.add_patch(Polygon([(cx - ww / 2, y + h / 2), (cx, y + h), (cx + ww / 2, y + h / 2), (cx, y)],
                                 closed=True, fc="#fff7e8", ec=AMBER, lw=1.2, zorder=2))
            ax.text(cx, y + h / 2, text, ha="center", va="center", fontsize=7.5, zorder=3, linespacing=1.2)
        y -= gap
    for i in range(len(kinds) - 1):
        (y1, h1), (y2, h2) = pos[i], pos[i + 1]
        label = None
        col = INK
        if kinds[i][0] == "dec":
            label, col = ("yes" if i != 9 else "no"), GREEN
        _arrow(ax, (cx, y1), (cx, y2 + h2), text=label, tpos=(cx + 1.2, y2 + h2 + 0.3), color=col, ha="left")
    # side branches
    (yv, hv) = pos[1]
    _box(ax, right_x, yv + hv / 2 - 4, right_w, 8, "raise ValueError\n(UI: st.error, st.stop)", fc="#fdf3f1", ec=RED, fs=7.2, style="square,pad=0.02")
    _arrow(ax, (cx + 28, yv + hv / 2), (right_x, yv + hv / 2), text="no", tpos=(cx + 30, yv + hv / 2 + 0.6), color=RED)
    (ys_, hs) = pos[4]
    ax.text(cx + 16, ys_ + hs / 2, "no: rule ignored", fontsize=7.2, color=MUTED, va="center")
    (ya, ha_) = pos[7]
    fb_y = ya + ha_ / 2 - 3.5
    _box(ax, right_x, fb_y, right_w, 7, "score = 50 (neutral\nfallback)", fc="#f6f6f6", ec="#8a857c", fs=7.2, style="square,pad=0.02")
    _arrow(ax, (cx + 28, ya + ha_ / 2), (right_x, ya + ha_ / 2), text="no", tpos=(cx + 30, ya + ha_ / 2 + 0.6), color=RED)
    (yc, hc) = pos[8]
    ax.plot([right_x + right_w / 2, right_x + right_w / 2], [fb_y, yc + hc / 2], color="#8a857c", lw=1.2, zorder=1)
    _arrow(ax, (right_x + right_w / 2, yc + hc / 2), (cx + w / 2, yc + hc / 2), color="#8a857c")
    (yp, hp) = pos[9]
    _box(ax, right_x, yp + hp / 2 - 5, right_w, 10, "Final recommendation:\nATTEND CLASS —\nBELOW MINIMUM\nATTENDANCE", fc="#fdf3f1", ec=RED, fs=7, style="square,pad=0.02")
    _arrow(ax, (cx + 28, yp + hp / 2), (right_x, yp + hp / 2), text="yes", tpos=(cx + 30, yp + hp / 2 + 0.6), color=RED)
    (yt, ht) = pos[11]
    ax.plot([right_x + right_w / 2, right_x + right_w / 2], [yp + hp / 2 - 5, yt + ht / 2], color=RED, lw=1.2, zorder=1)
    _arrow(ax, (right_x + right_w / 2, yt + ht / 2), (cx + w / 2, yt + ht / 2), color=RED)
    (yr, hr) = pos[10]
    ax.text(cx + w / 2 + 1.5, yr + hr / 2 + 0.2, "final = raw verdict", fontsize=7, color=MUTED, va="center", ha="left")
    return _save(fig, out)


def make_all(out_dir, ctx):
    p = lambda n: os.path.join(out_dir, n)  # noqa: E731
    os.makedirs(out_dir, exist_ok=True)
    dflt = {"attendance": 78, "credits": 2.5, "temptation": 8}
    ovr = {"attendance": 72, "credits": 2.5, "temptation": 9}
    return {
        "trimf": fig_trimf_shapes(p("fig_trimf_shapes.png")),
        "mfs": fig_membership_functions(p("fig_membership_functions.png")),
        "arch": fig_architecture(p("fig_architecture.png")),
        "flow": fig_flowchart(p("fig_flowchart.png")),
        "wfuzz": fig_worked_fuzzification(p("fig_worked_fuzzification.png"), dflt),
        "wagg": fig_aggregate(p("fig_worked_aggregate.png"), dflt,
                              "Attendance 78, credits 2.5, temptation 8", exact=ctx["exact_centroid"]),
        "oagg": fig_aggregate(p("fig_override_aggregate.png"), ovr, "Attendance 72, credits 2.5, temptation 9"),
        "sens": fig_sensitivity(p("fig_sensitivity.png")),
    }
