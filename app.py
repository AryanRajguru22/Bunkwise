"""BunkWise - Streamlit front end for the fuzzy-logic attendance decision-support tool.

All numbers shown here come from one call to bunk_meter.infer(); this file only
displays them.  Run with:  streamlit run app.py
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import bunk_meter as bm

st.set_page_config(page_title="BunkWise", page_icon=":material/target:", layout="wide")

# ---------------------------------------------------------------- look and feel
# Theme colours live in .streamlit/config.toml. The only custom CSS styles containers by their
# documented `key` class (st-key-card-*), not Streamlit's internal generated class names.
INK, MUTED, GRID, ACCENT = "#25232b", "#6b6760", "#ece6db", "#5b4bdb"
STATUS = {  # verdict text -> (status, icon, colour name used by Streamlit's :colour[] markdown)
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
      .block-container {max-width: 1180px; padding-top: 3.2rem; padding-bottom: 3rem;}
      [class*="st-key-card-"] {background: #fff; border: 1px solid #e4dccf; border-radius: 16px;
          padding: 1.25rem 1.5rem; box-shadow: 0 1px 2px rgba(37,35,43,.04), 0 6px 18px rgba(37,35,43,.04);}
      .st-key-card-final-danger {border-left: 6px solid #c5453e; background: #fdf3f1;}
      .st-key-card-final-caution {border-left: 6px solid #c98a1b; background: #fdf8ec;}
      .st-key-card-final-ok {border-left: 6px solid #2f8f62; background: #f1f9f4;}
    </style>
    """,
    unsafe_allow_html=True,
)


def chip(text, colour="#5b4bdb", bg="#efecfc"):
    """Small value badge (inline styles only: Streamlit strips class attributes from markdown HTML)."""
    return (f'<span style="background:{bg};color:{colour};border-radius:999px;padding:2px 12px;'
            f'font-weight:700;font-size:.95rem">{text}</span>')


def label_row(left, right_html):
    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'margin-top:.35rem"><span style="font-weight:700">{left}</span>{right_html}</div>',
                unsafe_allow_html=True)


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
st.markdown(
    '<div style="display:flex;align-items:center;gap:.9rem;flex-wrap:wrap">'
    '<span style="font-size:2.4rem;font-weight:800;letter-spacing:-0.02em;line-height:1.1">'
    'Bunk<span style="color:#5b4bdb">Wise</span></span>'
    + chip("Educational decision-support tool") + '</div>'
    '<div style="font-size:1.15rem;margin-top:.25rem;font-weight:500">Skip the guesswork. Know your risk.</div>',
    unsafe_allow_html=True)
st.caption("A fuzzy-logic (Mamdani) tool: it combines attendance, subject credits and temptation with "
           "18 IF-THEN rules and shows how it reached its Bunk Score.")
st.write("")

left, right = st.columns([5, 7], gap="large")

with left:
    with st.container(key="card-inputs", border=False):
        st.markdown("#### Your situation")
        att_now = st.session_state["attendance"]
        below_now = bm.below_attendance_minimum(att_now)
        label_row("Attendance",
                  chip(f"{att_now:.1f}%", "#a3322c", "#fbe4e1") if below_now else chip(f"{att_now:.1f}%"))
        st.slider("Attendance percentage", 0.0, 100.0, step=0.5, key="attendance",
                  format="%.1f%%", label_visibility="collapsed")
        st.caption(f"Your current attendance in this subject. The mandatory minimum is {bm.ATTENDANCE_MIN}%.")

        label_row("Subject credits", chip(f"{st.session_state['credits']:g}"))
        st.slider("Subject credits", 1.0, 4.0, step=0.5, key="credits", label_visibility="collapsed")
        st.caption("A proxy for how much one class matters: 1 = fragile (a miss hurts attendance fast), "
                   "4 = heavy (a lot of syllabus per class).")

        label_row("Temptation to skip", chip(f"{st.session_state['temptation']:g} / 10"))
        st.slider("Temptation to skip", 0.0, 10.0, step=0.5, key="temptation", label_visibility="collapsed")
        st.caption("How strongly you want to skip this class: 0 = not at all, 10 = very strongly.")

    with st.container(key="card-presets", border=False):
        st.markdown("#### Try a scenario")
        st.caption("Illustrative examples, not validated recommendations. Each one sets the sliders above "
                   "and runs the same inference.")
        for label, att, cred, temp, note in PRESETS:
            selected = (st.session_state["attendance"], st.session_state["credits"],
                        st.session_state["temptation"]) == (att, cred, temp)
            detail = f"{att:g}% · {cred:g} cr · temp {temp:g}"
            st.button(f"**{label}**  \n{detail}" if selected else f"**{label}**  \n:gray[{detail}]",
                      key=f"preset_{label}", help=note, width="stretch", on_click=apply_preset,
                      args=(att, cred, temp), type="primary" if selected else "secondary")

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

# ---------------------------------------------------------------- chart helpers
SET_COLORS = ["#5b4bdb", "#d08a1d", "#2a9d8f"]
OUT_COLORS = {"attend": "#c5453e", "maybe": "#d08a1d", "bunk": "#2f8f62"}


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
        number=dict(font=dict(size=58, color=INK), valueformat=".1f"),
        gauge={"axis": {"range": [0, 100], "tickvals": [0, 35, 65, 100],
                        "tickfont": {"size": 13, "color": MUTED}},
               "bar": {"color": ACCENT, "thickness": 0.3}, "bgcolor": "white", "borderwidth": 0,
               "steps": [{"range": [0, 35], "color": "rgba(197,69,62,.22)"},
                         {"range": [35, 65], "color": "rgba(208,138,29,.25)"},
                         {"range": [65, 100], "color": "rgba(47,143,98,.25)"}]}))
    return style(fig, 250, margin=dict(l=30, r=30, t=30, b=34))


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


