"""Kafka consumer for Smart City sensor readings."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from kafka import KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable

from message_validator import InvalidSensorMessage, validate_sensor_message


logger = logging.getLogger(__name__)

ReadingHandler = Callable[[dict[str, Any]], None]


class KafkaSensorConsumer:
    """Subscribes to a Kafka topic, validates JSON, and forwards good readings."""

    def __init__(
        self,
        on_reading: ReadingHandler,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "smart-city-sensor-data",
        group_id: str = "smartcity-sensor-consumers",
        client_id: str = "smartcity-sensor-consumer",
        auto_offset_reset: str = "earliest",
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.client_id = client_id
        self.auto_offset_reset = auto_offset_reset
        self.on_reading = on_reading
        self.received_count = 0
        self.invalid_count = 0
        self._consumer: KafkaConsumer | None = None
        self._stop = False

    def connect(self) -> None:
        try:
            self._consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                client_id=self.client_id,
                # Keep raw bytes here; JSON parsing happens in _handle_message
                # so malformed payloads do not crash the poll loop.
                value_deserializer=lambda raw: raw,
                key_deserializer=lambda raw: raw.decode("utf-8") if raw else None,
                auto_offset_reset=self.auto_offset_reset,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                consumer_timeout_ms=1000,
            )
        except NoBrokersAvailable as exc:
            raise ConnectionError(
                f"Cannot connect to Kafka at {self.bootstrap_servers}. "
                "Is the broker running? Try: ./tools/start_kafka.sh"
            ) from exc

        logger.info(
            "Connected Kafka consumer to %s topic=%s group_id=%s",
            self.bootstrap_servers,
            self.topic,
            self.group_id,
        )

    def run(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Consumer is not connected. Call connect() first.")

        self._stop = False
        while not self._stop:
            try:
                for message in self._consumer:
                    self._handle_message(message)
                    if self._stop:
                        break
            except KafkaError as exc:
                logger.error("Kafka consumer error: %s", exc)

    def _handle_message(self, message: Any) -> None:
        raw = message.value
        raw_text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)

        logger.info(
            "Raw message partition=%s offset=%s key=%s",
            message.partition,
            message.offset,
            message.key,
        )

        try:
            payload = json.loads(raw_text)
            reading = validate_sensor_message(payload)
        except json.JSONDecodeError:
            self.invalid_count += 1
            logger.error("Invalid JSON at offset=%s: %r", message.offset, raw_text)
            return
        except InvalidSensorMessage as exc:
            self.invalid_count += 1
            logger.error(
                "Invalid sensor message at offset=%s: %s | payload=%r",
                message.offset,
                exc,
                raw_text,
            )
            return
        except Exception as exc:  # noqa: BLE001 - keep consumer alive
            self.invalid_count += 1
            logger.error(
                "Failed to process offset=%s: %s | payload=%r",
                message.offset,
                exc,
                raw_text,
            )
            return

        self.received_count += 1
        self.on_reading(reading)

    def request_stop(self) -> None:
        self._stop = True

    def disconnect(self) -> None:
        self._stop = True
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None
            logger.info("Kafka consumer disconnected")
