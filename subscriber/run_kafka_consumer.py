"""Receive sensor readings from Kafka, process them, and store in SQLite."""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
from pathlib import Path
from typing import Any

from kafka_consumer import KafkaSensorConsumer
from processing import ProcessingError, process_reading

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "database"))

from db import DEFAULT_DB_PATH, SensorDatabase  # noqa: E402


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smart City Kafka consumer (receive + process + store)",
    )
    parser.add_argument(
        "--bootstrap-server",
        default="localhost:9092",
        help="Kafka bootstrap server",
    )
    parser.add_argument(
        "--topic",
        default="smart-city-sensor-data",
        help="Kafka topic to subscribe to",
    )
    parser.add_argument(
        "--group-id",
        default="smartcity-sensor-consumers",
        help="Kafka consumer group id",
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=0,
        help="Stop after N stored messages; 0 means run until Ctrl+C",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = parse_args()
    db = SensorDatabase(args.db)
    stored_count = 0
    rejected_count = 0

    def handle_reading(reading: dict[str, Any]) -> None:
        nonlocal stored_count, rejected_count
        try:
            processed = process_reading(reading)
            row_id = db.save_reading(processed)
            stored_count += 1
            print(
                f"Stored id={row_id} "
                f"category={processed['air_quality_category']}: "
                f"{json.dumps({k: processed[k] for k in ('sensor_id', 'location', 'timestamp', 'temperature', 'humidity', 'air_quality')}, ensure_ascii=False)}",
                flush=True,
            )
        except ProcessingError as exc:
            rejected_count += 1
            logger.error("Processing rejected reading: %s | %r", exc, reading)
            return

        if args.max_messages > 0 and stored_count >= args.max_messages:
            consumer.request_stop()

    consumer = KafkaSensorConsumer(
        on_reading=handle_reading,
        bootstrap_servers=args.bootstrap_server,
        topic=args.topic,
        group_id=args.group_id,
    )

    def _stop_handler(signum: int, frame: Any) -> None:
        print("\nStop signal received, shutting down...", flush=True)
        consumer.request_stop()

    signal.signal(signal.SIGINT, _stop_handler)
    signal.signal(signal.SIGTERM, _stop_handler)

    print("Kafka Consumer + Processing + SQLite started", flush=True)
    print(f"Bootstrap server: {args.bootstrap_server}", flush=True)
    print(f"Topic: {args.topic}", flush=True)
    print(f"Group id: {args.group_id}", flush=True)
    print(f"Database: {db.db_path}", flush=True)
    print("-" * 60, flush=True)

    try:
        consumer.connect()
        consumer.run()
    except ConnectionError as exc:
        print(f"Error: {exc}", flush=True)
        return
    finally:
        consumer.disconnect()
        print(
            f"Valid Kafka messages: {consumer.received_count}, "
            f"invalid ignored: {consumer.invalid_count}, "
            f"stored: {stored_count}, "
            f"processing rejected: {rejected_count}, "
            f"rows in DB: {db.count_readings()}",
            flush=True,
        )
        db.close()


if __name__ == "__main__":
    main()
