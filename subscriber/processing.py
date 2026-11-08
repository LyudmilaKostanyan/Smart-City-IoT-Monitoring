"""Small processing stage for Smart City sensor readings.

Assumptions (documented for the university assignment):
- temperature is Celsius
- humidity is percent relative humidity (0..100)
- air_quality is a unitless index on a 0..150 scale
  (same scale used by the sensor simulator, similar in spirit to AQI bands)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class ProcessingError(ValueError):
    """Raised when a reading fails business-rule checks."""


def _classify_air_quality(value: float) -> str:
    if value <= 50:
        return "good"
    if value <= 100:
        return "moderate"
    return "unhealthy"


def _normalize_timestamp(raw: str) -> str:
    """Accept ISO-8601 timestamps; keep original if already valid."""
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ProcessingError(f"timestamp is not valid ISO-8601: {raw!r}") from exc
    return parsed.isoformat()


def process_reading(reading: dict[str, Any]) -> dict[str, Any]:
    """Validate ranges, normalize timestamp, classify air quality.

    Returns a new dict ready for SQLite storage plus processing metadata.
    Does not mutate the input.
    """
    temperature = float(reading["temperature"])
    humidity = float(reading["humidity"])
    air_quality = float(reading["air_quality"])

    if not -20.0 <= temperature <= 50.0:
        raise ProcessingError(
            f"temperature out of range [-20, 50]: {temperature}"
        )
    if not 0.0 <= humidity <= 100.0:
        raise ProcessingError(f"humidity out of range [0, 100]: {humidity}")
    if not 0.0 <= air_quality <= 150.0:
        raise ProcessingError(
            f"air_quality out of range [0, 150]: {air_quality}"
        )

    normalized_timestamp = _normalize_timestamp(str(reading["timestamp"]))
    category = _classify_air_quality(air_quality)

    return {
        "sensor_id": reading["sensor_id"],
        "location": reading["location"],
        "timestamp": normalized_timestamp,
        "temperature": temperature,
        "humidity": humidity,
        "air_quality": air_quality,
        # Extra field for logs/dashboard logic; not stored in SQLite schema.
        "air_quality_category": category,
    }
