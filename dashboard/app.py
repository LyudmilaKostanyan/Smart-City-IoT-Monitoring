"""Streamlit Digital Twin dashboard for Smart City districts."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "database"))

from digital_twin import (  # noqa: E402
    DecisionEngine,
    DigitalTwinStateManager,
    ScenarioInputs,
    SimulationEngine,
)

st.set_page_config(
    page_title="Smart City Digital Twin",
    layout="wide",
)


def _default_scenario_values(district_state: dict) -> tuple[float, float, float]:
    temperature = district_state.get("temperature")
    humidity = district_state.get("humidity")
    air_quality = district_state.get("air_quality")
    return (
        float(temperature) if temperature is not None else 25.0,
        float(humidity) if humidity is not None else 50.0,
        float(air_quality) if air_quality is not None else 40.0,
    )


def main() -> None:
    st.title("Smart City Digital Twin")
    st.caption(
        "Yerevan districts: Kentron, Arabkir, Shengavit. "
        "Baseline values come from MQTT → SQLite. "
        "Simulation values are hypothetical and do not overwrite sensor data."
    )

    if "simulation_engine" not in st.session_state:
        st.session_state.simulation_engine = SimulationEngine()
    if "decision_engine" not in st.session_state:
        st.session_state.decision_engine = DecisionEngine()
    if "scenario_result" not in st.session_state:
        st.session_state.scenario_result = None
    if "decision_result" not in st.session_state:
        st.session_state.decision_result = None

    manager = DigitalTwinStateManager()
    try:
        manager.refresh()
        snapshot = manager.snapshot()
        twins = manager.twins
    finally:
        manager.close()

    st.markdown("### District Overview")
    if not snapshot:
        st.warning(
            "No Digital Twin state yet. Start Mosquitto, subscriber and publisher "
            "so SQLite receives sensor measurements."
        )
        return

    overview = pd.DataFrame(snapshot)
    display_overview = overview[
        [
            "name",
            "temperature",
            "humidity",
            "air_quality",
            "measured_at",
            "freshness",
            "sensor_id",
        ]
    ].rename(
        columns={
            "name": "District",
            "temperature": "Temperature °C",
            "humidity": "Humidity %",
            "air_quality": "Air Quality",
            "measured_at": "Last update",
            "freshness": "Freshness",
            "sensor_id": "Sensor",
        }
    )
    st.dataframe(display_overview, use_container_width=True, hide_index=True)

    st.markdown("### District Details")
    names = [item["name"] for item in snapshot]
    selected_name = st.selectbox("Select district", options=names)
    selected = next(item for item in snapshot if item["name"] == selected_name)
    twin = twins[selected["district_id"]]

    detail_cols = st.columns(4)
    detail_cols[0].metric(
        "Temperature °C",
        "n/a" if selected["temperature"] is None else f"{selected['temperature']:.2f}",
    )
    detail_cols[1].metric(
        "Humidity %",
        "n/a" if selected["humidity"] is None else f"{selected['humidity']:.2f}",
    )
    detail_cols[2].metric(
        "Air Quality",
        "n/a" if selected["air_quality"] is None else f"{selected['air_quality']:.2f}",
    )
    detail_cols[3].metric("Freshness", selected["freshness"])
    st.write(f"Last update: `{selected['measured_at']}`")
    st.write(f"Sensor: `{selected['sensor_id']}`")

    baseline_decision = st.session_state.decision_engine.evaluate_twin(twin)
    st.write(f"Current environmental status: **{baseline_decision.status}**")

    st.markdown("### Scenario Simulation")
    default_temp, default_hum, default_aq = _default_scenario_values(selected)
    stored = st.session_state.simulation_engine.get_scenario(selected["district_id"])
    if stored is not None:
        default_temp, default_hum, default_aq = (
            stored.temperature,
            stored.humidity,
            stored.air_quality,
        )

    sim_cols = st.columns(3)
    sim_temperature = sim_cols[0].slider(
        "Simulated temperature °C",
        min_value=-10.0,
        max_value=50.0,
        value=float(default_temp),
        step=0.5,
        key=f"sim_temp_{selected['district_id']}",
    )
    sim_humidity = sim_cols[1].slider(
        "Simulated humidity %",
        min_value=0.0,
        max_value=100.0,
        value=float(default_hum),
        step=1.0,
        key=f"sim_hum_{selected['district_id']}",
    )
    sim_air_quality = sim_cols[2].slider(
        "Simulated air quality (0-150)",
        min_value=0.0,
        max_value=150.0,
        value=float(default_aq),
        step=1.0,
        key=f"sim_aq_{selected['district_id']}",
    )

    action_cols = st.columns(3)
    run_clicked = action_cols[0].button("Run simulation", type="primary")
    reset_clicked = action_cols[1].button("Reset simulation")
    action_cols[2].caption("Simulation never writes to SQLite.")

    if reset_clicked:
        st.session_state.simulation_engine.reset_scenario(selected["district_id"])
        st.session_state.scenario_result = None
        st.session_state.decision_result = None
        st.success(f"Simulation reset for {selected_name}. Sensor baseline unchanged.")

    if run_clicked:
        inputs = ScenarioInputs(
            temperature=sim_temperature,
            humidity=sim_humidity,
            air_quality=sim_air_quality,
        )
        comparison = st.session_state.simulation_engine.run(twin, inputs)
        decision = st.session_state.decision_engine.evaluate_scenario(comparison)
        st.session_state.scenario_result = comparison.to_dict()
        st.session_state.decision_result = decision.to_dict()

    if st.session_state.scenario_result is not None:
        result = st.session_state.scenario_result
        if result["district_id"] == selected["district_id"]:
            st.markdown("### Before / After Comparison")
            comparison_df = pd.DataFrame(
                [
                    {
                        "Parameter": "Temperature °C",
                        "Baseline (sensors)": result["baseline"]["temperature"],
                        "Simulated": result["simulated"]["temperature"],
                        "Delta": result["deltas"]["temperature"],
                    },
                    {
                        "Parameter": "Humidity %",
                        "Baseline (sensors)": result["baseline"]["humidity"],
                        "Simulated": result["simulated"]["humidity"],
                        "Delta": result["deltas"]["humidity"],
                    },
                    {
                        "Parameter": "Air Quality",
                        "Baseline (sensors)": result["baseline"]["air_quality"],
                        "Simulated": result["simulated"]["air_quality"],
                        "Delta": result["deltas"]["air_quality"],
                    },
                ]
            )
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            for note in result["notes"]:
                st.caption(note)

            st.markdown("### Decision Support")
            decision = st.session_state.decision_result
            if decision is not None:
                st.write(f"Status: **{decision['status']}**")
                st.write("Warnings:")
                if decision["warnings"]:
                    for warning in decision["warnings"]:
                        st.warning(warning)
                else:
                    st.info("No warnings.")
                st.write("Recommendations:")
                for recommendation in decision["recommendations"]:
                    st.write(f"- {recommendation}")
                with st.expander("Threshold assumptions"):
                    for assumption in decision["assumptions"]:
                        st.write(f"- {assumption}")


if __name__ == "__main__":
    main()
