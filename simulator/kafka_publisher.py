"""Kafka producer for Smart City sensor readings."""

from __future__ import annotations

import json
import logging
from typing import Any

from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable


logger = logging.getLogger(__name__)


class KafkaSensorPublisher:
    """Publishes sensor reading dicts to a Kafka topic as JSON."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "smart-city-sensor-data",
        client_id: str = "smartcity-sensor-producer",
    ) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.client_id = client_id
        self._producer: KafkaProducer | None = None

    def connect(self) -> None:
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                client_id=self.client_id,
                # Convert Python dict -> UTF-8 JSON bytes before sending.
                value_serializer=lambda value: json.dumps(
                    value, ensure_ascii=False
                ).encode("utf-8"),
                key_serializer=lambda key: key.encode("utf-8") if key else None,
                acks="all",
                retries=3,
                linger_ms=10,
            )
        except NoBrokersAvailable as exc:
            raise ConnectionError(
                f"Cannot connect to Kafka at {self.bootstrap_servers}. "
                "Is the broker running? Try: ./tools/start_kafka.sh"
            ) from exc

        logger.info(
            "Connected Kafka producer to %s, topic=%s",
            self.bootstrap_servers,
            self.topic,
        )

    def publish(self, payload: dict[str, Any]) -> None:
        if self._producer is None:
            raise RuntimeError("Producer is not connected. Call connect() first.")

        key = str(payload.get("sensor_id", "unknown"))
        try:
            future = self._producer.send(self.topic, key=key, value=payload)
            record = future.get(timeout=10)
        except KafkaError as exc:
            raise RuntimeError(f"Kafka publish failed: {exc}") from exc

        logger.info(
            "Published sensor_id=%s to %s partition=%s offset=%s",
            key,
            self.topic,
            record.partition,
            record.offset,
        )

    def disconnect(self) -> None:
        if self._producer is not None:
            self._producer.flush(timeout=10)
            self._producer.close(timeout=10)
            self._producer = None
            logger.info("Kafka producer disconnected")
