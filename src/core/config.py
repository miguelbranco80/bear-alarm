"""Configuration management for Bear Alarm."""

import logging
import os
from datetime import time
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from .paths import get_user_config_path, resolve_sound_path

logger = logging.getLogger(__name__)


class DexcomConfig(BaseModel):
    """Dexcom Share configuration."""

    username: str = Field(default="", description="Dexcom Share username")
    password: str = Field(default="", description="Dexcom Share password")
    region: str = Field(
        default="us",
        description="Dexcom region: 'us', 'ous' (outside US), or 'jp' (Japan)",
    )
    
    @property
    def is_configured(self) -> bool:
        """Check if Dexcom credentials are configured."""
        return bool(self.username and self.password)


class ThresholdsConfig(BaseModel):
    """Threshold and persistence settings (used by default and schedules)."""
    
    low_threshold: float = Field(
        default=3.9, description="Low glucose threshold in mmol/L", gt=0
    )
    high_threshold: float = Field(
        default=15.0, description="High glucose threshold in mmol/L", gt=0
    )
    low_persist_minutes: int = Field(
        default=0, description="Minutes low must persist before alerting", ge=0
    )
    high_persist_minutes: int = Field(
        default=0, description="Minutes high must persist before alerting", ge=0
    )
    
    @field_validator("high_threshold")
    @classmethod
    def validate_thresholds(cls, v: float, info) -> float:
        """Ensure high threshold is greater than low threshold."""
        if "low_threshold" in info.data and v <= info.data["low_threshold"]:
            raise ValueError("high_threshold must be greater than low_threshold")
        return v


class ScheduleConfig(BaseModel):
    """A named schedule that overrides default thresholds during specific times."""
    
    name: str = Field(description="Schedule name (e.g., 'Work', 'Sleep')")
    enabled: bool = Field(default=True, description="Whether this schedule is active")
    priority: int = Field(default=1, description="Higher priority wins when schedules overlap", ge=1)
    
    # Time range
    start_time: str = Field(default="09:00", description="Start time (HH:MM)")
    end_time: str = Field(default="17:00", description="End time (HH:MM)")
    
    # Days of week (0=Monday, 6=Sunday)
    days: list[int] = Field(
        default=[0, 1, 2, 3, 4],  # Mon-Fri
        description="Days of week (0=Mon, 6=Sun)"
    )
    
    # Override thresholds (None = use default)
    low_threshold: Optional[float] = Field(default=None, description="Override low threshold")
    high_threshold: Optional[float] = Field(default=None, description="Override high threshold")
    low_persist_minutes: Optional[int] = Field(default=None, description="Override low persistence")
    high_persist_minutes: Optional[int] = Field(default=None, description="Override high persistence")
    
    def get_start_time(self) -> time:
        """Parse start time string to time object."""
        parts = self.start_time.split(":")
        return time(int(parts[0]), int(parts[1]))
    
    def get_end_time(self) -> time:
        """Parse end time string to time object."""
        parts = self.end_time.split(":")
        return time(int(parts[0]), int(parts[1]))
    
    def is_active_now(self) -> bool:
        """Check if this schedule is currently active."""
        if not self.enabled:
            return False
        
        from datetime import datetime
        now = datetime.now()
        
        # Check day of week
        if now.weekday() not in self.days:
            return False
        
        # Check time range
        current_time = now.time()
        start = self.get_start_time()
        end = self.get_end_time()
        
        # Handle overnight schedules (e.g., 23:00 - 07:00)
        if start <= end:
            return start <= current_time <= end
        else:
            return current_time >= start or current_time <= end


