"""Generate sensor readings and publish them to Apache Kafka."""

from __future__ import annotations

import argparse
import json
import logging
import time

from kafka_publisher import KafkaSensorPublisher
from sensor_simulator import SensorSimulator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smart City Kafka publisher (sensor simulator -> Kafka)",
    )
    parser.add_argument(
        "--bootstrap-server",
        default="localhost:9092",
        help="Kafka bootstrap server (default: localhost:9092)",
    )
    parser.add_argument(
        "--topic",
        default="smart-city-sensor-data",
        help="Kafka topic for sensor readings",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Seconds between reading cycles (default: 2.0)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=5,
        help="How many cycles to run; use 0 for infinite loop (default: 5)",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    args = parse_args()
    simulator = SensorSimulator()
    publisher = KafkaSensorPublisher(
        bootstrap_servers=args.bootstrap_server,
        topic=args.topic,
    )

    print("Kafka Publisher started")
    print(f"Bootstrap server: {args.bootstrap_server}")
    print(f"Topic: {args.topic}")
    print(f"Sensors: {len(simulator.sensors)}, interval: {args.interval}s")
    print("-" * 60)

    publisher.connect()
    cycle = 0

    try:
        while True:
            cycle += 1
            readings = simulator.generate_readings()

            print(f"Cycle {cycle}")
            for reading in readings:
                publisher.publish(reading)
                print(f"Published: {json.dumps(reading, ensure_ascii=False)}")
            print("-" * 60)

            if args.cycles > 0 and cycle >= args.cycles:
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nPublisher stopped by user")
    finally:
        publisher.disconnect()
        print("Disconnected from Kafka")


if __name__ == "__main__":
    main()
