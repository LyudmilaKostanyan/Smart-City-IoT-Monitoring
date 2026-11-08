"""Run the sensor simulator locally and print JSON readings.

MQTT is intentionally not used on this stage.
"""

from __future__ import annotations

import argparse
import json
import time

from sensor_simulator import SensorSimulator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smart City sensor simulator (console output only)",
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
    cycle = 0

    print("Sensor Simulator started (no MQTT yet)")
    print(f"Sensors: {len(simulator.sensors)}, interval: {args.interval}s")
    print("-" * 60)

    try:
        while True:
            cycle += 1
            readings = simulator.generate_readings()

            print(f"Cycle {cycle}")
            for reading in readings:
                print(json.dumps(reading, ensure_ascii=False))
            print("-" * 60)

            if args.cycles > 0 and cycle >= args.cycles:
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSimulator stopped by user")


if __name__ == "__main__":
    main()
