"""Synchronize Digital Twin district state from the SQLite data platform.

Raw sensor rows in SQLite are historical measurements.
The Digital Twin keeps only the latest known state per district plus freshness.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import (
    DISTRICTS,
    DistrictTwin,
    EnvironmentalState,
    FreshnessStatus,
    STALE_AFTER_SECONDS,
    build_empty_twins,
    district_id_for_location,
    district_id_for_sensor,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "database"))

from db import DEFAULT_DB_PATH, SensorDatabase  # noqa: E402


def parse_measurement_timestamp(raw: str) -> datetime:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class DigitalTwinStateManager:
    """Loads latest SQLite readings into in-memory district twins."""

    def __init__(
        self,
        db: SensorDatabase | None = None,
        db_path: Path | str | None = None,
        stale_after_seconds: int = STALE_AFTER_SECONDS,
    ) -> None:
        self._owns_db = db is None
        self.db = db if db is not None else SensorDatabase(db_path or DEFAULT_DB_PATH)
        self.stale_after_seconds = stale_after_seconds
        self.twins: dict[str, DistrictTwin] = build_empty_twins(DISTRICTS)

    def refresh(self, *, now: datetime | None = None) -> dict[str, DistrictTwin]:
        """Rebuild twin states from the latest SQLite measurement per location."""
        current_time = now or datetime.now(timezone.utc)
        # Start from empty states so removed/unknown districts do not keep stale memory.
        self.twins = build_empty_twins(DISTRICTS)

        latest_rows = self.db.fetch_latest_per_location()
        for row in latest_rows:
            self._apply_row(row)

        # Touch freshness evaluation with provided "now" for deterministic tests.
        for twin in self.twins.values():
            twin.freshness(
                now=current_time,
                stale_after_seconds=self.stale_after_seconds,
            )
        return self.twins

    def _apply_row(self, row: dict[str, Any]) -> None:
        location = str(row.get("location", ""))
        sensor_id = str(row.get("sensor_id", ""))

        # Prefer location mapping. Do NOT fall back to sensor_id when the location
        # is known but foreign (e.g. old "Erebuni" rows that reused sensor_02):
        # otherwise historical rows can overwrite the correct Arabkir state.
        district_id = district_id_for_location(location)
        if district_id is None and not location.strip():
            district_id = district_id_for_sensor(sensor_id)
        if district_id is None:
            # Unknown location (e.g. old Erebuni/Nor Nork/Malatsia) — ignore.
            return

        twin = self.twins[district_id]
        try:
            measured_at = parse_measurement_timestamp(str(row["timestamp"]))
            temperature = float(row["temperature"])
            humidity = float(row["humidity"])
            air_quality = float(row["air_quality"])
        except (KeyError, TypeError, ValueError):
            return

        twin.state = EnvironmentalState(
            temperature=temperature,
            humidity=humidity,
            air_quality=air_quality,
            measured_at=measured_at,
            sensor_id=sensor_id or None,
        )

    def get_district(self, district_id: str) -> DistrictTwin | None:
        return self.twins.get(district_id)

    def snapshot(
        self,
        *,
        now: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Return serializable district states for dashboards/APIs."""
        current_time = now or datetime.now(timezone.utc)
        return [
            twin.to_dict(
                now=current_time,
                stale_after_seconds=self.stale_after_seconds,
            )
            for twin in self.twins.values()
        ]

    def freshness_summary(
        self,
        *,
        now: datetime | None = None,
    ) -> dict[str, FreshnessStatus]:
        current_time = now or datetime.now(timezone.utc)
        return {
            district_id: twin.freshness(
                now=current_time,
                stale_after_seconds=self.stale_after_seconds,
            )
            for district_id, twin in self.twins.items()
        }

    def close(self) -> None:
        if self._owns_db:
            self.db.close()
