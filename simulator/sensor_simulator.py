"""Virtual IoT sensors for Smart City environmental monitoring."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


@dataclass
class SensorConfig:
    sensor_id: str
    location: str
    base_temperature: float
    base_humidity: float
    base_air_quality: float


DEFAULT_SENSORS: list[SensorConfig] = [
    SensorConfig("sensor_01", "Kentron", 4.5, 78.0, 48.0),
    SensorConfig("sensor_02", "Erebuni", 5.0, 72.0, 72.0),
    SensorConfig("sensor_03", "Nor Nork", 3.5, 82.0, 38.0),
    SensorConfig("sensor_04", "Malatsia", 4.0, 80.0, 32.0),
]


class VirtualSensor:
    """Keeps the latest reading and applies small realistic drift each tick."""

    def __init__(self, config: SensorConfig) -> None:
        self.sensor_id = config.sensor_id
        self.location = config.location
        self.temperature = config.base_temperature
        self.humidity = config.base_humidity
        self.air_quality = config.base_air_quality

    def update(self) -> dict[str, Any]:
        self.temperature = _clamp(
            self.temperature + random.uniform(-0.4, 0.4),
            -10.0,
            45.0,
        )
        self.humidity = _clamp(
            self.humidity + random.uniform(-1.5, 1.5),
            10.0,
            95.0,
        )
        self.air_quality = _clamp(
            self.air_quality + random.uniform(-2.0, 2.0),
            0.0,
            150.0,
        )

        return {
            "sensor_id": self.sensor_id,
            "location": self.location,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": round(self.temperature, 2),
            "humidity": round(self.humidity, 2),
            "air_quality": round(self.air_quality, 2),
        }


class SensorSimulator:
    """Owns several virtual sensors and produces one reading batch per cycle."""

    def __init__(self, configs: list[SensorConfig] | None = None) -> None:
        source = configs if configs is not None else DEFAULT_SENSORS
        self.sensors = [VirtualSensor(config) for config in source]

    def generate_readings(self) -> list[dict[str, Any]]:
        return [sensor.update() for sensor in self.sensors]
