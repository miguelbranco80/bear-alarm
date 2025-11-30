"""System utilities for Bear Alarm."""

import atexit
import logging
import platform
import subprocess
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_caffeinate_process: Optional[subprocess.Popen] = None

def get_system_volume() -> Optional[int]:
    """
    Get the current system volume level.
    
    Returns:
        Volume level 0-100, or None if unable to detect.
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception as e:
            logger.debug(f"Failed to get macOS volume: {e}")
    
    elif system == "Windows":
        try:
            # Use PowerShell to get volume
            result = subprocess.run(
                ["powershell", "-Command", 
                 "(Get-AudioDevice -PlaybackVolume).Volume"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return int(float(result.stdout.strip()))
        except Exception as e:
            logger.debug(f"Failed to get Windows volume: {e}")
    
    elif system == "Linux":
        try:
            # Try amixer (ALSA)
            result = subprocess.run(
                ["amixer", "get", "Master"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                # Parse output like "[50%]"
                import re
                match = re.search(r'\[(\d+)%\]', result.stdout)
                if match:
                    return int(match.group(1))
        except Exception as e:
            logger.debug(f"Failed to get Linux volume: {e}")
    
    return None


def is_muted() -> Optional[bool]:
    """
    Check if system audio is muted.
    
    Returns:
        True if muted, False if not, None if unable to detect.
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ["osascript", "-e", "output muted of (get volume settings)"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip().lower() == "true"
        except Exception as e:
            logger.debug(f"Failed to check macOS mute: {e}")
    
    return None


def check_volume_status(min_volume: int = 30) -> Tuple[bool, str]:
    """
    Check if volume is adequate for alerts.
    
    Args:
        min_volume: Minimum acceptable volume level (0-100)
    
    Returns:
        Tuple of (is_ok, message)
        - is_ok: True if volume is adequate
        - message: Warning message if not ok, empty string if ok
    """
    muted = is_muted()
    if muted is True:
        return False, "🔇 MUTED"
    
    volume = get_system_volume()
    if volume is not None and volume < min_volume:
        return False, f"🔈 Volume low: {volume}%"
    
    return True, ""


def prevent_sleep() -> bool:
    """
    Prevent the system from sleeping while the app is running.
    
    On macOS, starts a caffeinate process.
    On other platforms, this is a no-op (user should configure power settings).
    
    Returns:
        True if sleep prevention was enabled, False otherwise.
    """
    global _caffeinate_process
    
    if platform.system() != "Darwin":
        logger.debug("Sleep prevention not implemented for this platform")
        return False
    
    if _caffeinate_process is not None:
        logger.debug("Caffeinate already running")
        return True
    
    try:
        # -i: prevent idle sleep
        # -d: prevent display sleep (optional, remove if you want display to sleep)
        _caffeinate_process = subprocess.Popen(
            ["caffeinate", "-i"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        atexit.register(allow_sleep)
        logger.info("Sleep prevention enabled (caffeinate)")
        return True
    except FileNotFoundError:
        logger.warning("caffeinate not found")
        return False
    except Exception as e:
        logger.warning(f"Failed to start caffeinate: {e}")
        return False


def allow_sleep() -> None:
    """
    Allow the system to sleep again.
    
    Stops the caffeinate process if running.
    """
    global _caffeinate_process
    
    if _caffeinate_process is not None:
        try:
            _caffeinate_process.terminate()
            _caffeinate_process.wait(timeout=2)
            logger.info("Sleep prevention disabled")
        except Exception as e:
            logger.warning(f"Error stopping caffeinate: {e}")
        finally:
            _caffeinate_process = None

