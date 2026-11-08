"""Validate MQTT payloads for Smart City sensor readings."""

from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = (
    "sensor_id",
    "location",
    "timestamp",
    "temperature",
    "humidity",
    "air_quality",
)


class InvalidSensorMessage(ValueError):
    """Raised when a payload does not match the expected sensor format."""


def validate_sensor_message(payload: Any) -> dict[str, Any]:
    """Return a cleaned reading dict or raise InvalidSensorMessage."""
    if not isinstance(payload, dict):
        raise InvalidSensorMessage("Payload must be a JSON object")

    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        raise InvalidSensorMessage(f"Missing fields: {', '.join(missing)}")

    sensor_id = payload["sensor_id"]
    location = payload["location"]
    timestamp = payload["timestamp"]

    if not isinstance(sensor_id, str) or not sensor_id.strip():
        raise InvalidSensorMessage("sensor_id must be a non-empty string")
    if not isinstance(location, str) or not location.strip():
        raise InvalidSensorMessage("location must be a non-empty string")
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise InvalidSensorMessage("timestamp must be a non-empty string")

    try:
        temperature = float(payload["temperature"])
        humidity = float(payload["humidity"])
        air_quality = float(payload["air_quality"])
    except (TypeError, ValueError) as exc:
        raise InvalidSensorMessage(
            "temperature, humidity and air_quality must be numbers"
        ) from exc

    return {
        "sensor_id": sensor_id.strip(),
        "location": location.strip(),
        "timestamp": timestamp.strip(),
        "temperature": temperature,
        "humidity": humidity,
        "air_quality": air_quality,
    }
