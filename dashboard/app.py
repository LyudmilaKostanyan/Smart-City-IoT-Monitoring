"""Streamlit dashboard for Smart City environmental monitoring."""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "database"))

from db import DEFAULT_DB_PATH, SensorDatabase  # noqa: E402

HISTORY_LIMIT = 100
REFRESH_SECONDS = 5

st.set_page_config(
    page_title="Smart City Monitoring",
    layout="wide",
)


def load_db() -> SensorDatabase:
    return SensorDatabase(DEFAULT_DB_PATH)


def readings_to_frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame


def main() -> None:
    st.title("Smart City Environmental Monitoring")
    st.caption("Yerevan districts: Kentron, Erebuni, Nor Nork, Malatsia")

    db = load_db()
    try:
        total = db.count_readings()
    finally:
        db.close()

    if total == 0:
        st.warning(
            "No data in SQLite yet. Start Mosquitto, Subscriber and Publisher first."
        )
        return

    @st.fragment(run_every=timedelta(seconds=REFRESH_SECONDS))
    def live_dashboard() -> None:
        database = load_db()
        try:
            latest = readings_to_frame(database.fetch_latest_per_location())
            history = readings_to_frame(
                database.fetch_history(limit=HISTORY_LIMIT)
            )
            count = database.count_readings()
        finally:
            database.close()

        st.subheader("Current sensor state")
        st.write(f"Total stored readings: **{count}**")

        if latest.empty:
            st.info("Waiting for the first readings...")
            return

        metric_cols = st.columns(len(latest))
        for column, (_, row) in zip(metric_cols, latest.iterrows()):
            with column:
                st.markdown(f"### {row['location']}")
                st.metric("Temperature °C", f"{row['temperature']:.2f}")
                st.metric("Humidity %", f"{row['humidity']:.2f}")
                st.metric("Air Quality", f"{row['air_quality']:.2f}")
                st.caption(f"{row['sensor_id']} · {row['timestamp']}")

        st.subheader("History table")
        if history.empty:
            st.info("No history yet.")
            return

        display = history[
            [
                "id",
                "sensor_id",
                "location",
                "timestamp",
                "temperature",
                "humidity",
                "air_quality",
            ]
        ].sort_values("id", ascending=False)
        st.dataframe(display, use_container_width=True, hide_index=True)

        st.subheader("Charts")
        chart_cols = st.columns(3)

        with chart_cols[0]:
            fig_temp = px.line(
                history,
                x="timestamp",
                y="temperature",
                color="location",
                markers=True,
                title="Temperature",
            )
            st.plotly_chart(fig_temp, use_container_width=True)

        with chart_cols[1]:
            fig_hum = px.line(
                history,
                x="timestamp",
                y="humidity",
                color="location",
                markers=True,
                title="Humidity",
            )
            st.plotly_chart(fig_hum, use_container_width=True)

        with chart_cols[2]:
            fig_aq = px.line(
                history,
                x="timestamp",
                y="air_quality",
                color="location",
                markers=True,
                title="Air Quality",
            )
            st.plotly_chart(fig_aq, use_container_width=True)

        compare = (
            latest[["location", "temperature", "humidity", "air_quality"]]
            .set_index("location")
        )
        st.subheader("District comparison (latest values)")
        st.bar_chart(compare)

    live_dashboard()


if __name__ == "__main__":
    main()
