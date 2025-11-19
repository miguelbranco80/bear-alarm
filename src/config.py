"""Configuration management for Bear Alarm."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class DexcomConfig(BaseModel):
    """Dexcom Share configuration."""

    username: str = Field(..., description="Dexcom Share username")
    password: str = Field(..., description="Dexcom Share password")
    ous: bool = Field(
        default=False,
        description="Set to True if outside US (uses different Dexcom server)",
    )


class AlertsConfig(BaseModel):
    """Alert configuration."""

    low_threshold: float = Field(
        default=3.0, description="Low glucose threshold in mmol/L", gt=0
    )
    high_threshold: float = Field(
        default=13.0, description="High glucose threshold in mmol/L", gt=0
    )
    low_alert_sound: str = Field(
        default="alerts/alarm.wav", description="Path to low alert sound file"
    )
    high_alert_sound: str = Field(
        default="alerts/alarm.wav", description="Path to high alert sound file"
    )
    alert_interval: int = Field(
        default=300, description="Seconds between repeated alerts", gt=0
    )

    @field_validator("high_threshold")
    @classmethod
    def validate_thresholds(cls, v: float, info) -> float:
        """Ensure high threshold is greater than low threshold."""
        if "low_threshold" in info.data and v <= info.data["low_threshold"]:
            raise ValueError("high_threshold must be greater than low_threshold")
        return v


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

    dexcom: DexcomConfig
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, looks for config.yaml in current directory.

    Returns:
        Config object with validated settings.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config is invalid.
    """
    if config_path is None:
        config_path = "config.yaml"

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Please create a config.yaml file based on config.yaml.example"
        )

    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    if config_data is None:
        raise ValueError(f"Configuration file is empty: {config_path}")

    return Config(**config_data)


def load_config_with_env_override(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file with environment variable overrides.

    Environment variables:
        DEXCOM_USERNAME: Override dexcom.username
        DEXCOM_PASSWORD: Override dexcom.password
        DEXCOM_OUS: Override dexcom.ous (set to 'true' or 'false')

    Args:
        config_path: Path to config file.

    Returns:
        Config object with validated settings.
    """
    config = load_config(config_path)

    # Override with environment variables if present
    if os.getenv("DEXCOM_USERNAME"):
        config.dexcom.username = os.getenv("DEXCOM_USERNAME")
    if os.getenv("DEXCOM_PASSWORD"):
        config.dexcom.password = os.getenv("DEXCOM_PASSWORD")
    if os.getenv("DEXCOM_OUS"):
        config.dexcom.ous = os.getenv("DEXCOM_OUS", "").lower() == "true"

    return config

