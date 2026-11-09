"""Streamlit dashboard for Smart City cybersecurity risk assessment.

Separate from the environmental monitoring UI in dashboard/app.py.
Uses the defensive analysis modules under security/ only.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from security.recommendations import get_recommendations_for_threat
from security.risk_calculator import (
    IMPACT_LABELS,
    PROBABILITY_LABELS,
    assess_all,
    summarize_assessments,
    with_updated_factors,
)
from security.threats import (
    get_threat_by_id,
    list_entry_points,
    list_protected_assets,
    list_trust_boundaries,
)

st.set_page_config(
    page_title="Smart City Security Risk Assessment",
    layout="wide",
    initial_sidebar_state="expanded",
)

LEVEL_COLORS = {
    "High": "#B42318",
    "Medium": "#B54708",
    "Low": "#027A48",
}


def _init_session_state() -> None:
    if "assessments" not in st.session_state:
        st.session_state.assessments = {
            item.threat_id: item for item in assess_all()
        }
    if "selected_threat_id" not in st.session_state:
        st.session_state.selected_threat_id = "T-01"


def _assessments_list() -> list[Any]:
    order = [item.threat_id for item in assess_all()]
    return [st.session_state.assessments[threat_id] for threat_id in order]


def _assessments_frame(assessments: list[Any]) -> pd.DataFrame:
    rows = [
        {
            "Threat ID": item.threat_id,
            "Threat name": item.threat_name,
            "Affected component": item.affected_component,
            "Probability": item.probability,
            "Impact": item.impact,
            "Risk score": item.risk_score,
            "Risk level": item.risk_level,
            "Assessment type": item.assessment_type,
        }
        for item in assessments
    ]
    return pd.DataFrame(rows)


def _render_overview(assessments: list[Any]) -> None:
    summary = summarize_assessments(assessments)
    st.subheader("Security Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total threats", summary["total_threats"])
    col2.metric("High risk", summary["high"])
    col3.metric("Medium risk", summary["medium"])
    col4.metric("Low risk", summary["low"])
    col5.metric("Highest score", summary["highest_score"])
    st.caption(
        "Scores use the teaching formula Risk = Probability × Impact. "
        "Initial values are illustrative estimates from static review, not a penetration test."
    )


def _render_architecture() -> None:
    st.subheader("Architecture Overview")
    left, right = st.columns([1.2, 1])

    with left:
        st.code(
            "Sensor Simulator\n"
            "       |\n"
            "       v\n"
            "MQTT Publisher  -->  Mosquitto Broker (:1883)\n"
            "                            |\n"
            "                            v\n"
            "                     MQTT Subscriber + validator\n"
            "                            |\n"
            "                            v\n"
            "                     SQLite (data/smartcity.db)\n"
            "                            |\n"
            "                            v\n"
            "                     Streamlit Monitoring UI (:8501)",
            language="text",
        )
        st.markdown(
            """
**Exposure notes (confirmed vs unverified):**
- MQTT anonymous access is **confirmed** in `tools/mosquitto/mosquitto.conf`
  (`allow_anonymous true`).
