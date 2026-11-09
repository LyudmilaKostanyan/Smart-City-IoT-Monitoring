"""Rule-based decision support for Digital Twin scenarios.

Demonstration thresholds only — not official environmental standards.
Air-quality uses the project's 0..150 simulator index, not a certified AQI scale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import DistrictTwin, FreshnessStatus, STALE_AFTER_SECONDS
from .simulation import ScenarioComparison


@dataclass(frozen=True)
class DecisionThresholds:
    """Configurable demo thresholds for warnings."""

    high_temperature: float = 35.0
    high_air_quality: float = 70.0
    low_humidity: float = 20.0
    high_humidity: float = 90.0


@dataclass
class DecisionResult:
    district: str
    status: str
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    evaluated_values: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "district": self.district,
            "status": self.status,
            "warnings": list(self.warnings),
            "recommendations": list(self.recommendations),
            "evaluated_values": dict(self.evaluated_values),
            "assumptions": list(self.assumptions),
        }


class DecisionEngine:
    """Evaluates baseline or simulated values with simple if/then rules."""

    def __init__(self, thresholds: DecisionThresholds | None = None) -> None:
        self.thresholds = thresholds or DecisionThresholds()

    def evaluate_values(
        self,
        *,
        district_name: str,
        temperature: float | None,
        humidity: float | None,
        air_quality: float | None,
        freshness: FreshnessStatus | None = None,
        source: str = "sensor_baseline",
    ) -> DecisionResult:
        assumptions = [
            "Thresholds are demonstration values for a university prototype.",
            "air_quality is a 0..150 project index, not an official AQI certificate.",
            f"high_temperature > {self.thresholds.high_temperature} °C",
            f"high_air_quality > {self.thresholds.high_air_quality}",
            f"humidity outside [{self.thresholds.low_humidity}, {self.thresholds.high_humidity}] %",
            f"Data older than {STALE_AFTER_SECONDS}s is treated as stale.",
        ]

        warnings: list[str] = []
        recommendations: list[str] = []

        if freshness == FreshnessStatus.NO_DATA or (
            temperature is None and humidity is None and air_quality is None
        ):
            return DecisionResult(
                district=district_name,
                status="uncertain",
                warnings=["No sensor measurements available for this district"],
                recommendations=[
                    "Wait for live sensor data before making operational decisions"
                ],
                evaluated_values={
                    "temperature": temperature,
                    "humidity": humidity,
                    "air_quality": air_quality,
                    "freshness": freshness.value if freshness else "no_data",
                    "source": source,
                },
                assumptions=assumptions,
            )

        if freshness == FreshnessStatus.STALE:
            warnings.append("Sensor data is stale; current state is uncertain")
            recommendations.append(
                "Refresh monitoring feed before relying on this district state"
            )

        if temperature is not None and temperature > self.thresholds.high_temperature:
            warnings.append("High temperature detected")
            recommendations.append(
                "Increase heat-stress monitoring frequency for this district"
            )

        if air_quality is not None and air_quality > self.thresholds.high_air_quality:
            warnings.append("Elevated air pollution detected")
            recommendations.append(
                "Increase environmental monitoring and investigate possible sources"
            )

        if humidity is not None and humidity < self.thresholds.low_humidity:
            warnings.append("Low humidity detected")
            recommendations.append("Monitor dry-air comfort and dust conditions")
        elif humidity is not None and humidity > self.thresholds.high_humidity:
            warnings.append("High humidity detected")
            recommendations.append("Monitor moisture-related comfort conditions")

        multi_issue = sum(
            1
            for flag in (
                temperature is not None
                and temperature > self.thresholds.high_temperature,
                air_quality is not None
                and air_quality > self.thresholds.high_air_quality,
                humidity is not None
                and (
                    humidity < self.thresholds.low_humidity
                    or humidity > self.thresholds.high_humidity
                ),
            )
            if flag
        )
        if multi_issue >= 2:
            warnings.append("Multiple environmental parameters exceed demo thresholds")
            recommendations.append(
                "Treat this as a combined risk scenario and review all parameters together"
            )

        if not warnings:
            status = "normal"
            recommendations.append("Conditions are within configured demonstration ranges")
        elif freshness == FreshnessStatus.STALE:
            status = "uncertain"
        else:
            status = "warning"

        # Deduplicate while preserving order
        warnings = list(dict.fromkeys(warnings))
        recommendations = list(dict.fromkeys(recommendations))

        return DecisionResult(
            district=district_name,
            status=status,
            warnings=warnings,
            recommendations=recommendations,
            evaluated_values={
                "temperature": temperature,
                "humidity": humidity,
                "air_quality": air_quality,
                "freshness": freshness.value if freshness else None,
                "source": source,
            },
            assumptions=assumptions,
        )

    def evaluate_twin(
        self,
        twin: DistrictTwin,
        *,
        now=None,
    ) -> DecisionResult:
        freshness = twin.freshness(now=now)
        return self.evaluate_values(
            district_name=twin.name,
            temperature=twin.state.temperature,
            humidity=twin.state.humidity,
            air_quality=twin.state.air_quality,
            freshness=freshness,
            source="sensor_baseline",
        )

    def evaluate_scenario(self, comparison: ScenarioComparison) -> DecisionResult:
        simulated = comparison.simulated
        return self.evaluate_values(
            district_name=comparison.district_name,
            temperature=float(simulated["temperature"]),
            humidity=float(simulated["humidity"]),
            air_quality=float(simulated["air_quality"]),
            freshness=FreshnessStatus.CURRENT,
            source="hypothetical_simulation",
        )
