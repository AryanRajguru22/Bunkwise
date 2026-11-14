"""BunkWise - Streamlit front end for the fuzzy-logic attendance decision-support tool.

All numbers shown here come from bunk_meter.evaluate() (the Mamdani engine plus the separate 75%
attendance-policy step); this file only displays them.  Run with:  streamlit run app.py
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import bunk_meter as bm
import insights

st.set_page_config(page_title="BunkWise - attendance decision support", page_icon=":material/target:",
                   layout="wide")

# ---------------------------------------------------------------- look and feel
# Theme colours live in .streamlit/config.toml. The custom CSS only targets containers by their
# documented `key` class (st-key-*), never Streamlit's generated class names.
INK, MUTED, GRID, ACCENT = "#25232b", "#6b6760", "#ece6db", "#5b4bdb"
STATUS = {  # final recommendation -> (status, icon, colour name for Streamlit's :colour[] markdown)
    "CANNOT SKIP THE CLASS!!": ("danger", "block", "red"),
    "PROCEED WITH CAUTION": ("caution", "warning", "orange"),
    "CAN SKIP THE CLASS": ("ok", "check_circle", "green"),
    bm.BELOW_MINIMUM_TEXT: ("danger", "block", "red"),
}
SUPPORT = {  # one concise line under the final recommendation
    "CANNOT SKIP THE CLASS!!": "The fuzzy rules rate this class as too important to miss.",
    "PROCEED WITH CAUTION": "Mixed signals: skipping carries real risk, so think it through.",
    "CAN SKIP THE CLASS": "The rules rate skipping as tolerable here, but it is never guaranteed safe.",
    bm.BELOW_MINIMUM_TEXT: "Your attendance is under the mandatory minimum, so attending is the only recommendation.",
}

st.markdown(
    """
    <style>
      .block-container {max-width: 1180px; padding-top: 3rem; padding-bottom: 3rem;}
      [class*="st-key-card-"] {background: #fff; border: 1px solid #e4dccf; border-radius: 16px;
          padding: 1.25rem 1.5rem; box-shadow: 0 1px 2px rgba(37,35,43,.04), 0 6px 18px rgba(37,35,43,.04);}
      .st-key-card-final-danger {border-left: 6px solid #c5453e; background: #fdf3f1;}
      .st-key-card-final-caution {border-left: 6px solid #c98a1b; background: #fdf8ec;}
      .st-key-card-final-ok {border-left: 6px solid #2f8f62; background: #f1f9f4;}
      .bw-brand {font-size: 2.4rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1;}
      @media (max-width: 640px) {
        .block-container {padding: 1.4rem .85rem 2rem;}
        [class*="st-key-card-"] {padding: .9rem 1rem;}
        .bw-brand {font-size: 1.9rem;}
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def chip(text, colour="#5b4bdb", bg="#efecfc"):
    """Small value badge. Only ever called with numbers and fixed words, never user-typed text."""
    return (f'<span style="background:{bg};color:{colour};border-radius:999px;padding:2px 12px;'
            f'font-weight:700;font-size:.95rem;white-space:nowrap">{text}</span>')


def label_row(left, right_html):
    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;gap:.5rem;'
                f'margin-top:.35rem"><span style="font-weight:700">{left}</span>{right_html}</div>',
                unsafe_allow_html=True)


def attendance_status(att):
    """One-line policy status under the attendance slider (text plus icon, never colour alone)."""
    m = bm.ATTENDANCE_MIN
    if att < m:
        st.markdown(f":red[:material/block: **Below the {m}% minimum.** The policy step will always say attend.]")
    else:
        st.markdown(f":green[:material/check_circle: **At or above the {m}% minimum.**] "
                    "The fuzzy verdict decides.")


def top_set(memberships):
    return max(memberships, key=memberships.get)


# ---------------------------------------------------------------- inputs and scenarios
DEFAULTS = {"attendance": 78.0, "credits": 2.5, "temptation": 8.0}  # same as bunk_meter.py

# Illustrative examples only: (button label, attendance, credits, temptation, what it shows)
PRESETS = [
    ("Balanced buffer", 78.0, 2.5, 8.0, "Default demo: 2.5 credits, 78% attendance, high temptation."),
    ("Comfortable, heavy subject", 90.0, 4.0, 2.0, "Plenty of buffer, but a 4-credit subject and low temptation."),
    ("Low attendance", 50.0, 4.0, 3.0, "Far below 75% in a heavy subject."),
    ("Below 75%, score still high", 72.0, 2.5, 9.0,
     "Raw fuzzy score is high, but below the mandatory 75% the final recommendation is ATTEND."),
    ("Easy subject, very safe", 95.0, 1.0, 9.0, "High attendance, but a 1-credit subject is fragile."),
]

for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def apply_preset(attendance, credits, temptation):
    """Button callback: write the preset into the slider state (runs before the sliders are drawn)."""
    st.session_state.update(attendance=attendance, credits=credits, temptation=temptation)


# ---------------------------------------------------------------- inference (single source of truth)
# Sliders read their value from st.session_state, which is already current when the script reruns,
# so the engine can run once here and feed both the inputs panel and the results.
try:
    ev = bm.evaluate(st.session_state["attendance"], st.session_state["credits"],
                     st.session_state["temptation"])
except ValueError as err:  # sliders keep inputs valid; this guards against bad session state
    st.error(f"Invalid input: {err}")
    if st.button("Reset to defaults"):
        st.session_state.update(DEFAULTS)
        st.rerun()
    st.stop()

# ---------------------------------------------------------------- header
st.markdown(
    '<div style="display:flex;align-items:center;gap:.9rem;flex-wrap:wrap">'
    '<span class="bw-brand">Bunk<span style="color:#5b4bdb">Wise</span></span>'
    + chip("Educational decision-support tool") + '</div>'
    '<div style="font-size:1.15rem;margin-top:.25rem;font-weight:500">Skip the guesswork. Know your risk.</div>',
    unsafe_allow_html=True)
st.caption("Enter your attendance, the subject's credits and how tempted you are. A fuzzy-logic (Mamdani) "
           "system with 18 IF-THEN rules gives a Bunk Score, and a separate rule enforces the mandatory "
           f"{bm.ATTENDANCE_MIN}% attendance.")
st.write("")

left, right = st.columns([5, 7], gap="large")

with left:
    with st.container(key="card-inputs", border=False):
        st.markdown("#### Your situation")
        below_now = ev.below_minimum
        label_row("Attendance",
                  chip(f"{ev.attendance:.1f}% · below {bm.ATTENDANCE_MIN}%", "#a3322c", "#fbe4e1") if below_now
                  else chip(f"{ev.attendance:.1f}%"))
        st.slider("Attendance percentage", 0.0, 100.0, step=0.5, key="attendance",
                  format="%.1f%%", label_visibility="collapsed")
        attendance_status(ev.attendance)
        st.caption("Your current attendance in this subject, from your attendance record.")

        label_row("Subject credits", chip(f"{ev.credits:g} · {top_set(ev.fuzzy['credits'])}"))
        st.slider("Subject credits", 1.0, 4.0, step=0.5, key="credits", label_visibility="collapsed")
        st.caption("How much one class weighs in this model: 1 = fragile (a miss hurts attendance fast), "
                   "2-3 = moderate, 4 = heavy (a lot of syllabus per class). Half-credit steps sit between sets.")

        label_row("Temptation to skip", chip(f"{ev.temptation:g} / 10 · {top_set(ev.fuzzy['temptation'])}"))
        st.slider("Temptation to skip", 0.0, 10.0, step=0.5, key="temptation", label_visibility="collapsed")
        st.caption("How strongly you want to skip this class: 0 = not at all, 10 = very strongly. "
                   "It is self-reported, so be honest with yourself.")

    with st.expander("Try an example scenario (5)"):
        st.caption("Illustrative examples, not validated recommendations. Each one sets the sliders above "
                   "and runs the same inference.")
        for label, att, cred, temp, note in PRESETS:
            selected = (ev.attendance, ev.credits, ev.temptation) == (att, cred, temp)
            detail = f"{att:g}% · {cred:g} cr · temp {temp:g}"
            st.button(f"**{label}**  \n{detail}" if selected else f"**{label}**  \n:gray[{detail}]",
                      key=f"preset_{label}", help=note, width="stretch", on_click=apply_preset,
                      args=(att, cred, temp), type="primary" if selected else "secondary")

# ---------------------------------------------------------------- chart helpers
SET_COLORS = ["#5b4bdb", "#d08a1d", "#2a9d8f"]
OUT_COLORS = {"attend": "#c5453e", "maybe": "#d08a1d", "bunk": "#2f8f62"}
NO_BAR = {"displayModeBar": False}


def style(fig, height, **layout):
    """Shared light chart styling: transparent background, readable fonts, soft grid."""
    fig.update_layout(height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=INK, size=13), **layout)
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    return fig


def gauge(value):
    """Score gauge: the number is the actual raw fuzzy score; bands follow the 35 / 65 thresholds."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number=dict(font=dict(size=54, color=INK), valueformat=".1f"),
        gauge={"axis": {"range": [0, 100], "tickvals": [0, 35, 65, 100],
                        "tickfont": {"size": 13, "color": MUTED}},
               "bar": {"color": ACCENT, "thickness": 0.3}, "bgcolor": "white", "borderwidth": 0,
               "steps": [{"range": [0, 35], "color": "rgba(197,69,62,.22)"},
                         {"range": [35, 65], "color": "rgba(208,138,29,.25)"},
                         {"range": [65, 100], "color": "rgba(47,143,98,.25)"}]}))
    return style(fig, 220, margin=dict(l=36, r=40, t=16, b=24))


@st.cache_data(show_spinner=False)
def input_curves(name):
    """Membership curves of one input (static, so computed once): (x grid, {set: y values})."""
    lo, hi = bm.INPUTS[name]["range"]
    grid_x = [lo + (hi - lo) * i / 200 for i in range(201)]
    return grid_x, {s: [bm.trimf(x, *abc) for x in grid_x] for s, abc in bm.INPUTS[name]["sets"].items()}


# ---------------------------------------------------------------- results
status, icon, colour = STATUS[ev.final_text]
with right:
    with st.container(key=f"card-final-{status}", border=False):
        st.markdown("##### Final recommendation")
        st.markdown(f"### :{colour}[:material/{icon}: {ev.final_text}]")
        st.markdown(SUPPORT[ev.final_text])
        if ev.below_minimum:
            st.error(f"**Below the mandatory {bm.ATTENDANCE_MIN}% attendance** (you are at "
                     f"{ev.attendance:g}%). The fuzzy engine gave {ev.score:.1f} (\"{ev.raw_verdict}\"), but "
                     "the mandatory attendance constraint overrides the final recommendation.")
        else:
            st.caption(f"Attendance is at or above {bm.ATTENDANCE_MIN}%, so the final recommendation "
                       "follows the fuzzy verdict. 75% is a minimum, not a guarantee that skipping another "
                       "class is safe: BunkWise does not know your classes attended or held.")

    with st.container(key="card-score", border=False):
        st.markdown("#### Raw fuzzy Bunk Score")
        st.plotly_chart(gauge(ev.score), width="stretch", config=NO_BAR)
        st.markdown(f"Score **{ev.score:.1f} / 100** · fuzzy verdict before the attendance rule: "
                    f"**{ev.raw_verdict}**")
        st.caption(":red[■] below 35 cannot skip  ·  :orange[■] 35 to below 65 caution  ·  "
                   ":green[■] 65 and above can skip. The score is a fuzzy index, not a probability.")
        st.download_button("Download decision report", data=insights.build_report(ev),
                           file_name="bunkwise_report.md", mime="text/markdown",
                           icon=":material/download:", on_click="ignore")

# ---------------------------------------------------------------- details
values = {"attendance": ev.attendance, "credits": ev.credits, "temptation": ev.temptation}
st.write("")
with st.container(key="card-explain", border=False):
    tab_why, tab_what, tab_cmp, tab_engine, tab_about = st.tabs(
        ["Why this result", "What if?", "Compare subjects", "Inside the engine", "About & limits"])

    # ---- plain-English explanation
    with tab_why:
        st.caption("A step-by-step reading of this result, generated from the actual inference.")
        for step in insights.explain(ev):
            st.markdown(step)
        st.caption(f"The {bm.ATTENDANCE_MIN}% attendance requirement is a hard constraint applied after fuzzy "
                   "inference; it never changes the raw score.")

    # ---- sensitivity to attendance
    with tab_what:
        st.caption("Raw fuzzy score as attendance changes, keeping your current credits and temptation. "
                   "Below the red line the final recommendation is always ATTEND, whatever the score.")
        sweep = insights.attendance_sweep(ev.credits, ev.temptation)
        fig = go.Figure()
        fig.add_vrect(x0=0, x1=bm.ATTENDANCE_MIN, fillcolor="rgba(197,69,62,.10)", line_width=0,
                      annotation_text="policy: always attend", annotation_position="top left")
        fig.add_hline(y=35, line_dash="dot", line_color=MUTED)
        fig.add_hline(y=65, line_dash="dot", line_color=MUTED)
        fig.add_trace(go.Scatter(x=[r["attendance"] for r in sweep], y=[r["score"] for r in sweep],
                                 mode="lines", name="raw fuzzy score", line=dict(color=ACCENT, width=3)))
        fig.add_trace(go.Scatter(x=[ev.attendance], y=[ev.score], mode="markers+text", name="you are here",
                                 text=[f"{ev.score:.1f}"], textposition="top center",
                                 marker=dict(color=INK, size=12)))
        style(fig, 340, margin=dict(l=10, r=10, t=30, b=10), xaxis_title="Attendance (%)",
              yaxis=dict(title="Raw Bunk Score", range=[0, 105], gridcolor=GRID),
              legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig, width="stretch", config=NO_BAR)
        for target, meaning in ((35, "proceed with caution"), (65, "can skip")):
            first = insights.attendance_for_verdict(ev.credits, ev.temptation, target)
            if first is None:
                st.markdown(f"- With {ev.credits:g} credits and temptation {ev.temptation:g}, the raw score "
                            f"does not reach {target} (*{meaning}*) at any attendance from "
                            f"{bm.ATTENDANCE_MIN}% to 100%.")
            elif first == bm.ATTENDANCE_MIN:
                st.markdown(f"- With {ev.credits:g} credits and temptation {ev.temptation:g}, the raw score is "
                            f"already {target} or more (*{meaning}*) at the {bm.ATTENDANCE_MIN}% minimum.")
            else:
                st.markdown(f"- With {ev.credits:g} credits and temptation {ev.temptation:g}, the raw score first "
                            f"reaches {target} (*{meaning}*) at about {first:g}% attendance.")
        st.caption("These readings come from the fuzzy model, which is hand-designed. They are not a promise.")

    # ---- several subjects at once
    with tab_cmp:
        st.caption(f"Compare up to {insights.MAX_SUBJECTS} subjects side by side. Each row runs the same "
                   "inference and the same 75% rule. Edits stay in this browser session only.")
        subjects = pd.DataFrame({
            "name": ["Subject A", "Subject B", "Subject C"],
            "attendance": [78.0, 90.0, 72.0], "credits": [2.5, 4.0, 2.0], "temptation": [8.0, 2.0, 9.0]})
        edited = st.data_editor(
            subjects, key="subjects_editor", num_rows="dynamic", hide_index=True, width="stretch",
            column_config={
                "name": st.column_config.TextColumn("Subject", max_chars=insights.MAX_NAME_LENGTH),
                "attendance": st.column_config.NumberColumn("Attendance %", min_value=0.0, max_value=100.0,
                                                            step=0.5, format="%.1f"),
                "credits": st.column_config.NumberColumn("Credits", min_value=1.0, max_value=4.0, step=0.5,
                                                         format="%g"),
                "temptation": st.column_config.NumberColumn("Temptation", min_value=0.0, max_value=10.0,
                                                            step=0.5, format="%g")})
        results = insights.compare_subjects(edited.to_dict("records"))
        if len(edited) > insights.MAX_SUBJECTS:
            st.caption(f"Only the first {insights.MAX_SUBJECTS} rows are evaluated.")
        if results:
            st.dataframe(
                pd.DataFrame([{"Subject": r["name"], "Raw score": r["score"], "Raw fuzzy verdict": r["raw_verdict"],
                               "Final recommendation": r["final"]} for r in results]),
                hide_index=True, width="stretch",
                column_config={"Raw score": st.column_config.ProgressColumn(
                    "Raw score", min_value=0.0, max_value=100.0, format="%.1f")})
            if any(not r["valid"] for r in results):
                st.caption("Rows marked 'Check inputs' have a missing or out-of-range value.")
        else:
            st.caption("Add a row to start comparing.")

    # ---- how the engine got there
    with tab_engine:
        tab_fuzz, tab_rules, tab_out, tab_graphs = st.tabs(
            ["Fuzzification", "Active rules", "Aggregation & centroid", "Membership graphs"])

        with tab_fuzz:
            st.caption("Each crisp input is converted into a membership degree (0 to 1) in every fuzzy set "
                       "using the triangular function trimf(x; a, b, c).")
            cols = st.columns(3, gap="large")
            for col, (name, cfg) in zip(cols, bm.INPUTS.items()):
                with col:
                    st.markdown(f"**{cfg['label']}**")
                    st.markdown(f"Input value: `{values[name]:g}`")
                    df = pd.DataFrame({"Fuzzy set": list(cfg["sets"]),
                                       "Membership": [ev.fuzzy[name][s] for s in cfg["sets"]]})
                    st.dataframe(df, hide_index=True, width="stretch", column_config={
                        "Membership": st.column_config.ProgressColumn(
                            "Membership", min_value=0.0, max_value=1.0, format="%.3f")})
                    st.caption("(a, b, c): " + " · ".join(f"{s} {abc}" for s, abc in cfg["sets"].items()))

        with tab_rules:
            st.caption(f"{len(ev.fired)} of {len(bm.RULES)} rules have a firing strength above zero. "
                       "Firing strength = min(attendance degree, credits degree, temptation degree).")
            if ev.fired:
                rules_df = pd.DataFrame(ev.fired, columns=["Strength", "Attendance", "Credits", "Temptation",
                                                           "THEN output"])
                st.dataframe(rules_df, hide_index=True, width="stretch", column_config={
                    "Strength": st.column_config.ProgressColumn("Firing strength", min_value=0.0,
                                                                max_value=1.0, format="%.3f")})
            with st.expander("Show the full rule base (18 rules)"):
                st.dataframe(pd.DataFrame(bm.RULES, columns=["Attendance", "Credits", "Temptation", "THEN output"]),
                             hide_index=True, width="stretch")

        with tab_out:
            st.caption("Each output set is clipped at the strongest rule pointing to it; the clipped sets are "
                       "merged with max; the centroid of the merged shape is the Bunk Score.")
            cols = st.columns(len(bm.OUTPUT_SETS) + 1)
            for col, (name, strength) in zip(cols, ev.out_strength.items()):
                col.metric(f"'{name}' clip level", f"{strength:.3f}")
            cols[-1].metric("Centroid = Bunk Score", f"{ev.score:.2f}")
            st.markdown(f"Centroid = Σ(x·μ) / Σμ = {(ev.xs * ev.agg).sum():.2f} / {ev.agg.sum():.2f} = "
                        f"**{ev.score:.2f}** (401 sample points of the 0 to 100 output universe)")
            fig = go.Figure()
            for name in bm.OUTPUT_SETS:
                fig.add_trace(go.Scatter(x=bm.OUTPUT_XS, y=bm.OUTPUT_SHAPES[name], mode="lines", name=name,
                                         line=dict(color=OUT_COLORS[name], width=2, dash="dot")))
            fig.add_trace(go.Scatter(x=ev.xs, y=ev.agg, mode="lines", name="aggregated output", fill="tozeroy",
                                     line=dict(color=ACCENT, width=3), fillcolor="rgba(91,75,219,.22)"))
            fig.add_vline(x=ev.score, line_width=3, line_color=INK,
                          annotation_text=f"centroid {ev.score:.1f}", annotation_position="top")
            style(fig, 360, margin=dict(l=10, r=10, t=40, b=10), xaxis_title="Bunk Score",
                  yaxis=dict(title="Membership", range=[0, 1.15], gridcolor=GRID),
                  legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig, width="stretch", config=NO_BAR)

        with tab_graphs:
            st.caption("Dashed line = your current input. Dots show the membership degree in each set.")
            cols = st.columns(3, gap="large")
            for col, name in zip(cols, bm.INPUTS):
                grid_x, curves = input_curves(name)
                fig = go.Figure()
                for (set_name, ys), color in zip(curves.items(), SET_COLORS):
                    fig.add_trace(go.Scatter(x=grid_x, y=ys, mode="lines", name=set_name,
                                             line=dict(color=color, width=3)))
                    mu = ev.fuzzy[name][set_name]
                    if mu > 0:
                        fig.add_trace(go.Scatter(x=[values[name]], y=[mu], mode="markers+text", showlegend=False,
                                                 text=[f"{mu:.2f}"], textposition="top center",
                                                 marker=dict(color=color, size=11)))
                fig.add_vline(x=values[name], line_dash="dash", line_color=INK)
                style(fig, 320, margin=dict(l=10, r=10, t=44, b=10),
                      title=dict(text=name.capitalize(), font=dict(size=15)),
                      yaxis=dict(range=[0, 1.25], gridcolor=GRID),
                      legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center", font=dict(size=11)))
                col.plotly_chart(fig, width="stretch", config=NO_BAR)

    # ---- algorithm, limits, privacy
    with tab_about:
        st.markdown(
            """
            **Mamdani fuzzy inference in four steps, then one policy check**

            1. **Fuzzification** – each crisp input gets a membership degree in every fuzzy set
               (for example attendance 78% is *ok* to degree 1.0 and *danger*/*safe* to 0).
            2. **Rule evaluation** – every IF–THEN rule is scored with the *minimum* of its three
               antecedent degrees (fuzzy AND). Rules with strength 0 are ignored.
            3. **Aggregation** – each output set (*attend*, *maybe*, *bunk*) is clipped at its strongest
               rule, and the clipped shapes are combined with *maximum*.
            4. **Defuzzification** – the *centroid* (centre of area) of the combined shape is the raw
               Bunk Score. Fuzzy verdict: below 35 → cannot skip, 35 to below 65 → proceed with caution,
               65 or more → can skip.
            5. **Attendance rule (not fuzzy)** – the mandatory 75% attendance is a hard constraint applied
               *after* defuzzification. Below 75% the final recommendation is always **ATTEND CLASS —
               BELOW MINIMUM ATTENDANCE**, whatever the score; at 75% or above the fuzzy verdict is used.
               The raw score is never changed.

            **Limits:** the sets and rules were written by hand, not learned from data. The score is an
            index, not a probability, and 75% is a minimum, not a guarantee that skipping is safe
            (BunkWise does not know how many classes you attended or were held). Credits are only a proxy
            for how much a class matters, and temptation is self-reported.

            **Privacy:** BunkWise has no accounts and no database. What you enter lives only in your
            browser session while the page is open and is not saved or shared.
            """
        )

st.caption(insights.DISCLAIMER)
