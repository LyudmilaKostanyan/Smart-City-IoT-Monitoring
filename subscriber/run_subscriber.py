"""Receive sensor readings from MQTT, validate them, and store in SQLite."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from threading import Event
from typing import Any

from mqtt_subscriber import MqttSubscriber

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "database"))

from db import DEFAULT_DB_PATH, SensorDatabase  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smart City MQTT subscriber (receive + validate + store)",
    )
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument(
        "--topic",
        default="smartcity/sensors",
        help="MQTT topic to subscribe to",
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
        help="Stop after N valid messages; 0 means run until Ctrl+C",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stop_event = Event()
    db = SensorDatabase(args.db)

    def handle_reading(reading: dict[str, Any]) -> None:
        row_id = db.save_reading(reading)
        print(
            f"Saved id={row_id}: {json.dumps(reading, ensure_ascii=False)}",
            flush=True,
        )
        if args.max_messages > 0 and subscriber.received_count >= args.max_messages:
            stop_event.set()

    subscriber = MqttSubscriber(
        on_reading=handle_reading,
        host=args.host,
        port=args.port,
        topic=args.topic,
    )

    print("MQTT Subscriber started", flush=True)
    print(f"Broker: {args.host}:{args.port}", flush=True)
    print(f"Topic: {args.topic}", flush=True)
    print(f"Database: {db.db_path}", flush=True)
    print("-" * 60, flush=True)

    try:
        subscriber.connect()
        while not stop_event.is_set():
            time.sleep(0.2)
    except ConnectionError as exc:
        print(f"Error: {exc}", flush=True)
        return
    except KeyboardInterrupt:
        print("\nSubscriber stopped by user", flush=True)
    finally:
        subscriber.disconnect()
        print(
            f"Valid messages: {subscriber.received_count}, "
            f"invalid ignored: {subscriber.invalid_count}, "
            f"rows in DB: {db.count_readings()}",
            flush=True,
        )
        db.close()


if __name__ == "__main__":
    main()
