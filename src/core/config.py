"""Configuration management for Bear Alarm."""

import logging
import os
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
    ous: bool = Field(
        default=False,
        description="Set to True if outside US (uses different Dexcom server)",
    )
    
    @property
    def is_configured(self) -> bool:
        """Check if Dexcom credentials are configured."""
        return bool(self.username and self.password)


class AlertsConfig(BaseModel):
    """Alert configuration."""

    low_threshold: float = Field(
        default=3.9, description="Low glucose threshold in mmol/L", gt=0
    )
    high_threshold: float = Field(
        default=15.0, description="High glucose threshold in mmol/L", gt=0
    )
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
    if os.getenv("DEXCOM_OUS"):
        config_data.setdefault("dexcom", {})["ous"] = os.getenv("DEXCOM_OUS", "").lower() == "true"
    
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
            "ous": config.dexcom.ous,
        },
        "alerts": {
            "low_threshold": config.alerts.low_threshold,
            "high_threshold": config.alerts.high_threshold,
            "low_alert_sound": config.alerts.low_alert_sound,
            "high_alert_sound": config.alerts.high_alert_sound,
            "alert_interval": config.alerts.alert_interval,
            "min_volume": config.alerts.min_volume,
        },
        "monitoring": {
            "poll_interval": config.monitoring.poll_interval,
            "startup_delay_minutes": config.monitoring.startup_delay_minutes,
        },
    }
    
    with open(user_path, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Configuration saved to {user_path}")
