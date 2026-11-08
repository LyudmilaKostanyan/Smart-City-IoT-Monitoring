"""Generate sensor readings and publish them to the MQTT broker."""

from __future__ import annotations

import argparse
import json
import time

from mqtt_publisher import MqttPublisher
from sensor_simulator import SensorSimulator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smart City MQTT publisher (sensor simulator -> broker)",
    )
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument(
        "--topic",
        default="smartcity/sensors",
        help="MQTT topic for sensor readings",
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
    args = parse_args()
    simulator = SensorSimulator()
    publisher = MqttPublisher(host=args.host, port=args.port, topic=args.topic)

    print("MQTT Publisher started")
    print(f"Broker: {args.host}:{args.port}")
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
        print("Disconnected from MQTT broker")


if __name__ == "__main__":
    main()