class EmergencyContactConfig(BaseModel):
    """Emergency contact for auto-message on alerts."""
    
    name: str = Field(default="", description="Contact name")
    phone: str = Field(default="", description="Phone number (for FaceTime/iMessage)")
    enabled: bool = Field(default=True, description="Whether this contact is active")
    
    # Auto-message on LOW alert
    message_on_low: bool = Field(default=False, description="Send message when low alert triggers")
    message_on_low_snooze: int = Field(default=30, description="Minutes before re-sending low message", ge=5)
    low_message_text: str = Field(
        default="⚠️ LOW glucose alert! Please check on me.",
        description="Message for low alerts"
    )
    
    # Auto-message on HIGH alert  
    message_on_high: bool = Field(default=False, description="Send message when high alert triggers")
    message_on_high_snooze: int = Field(default=60, description="Minutes before re-sending high message", ge=5)
    high_message_text: str = Field(
        default="⚠️ HIGH glucose alert - prolonged high blood sugar.",
        description="Message for high alerts"
    )


class AlertsConfig(BaseModel):
    """Alert configuration."""

    # Urgent thresholds - ALWAYS alert immediately, bypass persistence
    urgent_low: float = Field(
        default=2.8, description="Urgent low - always alert immediately", gt=0
    )
    
    # Default thresholds (when no schedule is active)
    low_threshold: float = Field(
        default=3.9, description="Low glucose threshold in mmol/L", gt=0
    )
    high_threshold: float = Field(
        default=15.0, description="High glucose threshold in mmol/L", gt=0
    )
    
    # Persistence - how long condition must last before alerting
    low_persist_minutes: int = Field(
        default=0, description="Minutes low must persist before alerting", ge=0
    )
    high_persist_minutes: int = Field(
        default=0, description="Minutes high must persist before alerting", ge=0
    )
    
    # Sound settings
    low_alert_sound: str = Field(
        default="sounds/siren.mp3", description="Path to low alert sound file"
    )
    high_alert_sound: str = Field(
        default="sounds/siren.mp3", description="Path to high alert sound file"
    )
    alert_interval: int = Field(
        default=300, description="Seconds between repeated alerts", gt=0
    )
    min_volume: int = Field(
        default=50, description="Minimum system volume before warning (10-100)", ge=10, le=100
    )
    
    # Schedules
    schedules: list[ScheduleConfig] = Field(
        default_factory=list, description="Time-based schedule overrides"
    )
    
    # Emergency contacts
    emergency_contacts: list[EmergencyContactConfig] = Field(
        default_factory=list, description="Emergency contacts for critical alerts"
    )

    @field_validator("high_threshold")
    @classmethod
    def validate_thresholds(cls, v: float, info) -> float:
        """Ensure high threshold is greater than low threshold."""
        if "low_threshold" in info.data and v <= info.data["low_threshold"]:
            raise ValueError("high_threshold must be greater than low_threshold")
        return v
    
    def get_low_sound_path(self) -> Path:
        """Get resolved path to low alert sound."""
        return resolve_sound_path(self.low_alert_sound)
    
    def get_high_sound_path(self) -> Path:
        """Get resolved path to high alert sound."""
        return resolve_sound_path(self.high_alert_sound)
    
    def get_active_schedule(self) -> Optional[ScheduleConfig]:
        """Get the highest-priority currently active schedule, or None."""
        active = [s for s in self.schedules if s.is_active_now()]
        if not active:
            return None
        # Return highest priority
        return max(active, key=lambda s: s.priority)
    
    def get_effective_thresholds(self) -> ThresholdsConfig:
        """Get the currently effective thresholds (considering active schedule)."""
        schedule = self.get_active_schedule()
        
        if schedule is None:
            return ThresholdsConfig(
                low_threshold=self.low_threshold,
                high_threshold=self.high_threshold,
                low_persist_minutes=self.low_persist_minutes,
                high_persist_minutes=self.high_persist_minutes,
            )
        
        # Schedule overrides (use default if not specified)
        return ThresholdsConfig(
            low_threshold=schedule.low_threshold if schedule.low_threshold is not None else self.low_threshold,
            high_threshold=schedule.high_threshold if schedule.high_threshold is not None else self.high_threshold,
            low_persist_minutes=schedule.low_persist_minutes if schedule.low_persist_minutes is not None else self.low_persist_minutes,
            high_persist_minutes=schedule.high_persist_minutes if schedule.high_persist_minutes is not None else self.high_persist_minutes,
        )


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    poll_interval: int = Field(
        default=300,
        description="Seconds between glucose checks (5 minutes matches Dexcom update frequency)",
        gt=0,
    )
    startup_delay_minutes: int = Field(
        default=0, description="Minutes to wait before first check", ge=0
    )
    
    @property
    def startup_delay(self) -> int:
        """Get startup delay in seconds (for internal use)."""
        return self.startup_delay_minutes * 60


