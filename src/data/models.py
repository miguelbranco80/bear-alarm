"""Data models for Bear Alarm."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TrendDirection(Enum):
    """Glucose trend direction from Dexcom."""
    
    NONE = "None"
    DOUBLE_UP = "DoubleUp"
    SINGLE_UP = "SingleUp"
    FORTY_FIVE_UP = "FortyFiveUp"
    FLAT = "Flat"
    FORTY_FIVE_DOWN = "FortyFiveDown"
    SINGLE_DOWN = "SingleDown"
    DOUBLE_DOWN = "DoubleDown"
    NOT_COMPUTABLE = "NotComputable"
    RATE_OUT_OF_RANGE = "RateOutOfRange"

    @property
    def arrow(self) -> str:
        """Get arrow symbol for trend."""
        arrows = {
            TrendDirection.DOUBLE_UP: "⬆⬆",
            TrendDirection.SINGLE_UP: "⬆",
            TrendDirection.FORTY_FIVE_UP: "↗",
            TrendDirection.FLAT: "→",
            TrendDirection.FORTY_FIVE_DOWN: "↘",
            TrendDirection.SINGLE_DOWN: "⬇",
            TrendDirection.DOUBLE_DOWN: "⬇⬇",
        }
        return arrows.get(self, "?")


@dataclass
class GlucoseReading:
    """A single glucose reading."""
    
    id: Optional[int]
    timestamp: datetime
    glucose_mmol: float
    glucose_mgdl: int
    trend: TrendDirection
    
    @classmethod
    def from_row(cls, row: tuple) -> "GlucoseReading":
        """Create from database row."""
        return cls(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            glucose_mmol=row[2],
            glucose_mgdl=row[3],
            trend=TrendDirection(row[4]) if row[4] else TrendDirection.NONE,
        )
    
    @property
    def is_low(self) -> bool:
        """Check if reading is low (using default threshold)."""
        return self.glucose_mmol <= 3.9
    
    @property
    def is_high(self) -> bool:
        """Check if reading is high (using default threshold)."""
        return self.glucose_mmol >= 10.0


@dataclass
class SnoozeEvent:
    """A snooze event record."""
    
    id: Optional[int]
    started_at: datetime
    duration_minutes: int
    reason: Optional[str]
    
    @classmethod
    def from_row(cls, row: tuple) -> "SnoozeEvent":
        """Create from database row."""
        return cls(
            id=row[0],
            started_at=datetime.fromisoformat(row[1]),
            duration_minutes=row[2],
            reason=row[3],
        )
    
    @property
    def ends_at(self) -> datetime:
        """Get when snooze ends."""
        from datetime import timedelta
        return self.started_at + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_active(self) -> bool:
        """Check if snooze is currently active."""
        return datetime.now() < self.ends_at

