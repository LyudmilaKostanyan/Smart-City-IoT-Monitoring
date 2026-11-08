"""SQLite storage for Smart City sensor readings."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "smartcity.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL,
    location TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    air_quality REAL NOT NULL,
    received_at TEXT NOT NULL
);
"""


class SensorDatabase:
    """Creates the readings table and stores / reads sensor messages."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self._lock:
            self._conn.execute(CREATE_TABLE_SQL)
            self._conn.commit()

    def save_reading(self, reading: dict[str, Any]) -> int:
        received_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO sensor_readings (
                    sensor_id, location, timestamp,
                    temperature, humidity, air_quality, received_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reading["sensor_id"],
                    reading["location"],
                    reading["timestamp"],
                    float(reading["temperature"]),
                    float(reading["humidity"]),
                    float(reading["air_quality"]),
                    received_at,
                ),
            )
            self._conn.commit()
            return int(cursor.lastrowid)

    def fetch_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT
                    id, sensor_id, location, timestamp,
                    temperature, humidity, air_quality, received_at
                FROM sensor_readings
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def fetch_latest_per_location(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT
                    r.id, r.sensor_id, r.location, r.timestamp,
                    r.temperature, r.humidity, r.air_quality, r.received_at
                FROM sensor_readings AS r
                INNER JOIN (
                    SELECT location, MAX(id) AS max_id
                    FROM sensor_readings
                    GROUP BY location
                ) AS latest ON r.id = latest.max_id
                ORDER BY r.location
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def fetch_history(
        self,
        limit: int = 200,
        location: str | None = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                id, sensor_id, location, timestamp,
                temperature, humidity, air_quality, received_at
            FROM sensor_readings
        """
        params: tuple[Any, ...]
        if location:
            query += " WHERE location = ?"
            params = (location, limit)
        else:
            params = (limit,)

        query += " ORDER BY id DESC LIMIT ?"

        with self._lock:
            rows = self._conn.execute(query, params).fetchall()

        # Oldest first — convenient for charts.
        return [dict(row) for row in reversed(rows)]

    def list_locations(self) -> list[str]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT DISTINCT location
                FROM sensor_readings
                ORDER BY location
                """
            ).fetchall()
        return [str(row["location"]) for row in rows]

    def count_readings(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS total FROM sensor_readings"
            ).fetchone()
        return int(row["total"])

    def close(self) -> None:
        with self._lock:
            self._conn.close()
