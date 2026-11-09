"""Hypothetical scenario simulation for Digital Twin districts.

Important:
- Simulated values never write back to SQLite.
- Baseline values come from the Digital Twin state (sensor-backed).
- This is a demonstration tool, not a validated environmental forecast.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .models import DistrictTwin


@dataclass
class ScenarioInputs:
    """User-provided hypothetical environmental parameters."""

    temperature: float
    humidity: float
    air_quality: float


@dataclass
class ScenarioComparison:
    """Before/after view for one district scenario."""

    district_id: str
    district_name: str
    baseline: dict[str, Any]
    simulated: dict[str, Any]
    deltas: dict[str, float | None]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "district_id": self.district_id,
            "district_name": self.district_name,
            "baseline": self.baseline,
            "simulated": self.simulated,
            "deltas": self.deltas,
            "notes": list(self.notes),
            "is_hypothetical": True,
        }


class SimulationEngine:
    """Runs what-if scenarios against a district twin baseline."""

    def __init__(self) -> None:
        self._active: dict[str, ScenarioInputs] = {}

    def set_scenario(self, district_id: str, inputs: ScenarioInputs) -> None:
        self._validate_inputs(inputs)
        self._active[district_id] = ScenarioInputs(
            temperature=float(inputs.temperature),
            humidity=float(inputs.humidity),
            air_quality=float(inputs.air_quality),
        )

    def get_scenario(self, district_id: str) -> ScenarioInputs | None:
        stored = self._active.get(district_id)
        return deepcopy(stored) if stored is not None else None

    def reset_scenario(self, district_id: str | None = None) -> None:
        if district_id is None:
            self._active.clear()
            return
        self._active.pop(district_id, None)

    def run(
        self,
        twin: DistrictTwin,
        inputs: ScenarioInputs | None = None,
    ) -> ScenarioComparison:
        """Compare baseline twin state with hypothetical inputs.

        If inputs are omitted, uses a previously stored scenario for the district.
        """
        scenario = inputs if inputs is not None else self.get_scenario(twin.district_id)
        if scenario is None:
            raise ValueError(
                f"No scenario inputs provided for district '{twin.district_id}'"
            )

        self._validate_inputs(scenario)
        if inputs is not None:
            self.set_scenario(twin.district_id, scenario)

        baseline = {
            "temperature": twin.state.temperature,
            "humidity": twin.state.humidity,
            "air_quality": twin.state.air_quality,
            "measured_at": (
                twin.state.measured_at.isoformat() if twin.state.measured_at else None
            ),
            "source": "sensor_baseline",
        }
        simulated = {
            "temperature": float(scenario.temperature),
            "humidity": float(scenario.humidity),
            "air_quality": float(scenario.air_quality),
            "source": "hypothetical_simulation",
        }
        deltas = {
            "temperature": self._delta(baseline["temperature"], simulated["temperature"]),
            "humidity": self._delta(baseline["humidity"], simulated["humidity"]),
            "air_quality": self._delta(baseline["air_quality"], simulated["air_quality"]),
        }

        notes = [
            "Simulation values are hypothetical and do not modify SQLite sensor data.",
        ]
        if not twin.state.has_measurements:
            notes.append(
                "Baseline has no sensor data; comparison uses empty baseline values."
            )

        return ScenarioComparison(
            district_id=twin.district_id,
            district_name=twin.name,
            baseline=baseline,
            simulated=simulated,
            deltas=deltas,
            notes=notes,
        )

    @staticmethod
    def _delta(before: float | None, after: float) -> float | None:
        if before is None:
            return None
        return round(after - float(before), 2)

    @staticmethod
    def _validate_inputs(inputs: ScenarioInputs) -> None:
        if not -30.0 <= float(inputs.temperature) <= 55.0:
            raise ValueError("temperature must be within [-30, 55] °C for the demo")
        if not 0.0 <= float(inputs.humidity) <= 100.0:
            raise ValueError("humidity must be within [0, 100] %")
        if not 0.0 <= float(inputs.air_quality) <= 150.0:
            raise ValueError("air_quality must be within [0, 150] demo index")
