"""MQTT publisher for Smart City sensor readings."""

from __future__ import annotations

import json
from typing import Any

import paho.mqtt.client as mqtt


class MqttPublisher:
    """Connects to an MQTT broker and publishes JSON payloads to a topic."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1883,
        topic: str = "smartcity/sensors",
        client_id: str = "smartcity-sensor-publisher",
    ) -> None:
        self.host = host
        self.port = port
        self.topic = topic
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )

    def connect(self) -> None:
        self._client.connect(self.host, self.port, keepalive=60)
        self._client.loop_start()

    def publish(self, payload: dict[str, Any]) -> None:
        message = json.dumps(payload, ensure_ascii=False)
        result = self._client.publish(self.topic, message, qos=0)
        result.wait_for_publish(timeout=5.0)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT publish failed with code {result.rc}")

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