- No TLS listener is **confirmed absent** in the project broker config.
- Monitoring dashboard has **no application login** in `dashboard/app.py`.
- OS bind/firewall for ports `1883` / `8501` was **not dynamically verified**.
"""
        )

    with right:
        st.markdown("**Protected assets**")
        for asset in list_protected_assets():
            st.markdown(f"- `{asset.asset_id}` — {asset.name}")

        st.markdown("**Entry points**")
        for entry in list_entry_points():
            st.markdown(f"- `{entry.entry_id}` — {entry.name} ({entry.interface})")

        st.markdown("**Trust boundaries**")
        for boundary in list_trust_boundaries():
            st.markdown(f"- `{boundary.boundary_id}` — {boundary.name}")


def _render_threat_table(assessments: list[Any]) -> None:
    st.subheader("Threat Table")
    frame = _assessments_frame(assessments)

    def _color_level(level: str) -> str:
        color = LEVEL_COLORS.get(level, "#344054")
        return f"color: {color}; font-weight: 600"

    styler = frame.style.map(_color_level, subset=["Risk level"])
    st.dataframe(styler, use_container_width=True, hide_index=True)


def _build_risk_matrix_figure(selected: Any) -> go.Figure:
    """5×5 matrix: X = Impact, Y = Probability, cell = P×I."""
    z_values = [[prob * impact for impact in range(1, 6)] for prob in range(5, 0, -1)]
    text = [[str(value) for value in row] for row in z_values]

    fig = go.Figure(
        data=go.Heatmap(
            z=z_values,
            x=[f"{i}\n{IMPACT_LABELS[i]}" for i in range(1, 6)],
            y=[f"{PROBABILITY_LABELS[i]}\n{i}" for i in range(5, 0, -1)],
            text=text,
            texttemplate="%{text}",
            colorscale=[
                [0.0, "#DCFAE6"],
                [0.28, "#FEE4E2"],
                [0.56, "#FEF0C7"],
                [1.0, "#F04438"],
            ],
            showscale=True,
            colorbar={"title": "Score"},
            hovertemplate="Impact=%{x}<br>Probability=%{y}<br>Score=%{z}<extra></extra>",
        )
    )

    # Heatmap y is reversed (5..1). Marker uses categorical axis positions.
    fig.add_trace(
        go.Scatter(
            x=[f"{selected.impact}\n{IMPACT_LABELS[selected.impact]}"],
            y=[f"{PROBABILITY_LABELS[selected.probability]}\n{selected.probability}"],
            mode="markers+text",
            marker={
                "size": 18,
                "color": "rgba(0,0,0,0)",
                "line": {"width": 3, "color": "#101828"},
                "symbol": "square",
            },
            text=[selected.threat_id],
            textposition="top center",
            name="Selected threat",
            hovertemplate=(
                f"{selected.threat_id}: {selected.threat_name}<br>"
                f"P={selected.probability}, I={selected.impact}, "
                f"Score={selected.risk_score}<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title="Risk Matrix (Probability × Impact)",
        xaxis_title="Impact →",
        yaxis_title="Probability →",
        height=460,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
    )
    return fig


def _render_interactive_assessment(assessments: list[Any]) -> None:
    st.subheader("Interactive Risk Assessment")
    labels = {
        item.threat_id: f"{item.threat_id} — {item.threat_name}"
        for item in assessments
    }
    options = list(labels.keys())
    selected_id = st.selectbox(
        "Select a threat",
        options=options,
        format_func=lambda threat_id: labels[threat_id],
        index=options.index(st.session_state.selected_threat_id)
        if st.session_state.selected_threat_id in options
        else 0,
    )
    st.session_state.selected_threat_id = selected_id
    selected = st.session_state.assessments[selected_id]
    threat = get_threat_by_id(selected_id)

    left, right = st.columns([1, 1.2])

    with left:
        st.markdown(f"**{threat.threat_id}: {threat.name}**")
        st.write(threat.description)
        st.markdown(f"**Affected component:** {threat.affected_component}")
        st.markdown(f"**Scenario type:** `{threat.attack_scenario_type}`")
        with st.expander("Potential attack scenario"):
            st.write(threat.attack_scenario)
        with st.expander("Potential consequences"):
            st.write(threat.potential_consequences)
        with st.expander("Why the initial score was chosen"):
            st.write(selected.rationale)

        probability = st.slider(
            "Probability (1=Rare … 5=Very likely)",
            min_value=1,
            max_value=5,
            value=int(selected.probability),
            key=f"prob_{selected_id}",
        )
        impact = st.slider(
            "Impact (1=Negligible … 5=Critical)",
            min_value=1,
            max_value=5,
            value=int(selected.impact),
            key=f"impact_{selected_id}",
        )

        preview = with_updated_factors(selected, probability, impact)
        st.markdown(
            f"**Recalculated score:** `{preview.risk_score}` "
            f"→ **{preview.risk_level}** "
            f"({PROBABILITY_LABELS[probability]} × {IMPACT_LABELS[impact]})"
        )

        apply_col, reset_col, reset_all_col = st.columns(3)
        with apply_col:
            if st.button("Apply to session", use_container_width=True):
                st.session_state.assessments[selected_id] = preview
                st.rerun()
        with reset_col:
            if st.button("Reset threat", use_container_width=True):
                baseline = {
                    item.threat_id: item for item in assess_all()
                }[selected_id]
                st.session_state.assessments[selected_id] = baseline
                st.session_state.pop(f"prob_{selected_id}", None)
                st.session_state.pop(f"impact_{selected_id}", None)
                st.rerun()
        with reset_all_col:
            if st.button("Reset all", use_container_width=True):
                st.session_state.assessments = {
                    item.threat_id: item for item in assess_all()
                }
                for threat_id in list(labels):
                    st.session_state.pop(f"prob_{threat_id}", None)
                    st.session_state.pop(f"impact_{threat_id}", None)
                st.rerun()

        st.info(
            "Slider changes stay local until you click **Apply to session**. "
            "Nothing is written to disk unless you later export/commit separately."
        )

    with right:
        st.plotly_chart(
            _build_risk_matrix_figure(
                st.session_state.assessments[selected_id]
                if (
                    st.session_state.assessments[selected_id].probability == probability
                    and st.session_state.assessments[selected_id].impact == impact
                )
                else preview
            ),
            use_container_width=True,
        )
        level = (
            preview.risk_level
            if (
                probability != selected.probability or impact != selected.impact
            )
            else selected.risk_level
        )
        st.markdown(
            f"Selected cell highlight follows the current slider values. "
            f"Current classification colour target: "
            f"<span style='color:{LEVEL_COLORS[level]};font-weight:600'>{level}</span>.",
            unsafe_allow_html=True,
        )


def _render_recommendations(threat_id: str) -> None:
    st.subheader("Security Recommendations")
    pack = get_recommendations_for_threat(threat_id)
    st.markdown(f"**Threat:** `{pack.threat_id}` — {pack.threat_name}")
    st.caption(pack.residual_notes)

    existing_col, proposed_col = st.columns(2)

    with existing_col:
        st.markdown("#### Existing controls (verified in repo)")
        if not pack.existing_controls:
            st.warning("No confirmed existing controls mapped for this threat.")
        for control in pack.existing_controls:
            st.markdown(f"**{control.control_id}: {control.title}**")
            st.write(control.description)
            st.caption(
                f"Reduces: {', '.join(control.reduces)} · {control.how_it_helps}"
            )

    with proposed_col:
        st.markdown("#### Proposed improvements (not implemented by this app)")
        for control in pack.proposed_controls:
            st.markdown(f"**{control.control_id}: {control.title}**")
            st.write(control.description)
            st.caption(
                f"Reduces: {', '.join(control.reduces)} · {control.how_it_helps}"
            )


def main() -> None:
    _init_session_state()

    st.title("Smart City Cybersecurity Risk Assessment")
    st.caption(
        "Defensive threat modelling and illustrative risk scoring for the MQTT IoT project. "
        "This dashboard does not run attacks or change broker security settings."
    )

    assessments = _assessments_list()
    _render_overview(assessments)
    st.divider()
    _render_architecture()
    st.divider()
    _render_threat_table(assessments)
    st.divider()
    _render_interactive_assessment(assessments)
    st.divider()
    _render_recommendations(st.session_state.selected_threat_id)

    with st.sidebar:
        st.header("About")
        st.write(
            "Branch focus: `security-risk-assessment`. "
            "Environmental monitoring UI remains in `dashboard/app.py`."
        )
        st.write("Formula: **Risk Score = Probability × Impact**")
        st.write("Levels: Low 1–7 · Medium 8–14 · High 15–25")
        current = st.session_state.assessments[st.session_state.selected_threat_id]
        st.metric("Selected score", current.risk_score)
        st.metric("Selected level", current.risk_level)


if __name__ == "__main__":
    main()
