"""SQLite database for storing glucose readings and app state."""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import GlucoseReading, SnoozeEvent, TrendDirection
from ..core.paths import get_database_path

logger = logging.getLogger(__name__)

# Schema version for migrations
SCHEMA_VERSION = 1


class Database:
    """SQLite database manager for Bear Alarm."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            db_path = get_database_path()
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._init_schema()

    def _connect(self) -> None:
        """Establish database connection."""
        self._conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,  # Allow access from multiple threads
        )
        self._conn.row_factory = sqlite3.Row
        logger.info(f"Connected to database: {self.db_path}")

    def _init_schema(self) -> None:
        """Initialize database schema."""
        cursor = self._conn.cursor()
        
        # Create tables
        cursor.executescript("""
            -- Glucose readings table
            CREATE TABLE IF NOT EXISTS glucose_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                glucose_mmol REAL NOT NULL,
                glucose_mgdl INTEGER NOT NULL,
                trend TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Index for time-based queries
            CREATE INDEX IF NOT EXISTS idx_readings_timestamp 
                ON glucose_readings(timestamp DESC);
            
            -- Snooze events table
            CREATE TABLE IF NOT EXISTS snooze_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- App settings table (for UI state)
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Schema version tracking
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            );
        """)
        
        # Set schema version if not exists
        cursor.execute(
            "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,)
        )
        
        self._conn.commit()
        logger.info("Database schema initialized")

    def add_reading(
        self,
        glucose_mmol: float,
        glucose_mgdl: int,
        trend: Optional[TrendDirection] = None,
        timestamp: Optional[datetime] = None,
    ) -> GlucoseReading:
        """
        Add a new glucose reading.
        
        Args:
            glucose_mmol: Glucose level in mmol/L
            glucose_mgdl: Glucose level in mg/dL
            trend: Optional trend direction
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            The created GlucoseReading
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        trend_value = trend.value if trend else None
        
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO glucose_readings (timestamp, glucose_mmol, glucose_mgdl, trend)
            VALUES (?, ?, ?, ?)
            """,
            (timestamp.isoformat(), glucose_mmol, glucose_mgdl, trend_value)
        )
        self._conn.commit()
        
        reading = GlucoseReading(
            id=cursor.lastrowid,
            timestamp=timestamp,
            glucose_mmol=glucose_mmol,
            glucose_mgdl=glucose_mgdl,
            trend=trend or TrendDirection.NONE,
        )
        
        logger.debug(f"Added reading: {glucose_mmol} mmol/L at {timestamp}")
        return reading

    def get_latest_reading(self) -> Optional[GlucoseReading]:
        """Get the most recent glucose reading."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT id, timestamp, glucose_mmol, glucose_mgdl, trend
            FROM glucose_readings
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        return GlucoseReading.from_row(tuple(row))

    def get_readings(
        self,
        hours: int = 24,
        limit: Optional[int] = None,
    ) -> list[GlucoseReading]:
        """
        Get glucose readings for a time period.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of readings to return
            
        Returns:
            List of GlucoseReading objects, newest first
        """
        since = datetime.now() - timedelta(hours=hours)
        
        query = """
            SELECT id, timestamp, glucose_mmol, glucose_mgdl, trend
            FROM glucose_readings
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self._conn.cursor()
        cursor.execute(query, (since.isoformat(),))
        
        return [GlucoseReading.from_row(tuple(row)) for row in cursor.fetchall()]

    def get_readings_for_chart(
        self,
        hours: int = 24,
    ) -> list[tuple[datetime, float]]:
        """
        Get readings formatted for charting (timestamp, value pairs).
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of (timestamp, glucose_mmol) tuples, oldest first
        """
        readings = self.get_readings(hours=hours)
        # Reverse to get oldest first for charting
        return [(r.timestamp, r.glucose_mmol) for r in reversed(readings)]

    def add_snooze(
        self,
        duration_minutes: int,
        reason: Optional[str] = None,
    ) -> SnoozeEvent:
        """
        Record a snooze event.
        
        Args:
            duration_minutes: How long to snooze for
            reason: Optional reason for snooze
            
        Returns:
            The created SnoozeEvent
        """
        now = datetime.now()
        
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO snooze_events (started_at, duration_minutes, reason)
            VALUES (?, ?, ?)
            """,
            (now.isoformat(), duration_minutes, reason)
        )
        self._conn.commit()
        
        event = SnoozeEvent(
            id=cursor.lastrowid,
            started_at=now,
            duration_minutes=duration_minutes,
            reason=reason,
        )
        
        logger.info(f"Snooze started: {duration_minutes} minutes")
        return event

    def get_active_snooze(self) -> Optional[SnoozeEvent]:
        """Get currently active snooze, if any."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT id, started_at, duration_minutes, reason
            FROM snooze_events
            ORDER BY started_at DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        event = SnoozeEvent.from_row(tuple(row))
        
        if event.is_active:
            return event
        return None

    def cancel_snooze(self) -> bool:
        """
        Cancel any active snooze by setting its duration to elapsed time.
        
        Returns:
            True if a snooze was cancelled, False if none was active
        """
        active = self.get_active_snooze()
        if active is None:
            return False
        
        elapsed = int((datetime.now() - active.started_at).total_seconds() / 60)
        
        cursor = self._conn.cursor()
        cursor.execute(
            """
            UPDATE snooze_events
            SET duration_minutes = ?
            WHERE id = ?
            """,
            (elapsed, active.id)
        )
        self._conn.commit()
        
        logger.info("Snooze cancelled")
        return True

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            """,
            (key, value, datetime.now().isoformat())
        )
        self._conn.commit()

    def get_stats(self, hours: int = 24) -> dict:
        """
        Get statistics for a time period.
        
        Returns:
            Dict with min, max, avg, count, time_in_range percentage
        """
        readings = self.get_readings(hours=hours)
        
        if not readings:
            return {
                "min": None,
                "max": None,
                "avg": None,
                "count": 0,
                "time_in_range": None,
            }
        
        values = [r.glucose_mmol for r in readings]
        in_range = sum(1 for v in values if 3.9 <= v <= 10.0)
        
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(readings),
            "time_in_range": (in_range / len(readings)) * 100,
        }

    def cleanup_old_data(self, days: int = 90) -> int:
        """
        Remove readings older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of rows deleted
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        cursor = self._conn.cursor()
        cursor.execute(
            "DELETE FROM glucose_readings WHERE timestamp < ?",
            (cutoff.isoformat(),)
        )
        deleted = cursor.rowcount
        self._conn.commit()
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old readings")
        
        return deleted

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