class Config(BaseModel):
    """Main application configuration."""

    dexcom: DexcomConfig = Field(default_factory=DexcomConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    @property
    def is_configured(self) -> bool:
        """Check if required configuration is present."""
        return self.dexcom.is_configured


def _load_yaml(path: Path) -> dict:
    """Load YAML file, returning empty dict if not found."""
    if not path.exists():
        return {}
    
    with open(path, "r") as f:
        data = yaml.safe_load(f)
        return data if data else {}


def load_config() -> Config:
    """
    Load configuration.
    
    Order (later overrides earlier):
    1. Pydantic model defaults (in code)
    2. User config (~/.../BearAlarm/config.yaml)
    3. Environment variables
    
    Returns:
        Config object with merged settings.
    """
    # Start with empty dict - Pydantic provides defaults
    config_data = {}
    
    # Load user config if exists
    user_path = get_user_config_path()
    if user_path.exists():
        config_data = _load_yaml(user_path)
        logger.debug(f"Loaded user config from {user_path}")
    
    # Apply environment variable overrides
    if os.getenv("DEXCOM_USERNAME"):
        config_data.setdefault("dexcom", {})["username"] = os.getenv("DEXCOM_USERNAME")
    if os.getenv("DEXCOM_PASSWORD"):
        config_data.setdefault("dexcom", {})["password"] = os.getenv("DEXCOM_PASSWORD")
    if os.getenv("DEXCOM_REGION"):
        config_data.setdefault("dexcom", {})["region"] = os.getenv("DEXCOM_REGION", "us")
    
    return Config(**config_data)


def save_config(config: Config) -> None:
    """
    Save configuration to user config file.
    
    Args:
        config: Config object to save
    """
    user_path = get_user_config_path()
    
    # Ensure directory exists
    user_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict
    config_dict = {
        "dexcom": {
            "username": config.dexcom.username,
            "password": config.dexcom.password,
            "region": config.dexcom.region,
        },
        "alerts": {
            "urgent_low": config.alerts.urgent_low,
            "low_threshold": config.alerts.low_threshold,
            "high_threshold": config.alerts.high_threshold,
            "low_persist_minutes": config.alerts.low_persist_minutes,
            "high_persist_minutes": config.alerts.high_persist_minutes,
            "low_alert_sound": config.alerts.low_alert_sound,
            "high_alert_sound": config.alerts.high_alert_sound,
            "alert_interval": config.alerts.alert_interval,
            "min_volume": config.alerts.min_volume,
            "schedules": [
                {
                    "name": s.name,
                    "enabled": s.enabled,
                    "priority": s.priority,
                    "start_time": s.start_time,
                    "end_time": s.end_time,
                    "days": s.days,
                    "low_threshold": s.low_threshold,
                    "high_threshold": s.high_threshold,
                    "low_persist_minutes": s.low_persist_minutes,
                    "high_persist_minutes": s.high_persist_minutes,
                }
                for s in config.alerts.schedules
            ],
            "emergency_contacts": [
                {
                    "name": c.name,
                    "phone": c.phone,
                    "enabled": c.enabled,
                    "message_on_low": c.message_on_low,
                    "message_on_low_snooze": c.message_on_low_snooze,
                    "low_message_text": c.low_message_text,
                    "message_on_high": c.message_on_high,
                    "message_on_high_snooze": c.message_on_high_snooze,
                    "high_message_text": c.high_message_text,
                }
                for c in config.alerts.emergency_contacts
            ],
        },
        "monitoring": {
            "poll_interval": config.monitoring.poll_interval,
            "startup_delay_minutes": config.monitoring.startup_delay_minutes,
        },
    }
    
    with open(user_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Configuration saved to {user_path}")
