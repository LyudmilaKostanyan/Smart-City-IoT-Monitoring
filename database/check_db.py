"""Print recent rows from the Smart City SQLite database."""

from __future__ import annotations

import argparse
import json

from db import DEFAULT_DB_PATH, SensorDatabase


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect stored sensor readings")
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="How many recent rows to show (default: 10)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = SensorDatabase(args.db)
    try:
        total = db.count_readings()
        rows = db.fetch_recent(limit=args.limit)
        print(f"Database: {db.db_path}")
        print(f"Total readings: {total}")
        print("-" * 60)
        for row in rows:
            print(json.dumps(row, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
