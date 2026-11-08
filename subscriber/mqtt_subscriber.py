"""MQTT subscriber for Smart City sensor readings."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

from message_validator import InvalidSensorMessage, validate_sensor_message

ReadingHandler = Callable[[dict[str, Any]], None]


class MqttSubscriber:
    """Subscribes to a topic, validates payloads, and forwards good readings."""

    def __init__(
        self,
        on_reading: ReadingHandler,
        host: str = "localhost",
        port: int = 1883,
        topic: str = "smartcity/sensors",
        client_id: str = "smartcity-sensor-subscriber",
    ) -> None:
        self.host = host
        self.port = port
        self.topic = topic
        self.on_reading = on_reading
        self.received_count = 0
        self.invalid_count = 0
        self._connected = False

        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: mqtt.ReasonCode,
        properties: Any = None,
    ) -> None:
        if reason_code.is_failure:
            self._connected = False
            print(f"Connection failed: {reason_code}")
            return

        self._connected = True
        client.subscribe(self.topic)
        print(f"Connected to {self.host}:{self.port}")
        print(f"Subscribed to topic: {self.topic}")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: mqtt.ReasonCode,
        properties: Any = None,
    ) -> None:
        self._connected = False
        if reason_code.is_failure:
            print(f"Unexpected disconnect: {reason_code}")
        else:
            print("Disconnected from MQTT broker")

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        raw = message.payload.decode("utf-8", errors="replace")

        try:
            payload = json.loads(raw)
            reading = validate_sensor_message(payload)
        except json.JSONDecodeError:
            self.invalid_count += 1
            print(f"Invalid JSON ignored: {raw!r}")
            return
        except InvalidSensorMessage as exc:
            self.invalid_count += 1
            print(f"Invalid message ignored ({exc}): {raw!r}")
            return

        self.received_count += 1
        self.on_reading(reading)

    def connect(self) -> None:
        try:
            self._client.connect(self.host, self.port, keepalive=60)
        except ConnectionRefusedError as exc:
            raise ConnectionError(
                f"Cannot connect to MQTT broker at {self.host}:{self.port}. "
                "Is Mosquitto running?"
            ) from exc

        self._client.loop_start()

        deadline = time.time() + 5.0
        while time.time() < deadline and not self._connected:
            time.sleep(0.05)

        if not self._connected:
            self._client.loop_stop()
            raise ConnectionError(
                f"Timed out while connecting to {self.host}:{self.port}"
            )

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()
