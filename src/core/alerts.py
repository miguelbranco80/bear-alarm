"""Alert system with audio playback and state management."""

import logging
import threading
import time
from enum import Enum
from pathlib import Path
from typing import Optional

import pygame

from .paths import resolve_sound_path

logger = logging.getLogger(__name__)


class AlertState(Enum):
    """Alert states for glucose monitoring."""

    NORMAL = "normal"
    LOW_ALERT = "low_alert"
    HIGH_ALERT = "high_alert"


class AlertSystem:
    """
    Manages glucose alerts with audio playback.

    Plays alert sounds when glucose levels are out of range and repeats
    at configurable intervals until levels return to normal.
    """

    def __init__(
        self,
        low_alert_sound: str,
        high_alert_sound: str,
        alert_interval: int = 300,
    ):
        """
        Initialize alert system.

        Args:
            low_alert_sound: Path to audio file (WAV or MP3) for low glucose alerts
            high_alert_sound: Path to audio file (WAV or MP3) for high glucose alerts
            alert_interval: Seconds between repeated alerts
        """
        # Resolve paths (handles both development and packaged modes)
        self.low_alert_sound = resolve_sound_path(low_alert_sound)
        self.high_alert_sound = resolve_sound_path(high_alert_sound)
        self.alert_interval = alert_interval

        self._current_state = AlertState.NORMAL
        self._alert_thread: Optional[threading.Thread] = None
        self._stop_alert_event = threading.Event()
        self._mixer_initialized = False
        self._music_initialized = False

        self._initialize_mixer()

    def _initialize_mixer(self) -> None:
        """Initialize pygame mixer for audio playback."""
        try:
            pygame.mixer.init()
            self._mixer_initialized = True
            # Also initialize music module for MP3 support
            try:
                pygame.mixer.music.set_volume(1.0)
                self._music_initialized = True
            except Exception:
                logger.warning("Music module not available, MP3 support may be limited")
                self._music_initialized = False
            logger.info("Audio system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            logger.warning("Alerts will not play sounds")
            self._mixer_initialized = False
            self._music_initialized = False

    def _validate_sound_file(self, sound_path: Path) -> bool:
        """
        Validate that sound file exists and is accessible.

        Args:
            sound_path: Path to sound file

        Returns:
            True if file is valid, False otherwise
        """
        if not sound_path.exists():
            logger.error(f"Alert sound file not found: {sound_path}")
            return False

        if not sound_path.is_file():
            logger.error(f"Alert sound path is not a file: {sound_path}")
            return False

        return True

    def _is_mp3(self, sound_path: Path) -> bool:
        """Check if file is MP3 based on extension."""
        return sound_path.suffix.lower() in ['.mp3', '.mpeg']

    def _play_sound(self, sound_path: Path) -> bool:
        """
        Play a sound file (WAV or MP3).

        Args:
            sound_path: Path to audio file (WAV or MP3)

        Returns:
            True if sound played successfully, False otherwise
        """
        if not self._mixer_initialized:
            logger.warning("Audio system not initialized, cannot play sound")
            return False

        if not self._validate_sound_file(sound_path):
            return False

        try:
            # Use music module for MP3, Sound for WAV
            if self._is_mp3(sound_path):
                if not self._music_initialized:
                    logger.warning("Music module not initialized, cannot play MP3")
                    return False
                pygame.mixer.music.load(str(sound_path))
                pygame.mixer.music.play()
                logger.debug(f"Playing MP3 alert sound: {sound_path}")
            else:
                sound = pygame.mixer.Sound(str(sound_path))
                sound.play()
                logger.debug(f"Playing WAV alert sound: {sound_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to play sound {sound_path}: {e}")
            return False

    def _alert_loop(self, alert_state: AlertState) -> None:
        """
        Alert loop that plays sounds at intervals.

        Args:
            alert_state: Type of alert (LOW_ALERT or HIGH_ALERT)
        """
        sound_path = (
            self.low_alert_sound
            if alert_state == AlertState.LOW_ALERT
            else self.high_alert_sound
        )

        logger.info(f"Starting alert loop for {alert_state.value}")

        # Play immediately
        self._play_sound(sound_path)

        # Continue playing at intervals until stopped
        while not self._stop_alert_event.is_set():
            # Wait for interval or until stop event
            if self._stop_alert_event.wait(timeout=self.alert_interval):
                break
            self._play_sound(sound_path)

        logger.info(f"Alert loop stopped for {alert_state.value}")

    def _stop_current_alert(self) -> None:
        """Stop any currently running alert."""
        if self._alert_thread and self._alert_thread.is_alive():
            logger.debug("Stopping current alert")
            self._stop_alert_event.set()
            self._alert_thread.join(timeout=2)
            self._alert_thread = None

    def trigger_low_alert(self) -> None:
        """Trigger low glucose alert."""
        if self._current_state == AlertState.LOW_ALERT:
            logger.debug("Low alert already active")
            return

        logger.warning("LOW GLUCOSE ALERT TRIGGERED")
        self._stop_current_alert()
        self._current_state = AlertState.LOW_ALERT
        self._stop_alert_event.clear()
        self._alert_thread = threading.Thread(
            target=self._alert_loop,
            args=(AlertState.LOW_ALERT,),
            daemon=True,
        )
        self._alert_thread.start()

    def trigger_high_alert(self) -> None:
        """Trigger high glucose alert."""
        if self._current_state == AlertState.HIGH_ALERT:
            logger.debug("High alert already active")
            return

        logger.warning("HIGH GLUCOSE ALERT TRIGGERED")
        self._stop_current_alert()
        self._current_state = AlertState.HIGH_ALERT
        self._stop_alert_event.clear()
        self._alert_thread = threading.Thread(
            target=self._alert_loop,
            args=(AlertState.HIGH_ALERT,),
            daemon=True,
        )
        self._alert_thread.start()

    def clear_alert(self) -> None:
        """Clear any active alerts (glucose returned to normal)."""
        if self._current_state == AlertState.NORMAL:
            return

        logger.info(f"Clearing {self._current_state.value}, glucose returned to normal")
        self._stop_current_alert()
        self._current_state = AlertState.NORMAL

    def get_state(self) -> AlertState:
        """
        Get current alert state.

        Returns:
            Current AlertState
        """
        return self._current_state

    def is_alerting(self) -> bool:
        """
        Check if currently alerting.

        Returns:
            True if in alert state, False if normal
        """
        return self._current_state != AlertState.NORMAL

    def shutdown(self) -> None:
        """Shutdown alert system and cleanup resources."""
        logger.info("Shutting down alert system")
        self._stop_current_alert()
        if self._mixer_initialized:
            try:
                pygame.mixer.quit()
            except Exception as e:
                logger.error(f"Error shutting down mixer: {e}")