# ---------------------------------------------------------------- results
status, icon, colour = STATUS[final_text]
with right:
    with st.container(key="card-score", border=False):
        st.markdown("#### Raw fuzzy Bunk Score")
        st.plotly_chart(gauge(score), width="stretch", config={"displayModeBar": False})
        st.markdown(f"Score **{score:.1f} / 100** · fuzzy verdict before the attendance rule: **{raw_text}**")
        st.caption(":red[■] below 35 cannot skip  ·  :orange[■] 35 to below 65 caution  ·  "
                   ":green[■] 65 and above can skip")

    with st.container(key=f"card-final-{status}", border=False):
        st.markdown("##### Final recommendation")
        st.markdown(f"### :{colour}[:material/{icon}: {final_text}]")
        st.markdown(SUPPORT[final_text])
        if below_minimum:
            st.error(f"**Below the mandatory {bm.ATTENDANCE_MIN}% attendance** (you are at "
                     f"{values['attendance']:g}%). The fuzzy engine gave {score:.1f} (\"{raw_text}\"), but "
                     "the mandatory attendance constraint overrides the final recommendation.")
        else:
            st.caption(f"Attendance is at or above {bm.ATTENDANCE_MIN}%, so the final recommendation "
                       "follows the fuzzy verdict. 75% is a minimum, not a guarantee that skipping another "
                       "class is safe: BunkWise does not know your classes attended or held.")

    with st.container(key="card-why", border=False):
        st.markdown("##### Why this score?")
        st.markdown(explanation())
        st.caption(f"The {bm.ATTENDANCE_MIN}% attendance requirement is a hard constraint applied after fuzzy "
                   "inference; it never changes the raw score. The Bunk Score is a fuzzy index from 0 to 100, "
                   "not a probability. Higher = more tolerable to skip.")

# ---------------------------------------------------------------- explainability
st.write("")
with st.container(key="card-explain", border=False):
    st.markdown("### How the score was calculated")
    tab_fuzz, tab_rules, tab_out, tab_graphs, tab_how = st.tabs(
        ["Fuzzification", "Active rules", "Aggregation & centroid", "Membership graphs", "Algorithm"])

    with tab_fuzz:
        st.caption("Each crisp input is converted into a membership degree (0 to 1) in every fuzzy set "
                   "using the triangular function trimf(x; a, b, c).")
        cols = st.columns(3, gap="large")
        for col, (name, cfg) in zip(cols, bm.INPUTS.items()):
            with col:
                st.markdown(f"**{cfg['label']}**")
                st.markdown(f"Input value: `{values[name]:g}`")
                df = pd.DataFrame({
                    "Fuzzy set": list(cfg["sets"]),
                    "Membership": [fuzzy[name][s] for s in cfg["sets"]],
                })
                st.dataframe(df, hide_index=True, width="stretch", column_config={
                    "Membership": st.column_config.ProgressColumn(
                        "Membership", min_value=0.0, max_value=1.0, format="%.3f")})
                st.caption("(a, b, c): " + " · ".join(f"{s} {abc}" for s, abc in cfg["sets"].items()))

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
                                     line=dict(color=OUT_COLORS[name], width=2, dash="dot")))
        fig.add_trace(go.Scatter(x=xs, y=agg, mode="lines", name="aggregated output", fill="tozeroy",
                                 line=dict(color=ACCENT, width=3), fillcolor="rgba(91,75,219,.22)"))
        fig.add_vline(x=score, line_width=3, line_color=INK,
                      annotation_text=f"centroid {score:.1f}", annotation_position="top")
        style(fig, 360, margin=dict(l=10, r=10, t=40, b=10), xaxis_title="Bunk Score",
              yaxis=dict(title="Membership", range=[0, 1.15], gridcolor=GRID),
              legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    with tab_graphs:
        st.caption("Dashed line = your current input. Dots show the membership degree in each set.")
        cols = st.columns(3, gap="large")
        for col, (name, cfg) in zip(cols, bm.INPUTS.items()):
            lo, hi = cfg["range"]
            grid_x = [lo + (hi - lo) * i / 200 for i in range(201)]
            fig = go.Figure()
            for (set_name, abc), color in zip(cfg["sets"].items(), SET_COLORS):
                fig.add_trace(go.Scatter(x=grid_x, y=[bm.trimf(x, *abc) for x in grid_x], mode="lines",
                                         name=set_name, line=dict(color=color, width=3)))
                mu = fuzzy[name][set_name]
                if mu > 0:
                    fig.add_trace(go.Scatter(x=[values[name]], y=[mu], mode="markers+text", showlegend=False,
                                             text=[f"{mu:.2f}"], textposition="top center",
                                             marker=dict(color=color, size=11)))
            fig.add_vline(x=values[name], line_dash="dash", line_color=INK)
            style(fig, 320, margin=dict(l=10, r=10, t=44, b=10),
                  title=dict(text=name.capitalize(), font=dict(size=15)),
                  yaxis=dict(range=[0, 1.25], gridcolor=GRID),
                  legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center", font=dict(size=11)))
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
