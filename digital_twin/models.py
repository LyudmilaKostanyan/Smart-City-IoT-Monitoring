"""Digital Twin data model for Yerevan districts.

Freshness policy (demonstration assumption):
- CURRENT: last measurement age <= STALE_AFTER_SECONDS
- STALE: measurement exists but is older than STALE_AFTER_SECONDS
- NO_DATA: no measurement has been associated with the district yet

These thresholds are for the university prototype only. They are not official
city monitoring SLAs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


STALE_AFTER_SECONDS = 60


class FreshnessStatus(str, Enum):
    CURRENT = "current"
    STALE = "stale"
    NO_DATA = "no_data"


@dataclass(frozen=True)
class DistrictDefinition:
    """Static mapping between a virtual district and its sensors."""

    district_id: str
    name: str
    sensor_ids: tuple[str, ...]


# Virtual districts required by the assignment.
# Each district is linked to one simulated sensor (1:1 for clarity).
DISTRICTS: tuple[DistrictDefinition, ...] = (
    DistrictDefinition("kentron", "Kentron", ("sensor_01",)),
    DistrictDefinition("arabkir", "Arabkir", ("sensor_02",)),
    DistrictDefinition("shengavit", "Shengavit", ("sensor_03",)),
)


@dataclass
class EnvironmentalState:
    """Latest known environmental measurements for one district."""

    temperature: float | None = None
    humidity: float | None = None
    air_quality: float | None = None
    measured_at: datetime | None = None
    sensor_id: str | None = None

    @property
    def has_measurements(self) -> bool:
        return (
            self.temperature is not None
            and self.humidity is not None
            and self.air_quality is not None
            and self.measured_at is not None
        )


@dataclass
class DistrictTwin:
    """Digital Twin representation of one city district."""

    definition: DistrictDefinition
    state: EnvironmentalState = field(default_factory=EnvironmentalState)

    @property
    def district_id(self) -> str:
        return self.definition.district_id

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def sensor_ids(self) -> tuple[str, ...]:
        return self.definition.sensor_ids

    def freshness(
        self,
        *,
        now: datetime | None = None,
        stale_after_seconds: int = STALE_AFTER_SECONDS,
    ) -> FreshnessStatus:
        if not self.state.has_measurements or self.state.measured_at is None:
            return FreshnessStatus.NO_DATA

        current_time = now or datetime.now(timezone.utc)
        measured_at = self.state.measured_at
        if measured_at.tzinfo is None:
            measured_at = measured_at.replace(tzinfo=timezone.utc)

        age = current_time - measured_at
        if age <= timedelta(seconds=stale_after_seconds):
            return FreshnessStatus.CURRENT
        return FreshnessStatus.STALE

    def to_dict(
        self,
        *,
        now: datetime | None = None,
        stale_after_seconds: int = STALE_AFTER_SECONDS,
    ) -> dict[str, Any]:
        freshness = self.freshness(now=now, stale_after_seconds=stale_after_seconds)
        measured_at = self.state.measured_at
        return {
            "district_id": self.district_id,
            "name": self.name,
            "sensor_ids": list(self.sensor_ids),
            "temperature": self.state.temperature,
            "humidity": self.state.humidity,
            "air_quality": self.state.air_quality,
            "measured_at": measured_at.isoformat() if measured_at else None,
            "sensor_id": self.state.sensor_id,
            "freshness": freshness.value,
            "has_measurements": self.state.has_measurements,
        }


def build_empty_twins(
    definitions: tuple[DistrictDefinition, ...] = DISTRICTS,
) -> dict[str, DistrictTwin]:
    """Create an empty twin for every configured district."""
    return {
        definition.district_id: DistrictTwin(definition=definition)
        for definition in definitions
    }


def district_id_for_location(location: str) -> str | None:
    """Map a sensor location string to a district_id."""
    normalized = location.strip().lower()
    for definition in DISTRICTS:
        if definition.name.lower() == normalized:
            return definition.district_id
    return None


def district_id_for_sensor(sensor_id: str) -> str | None:
    """Map a sensor_id to a district_id."""
    for definition in DISTRICTS:
        if sensor_id in definition.sensor_ids:
            return definition.district_id
    return None
