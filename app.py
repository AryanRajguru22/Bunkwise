"""BunkWise - Streamlit front end for the fuzzy-logic attendance decision-support tool.

All numbers shown here come from one call to bunk_meter.infer(); this file only
displays them.  Run with:  streamlit run app.py
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import bunk_meter as bm

st.set_page_config(page_title="BunkWise", page_icon="🎯", layout="wide")

st.markdown("<style>.block-container {padding-top: 2.2rem; max-width: 1250px;}</style>",
            unsafe_allow_html=True)

# Streamlit strips class attributes from markdown HTML, so these snippets use inline styles.
LABEL_STYLE = "font-size:.8rem;text-transform:uppercase;letter-spacing:.08em;opacity:.65"

# ---------------------------------------------------------------- inputs
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


# ---------------------------------------------------------------- header
st.markdown('<p style="font-size:2.6rem;font-weight:800;letter-spacing:-0.02em;margin:0">'
            'Bunk<span style="color:#8b7cf6">Wise</span></p>', unsafe_allow_html=True)
st.markdown('<p style="font-size:1.1rem;opacity:.85;margin:0">Skip the guesswork. Know your risk.</p>',
            unsafe_allow_html=True)
st.caption(
    "A fuzzy-logic (Mamdani) decision-support tool: it combines attendance, subject credits and "
    "temptation using 18 IF-THEN rules and explains how it reached its Bunk Score."
)
st.markdown('<span style="display:inline-block;padding:2px 12px;border-radius:999px;font-size:.78rem;'
            'border:1px solid #8b7cf6;color:#b4a9ff">Educational decision-support tool</span>',
            unsafe_allow_html=True)
st.write("")

left, right = st.columns([1, 1.25], gap="large")

with left:
    with st.container(border=True):
        st.subheader("1 · Your situation")
        st.slider("Attendance percentage", 0.0, 100.0, step=0.5, key="attendance", format="%.1f%%",
                  help="Your current attendance in this subject. The mandatory minimum is 75%.")
        st.slider("Subject credits", 1.0, 4.0, step=0.5, key="credits",
                  help="A proxy for how important the subject is: 1 = fragile (a missed class "
                       "hurts attendance fast), 4 = heavy (a lot of syllabus per class).")
        st.slider("Temptation to skip", 0.0, 10.0, step=0.5, key="temptation",
                  help="How strongly you want to skip this class: 0 = no temptation, 10 = very strong.")

    with st.container(border=True):
        st.subheader("Demo scenarios")
        st.caption("Illustrative examples, not validated academic or institutional recommendations. "
                   "Each button sets the sliders above and re-runs the same inference.")
        for label, att, cred, temp, note in PRESETS:
            st.button(label, key=f"preset_{label}", help=f"{note} (attendance {att:g}%, "
                      f"credits {cred:g}, temptation {temp:g})", width="stretch",
                      on_click=apply_preset, args=(att, cred, temp))

values = {name: st.session_state[name] for name in bm.INPUTS}

# ---------------------------------------------------------------- inference (single source of truth)
try:
    fuzzy, fired, out_strength, xs, agg, score = bm.infer(values)
except ValueError as err:  # sliders keep inputs valid; this guards against bad session state
    st.error(f"Invalid input: {err}")
    st.stop()

raw_text, raw_color = bm.verdict(score)  # raw fuzzy verdict, ignores the attendance policy
final_text, final_color = bm.final_recommendation(score, values["attendance"])
below_minimum = bm.below_attendance_minimum(values["attendance"])
fired = sorted(fired, reverse=True)  # strongest rule first

# ---------------------------------------------------------------- results
SET_COLORS = ["#6c8cff", "#b07cff", "#35c4a8"]
OUT_COLORS = {"attend": "#e5534b", "maybe": "#e3a03a", "bunk": "#3fb27f"}


def gauge(value):
    fig = go.Figure(go.Indicator(
        mode="gauge", value=value,
        gauge={"axis": {"range": [0, 100], "tickvals": [0, 35, 65, 100]},
               "bar": {"color": "#8b7cf6", "thickness": 0.3},
               "steps": [{"range": [0, 35], "color": "rgba(229,83,75,.35)"},
                         {"range": [35, 65], "color": "rgba(227,160,58,.35)"},
                         {"range": [65, 100], "color": "rgba(63,178,127,.35)"}]}))
    fig.update_layout(height=190, margin=dict(l=25, r=25, t=10, b=25), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def explanation():
    """Plain-English summary built from the real inference results."""
    if not fired:
        return "No rule fired, so the neutral fallback score was used."
    s, a, c, t, out = fired[0]
    text = (f"The strongest rule is **IF** attendance is *{a}* **AND** credits are *{c}* **AND** "
            f"temptation is *{t}* **THEN** *{out}* (firing strength {s:.2f}). ")
    if len(fired) > 1:
        text += f"{len(fired) - 1} other rule(s) also fired. "
    text += (f"Their clipped output sets were merged and the centroid of the merged shape is "
             f"**{score:.1f}**.")
    return text


with right:
    with st.container(border=True):
        st.subheader("2 · Result")
        # Raw fuzzy output: shown in a neutral colour so it is not mistaken for the final answer.
        st.markdown(f'<div style="{LABEL_STYLE}">Raw fuzzy Bunk Score</div>'
                    f'<p style="font-size:3.6rem;font-weight:800;line-height:1.05;margin:0">'
                    f'{score:.1f}<small style="font-size:1.1rem;font-weight:500;opacity:.6"> / 100</small></p>'
                    f'<p style="font-size:.95rem;margin:.1rem 0 0 0;opacity:.8">Fuzzy verdict (before the '
                    f'attendance rule): <b>{raw_text}</b></p>', unsafe_allow_html=True)
        st.plotly_chart(gauge(score), width="stretch", config={"displayModeBar": False})
        st.markdown(f'<div style="{LABEL_STYLE}">Final recommendation</div>'
                    f'<p style="font-size:1.6rem;font-weight:800;margin:.1rem 0 .4rem 0;color:{final_color}">'
                    f'{final_text}</p>', unsafe_allow_html=True)
        if below_minimum:
            st.error(f"**Below the mandatory {bm.ATTENDANCE_MIN}% attendance** (you are at "
                     f"{values['attendance']:g}%). The fuzzy engine gave {score:.1f} (\"{raw_text}\"), but "
                     "the mandatory attendance constraint overrides the final recommendation.")
        else:
            st.caption(f"Attendance is at or above {bm.ATTENDANCE_MIN}%, so the final recommendation "
                       "follows the fuzzy verdict. Note that 75% is a minimum, not a guarantee that "
                       "skipping another class is safe: BunkWise does not know your classes attended or held.")
        st.markdown(explanation())
        st.caption(f"The {bm.ATTENDANCE_MIN}% attendance requirement is a hard constraint applied after "
                   "fuzzy inference; it never changes the raw score. The Bunk Score is a fuzzy index from "
                   "0 to 100, not a probability. Higher = more tolerable to skip.")

# ---------------------------------------------------------------- explainability
st.write("")
st.subheader("3 · Why this result? (explainable fuzzy logic)")
tab_fuzz, tab_rules, tab_out, tab_graphs, tab_how = st.tabs(
    ["1 Fuzzification", "2 Active rules", "3 Aggregation & centroid", "Membership graphs", "How it works"])

with tab_fuzz:
    st.caption("Each crisp input is converted into a membership degree (0 to 1) in every fuzzy set "
               "using the triangular function trimf(x; a, b, c).")
    cols = st.columns(3)
    for col, (name, cfg) in zip(cols, bm.INPUTS.items()):
        with col:
            st.markdown(f"**{cfg['label']}**")
            st.markdown(f"Input value: `{values[name]:g}`")
            df = pd.DataFrame({
                "Fuzzy set": list(cfg["sets"]),
                "(a, b, c)": [str(abc) for abc in cfg["sets"].values()],
                "Membership": [fuzzy[name][s] for s in cfg["sets"]],
            })
            st.dataframe(df, hide_index=True, width="stretch", column_config={
                "Membership": st.column_config.ProgressColumn(
                    "Membership", min_value=0.0, max_value=1.0, format="%.3f")})

with tab_rules:
    st.caption(f"{len(fired)} of {len(bm.RULES)} rules have a firing strength above zero. "
               "Firing strength = min(attendance degree, credits degree, temptation degree).")
    if fired:
        rules_df = pd.DataFrame(fired, columns=["Strength", "Attendance", "Credits", "Temptation", "THEN output"])
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
    for col, (name, strength) in zip(cols, out_strength.items()):
        col.metric(f"'{name}' clip level", f"{strength:.3f}")
    cols[-1].metric("Centroid = Bunk Score", f"{score:.2f}")
    st.markdown(f"Centroid = Σ(x·μ) / Σμ = {(xs * agg).sum():.2f} / {agg.sum():.2f} = **{score:.2f}** "
                f"(401 sample points of the 0 to 100 output universe)")
    fig = go.Figure()
    for name, abc in bm.OUTPUT_SETS.items():
        fig.add_trace(go.Scatter(x=xs, y=[bm.trimf(x, *abc) for x in xs], mode="lines", name=name,
                                 line=dict(color=OUT_COLORS[name], width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=xs, y=agg, mode="lines", name="aggregated output", fill="tozeroy",
                             line=dict(color="#8b7cf6", width=2), fillcolor="rgba(139,124,246,.35)"))
    fig.add_vline(x=score, line_width=3, line_color=raw_color,
                  annotation_text=f"centroid {score:.1f}", annotation_position="top")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), xaxis_title="Bunk Score",
                      yaxis=dict(title="Membership", range=[0, 1.15]),
                      legend=dict(orientation="h", y=-0.25), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

with tab_graphs:
    st.caption("Dashed line = your current input. Dots show the membership degree in each set.")
    cols = st.columns(3)
    for col, (name, cfg) in zip(cols, bm.INPUTS.items()):
        lo, hi = cfg["range"]
        grid = [lo + (hi - lo) * i / 200 for i in range(201)]
        fig = go.Figure()
        for (set_name, abc), color in zip(cfg["sets"].items(), SET_COLORS):
            fig.add_trace(go.Scatter(x=grid, y=[bm.trimf(x, *abc) for x in grid], mode="lines",
                                     name=set_name, line=dict(color=color, width=2)))
            mu = fuzzy[name][set_name]
            if mu > 0:
                fig.add_trace(go.Scatter(x=[values[name]], y=[mu], mode="markers+text", showlegend=False,
                                         text=[f"{mu:.2f}"], textposition="top center",
                                         marker=dict(color=color, size=10)))
        fig.add_vline(x=values[name], line_dash="dash", line_color="#cfd3ff")
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=40, b=10),
                          title=dict(text=name.capitalize(), font=dict(size=14)),
                          yaxis=dict(range=[0, 1.25]), legend=dict(orientation="h", y=-0.2),
                          paper_bgcolor="rgba(0,0,0,0)")
        col.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

with tab_how:
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
        (BunkWise does not know how many classes you attended or were held).
        """
    )
