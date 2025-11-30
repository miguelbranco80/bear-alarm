"""Path resolution for Bear Alarm - handles both development and packaged modes."""

import os
import platform
import sys
from pathlib import Path


def is_packaged() -> bool:
    """Check if running as a packaged application."""
    # PyInstaller sets this attribute
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_bundle_dir() -> Path:
    """Get the directory where bundled resources are located."""
    if is_packaged():
        # PyInstaller extracts to _MEIPASS
        return Path(sys._MEIPASS)
    else:
        # Development: project root
        return Path(__file__).parent.parent.parent


def get_resources_dir() -> Path:
    """Get the resources directory."""
    return get_bundle_dir() / "resources"


def get_user_data_dir() -> Path:
    """
    Get the user's application data directory.
    
    Returns:
        macOS: ~/Library/Application Support/BearAlarm
        Windows: %LOCALAPPDATA%/BearAlarm
        Linux: ~/.local/share/bear-alarm
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        base = Path.home() / "Library" / "Application Support" / "BearAlarm"
    elif system == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        base = Path(local_app_data) / "BearAlarm"
    else:  # Linux and others
        xdg_data = os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
        base = Path(xdg_data) / "bear-alarm"
    
    # Ensure directory exists
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_user_config_path() -> Path:
    """Get path to user's config file."""
    return get_user_data_dir() / "config.yaml"


def resolve_sound_path(sound_path: str) -> Path:
    """
    Resolve a sound file path to an absolute path.
    
    Args:
        sound_path: Path string like "sounds/alarm.wav"
        
    Returns:
        Resolved absolute Path within resources directory
    """
    path = Path(sound_path)
    
    if path.is_absolute():
        return path
    
    # Strip "resources/" prefix if present
    sound_path_str = str(sound_path)
    if sound_path_str.startswith("resources/"):
        sound_path_str = sound_path_str[len("resources/"):]
    
    return get_resources_dir() / sound_path_str


def get_database_path() -> Path:
    """Get path to SQLite database."""
    return get_user_data_dir() / "bear_alarm.db"

