"""Core business logic for Bear Alarm."""

from .alerts import AlertSystem, AlertState
from .config import (
    Config, load_config, save_config,
    ScheduleConfig, EmergencyContactConfig, ThresholdsConfig,
)
from .dexcom_client import DexcomClient, DexcomClientError
from .emergency import call_facetime, send_imessage, open_messages_app
from .monitor import GlucoseMonitor
from .paths import (
    get_user_data_dir,
    get_user_config_path,
    get_resources_dir,
    resolve_sound_path,
    is_packaged,
)
from .system import prevent_sleep, allow_sleep, check_volume_status, get_system_volume

__all__ = [
    "AlertSystem",
    "AlertState",
    "Config",
    "load_config",
    "save_config",
    "ScheduleConfig",
    "EmergencyContactConfig",
    "ThresholdsConfig",
    "DexcomClient",
    "DexcomClientError",
    "GlucoseMonitor",
    "get_user_data_dir",
    "get_user_config_path",
    "get_resources_dir",
    "resolve_sound_path",
    "is_packaged",
    "prevent_sleep",
    "allow_sleep",
    "check_volume_status",
    "get_system_volume",
    "call_facetime",
    "send_imessage",
    "open_messages_app",
]

