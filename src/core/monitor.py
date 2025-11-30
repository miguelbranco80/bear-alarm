"""Glucose monitoring service with continuous polling and alerting."""

import logging
import time
from typing import Optional

from .alerts import AlertSystem
from .config import Config
from .dexcom_client import DexcomClient, DexcomClientError

logger = logging.getLogger(__name__)


class GlucoseMonitor:
    """
    Continuous glucose monitoring service.

    Polls Dexcom Share at regular intervals, checks glucose levels against
    configured thresholds, and triggers alerts when necessary.
    """

    def __init__(self, config: Config):
        """
        Initialize glucose monitor.

        Args:
            config: Application configuration
        """
        self.config = config
        self.running = False

        # Initialize Dexcom client
        logger.info("Initializing Dexcom client...")
        self.dexcom_client = DexcomClient(
            username=config.dexcom.username,
            password=config.dexcom.password,
            ous=config.dexcom.ous,
        )

        # Initialize alert system
        logger.info("Initializing alert system...")
        self.alert_system = AlertSystem(
            low_alert_sound=config.alerts.low_alert_sound,
            high_alert_sound=config.alerts.high_alert_sound,
            alert_interval=config.alerts.alert_interval,
        )

        self._consecutive_errors = 0
        self._max_consecutive_errors = 5

    def _check_glucose_level(self, glucose_mmol: float) -> None:
        """
        Check glucose level against thresholds and trigger alerts.

        Args:
            glucose_mmol: Current glucose level in mmol/L
        """
        low_threshold = self.config.alerts.low_threshold
        high_threshold = self.config.alerts.high_threshold

        logger.info(
            f"Glucose: {glucose_mmol:.1f} mmol/L "
            f"(thresholds: {low_threshold:.1f} - {high_threshold:.1f})"
        )

        # Low takes priority over high
        if glucose_mmol <= low_threshold:
            logger.warning(
                f"LOW GLUCOSE: {glucose_mmol:.1f} mmol/L "
                f"(threshold: {low_threshold:.1f})"
            )
            self.alert_system.trigger_low_alert()

        elif glucose_mmol >= high_threshold:
            logger.warning(
                f"HIGH GLUCOSE: {glucose_mmol:.1f} mmol/L "
                f"(threshold: {high_threshold:.1f})"
            )
            self.alert_system.trigger_high_alert()

        else:
            # Glucose is in normal range
            if self.alert_system.is_alerting():
                logger.info("Glucose returned to normal range")
            self.alert_system.clear_alert()

    def _poll_once(self) -> bool:
        """
        Poll glucose level once and check thresholds.

        Returns:
            True if successful, False if error occurred
        """
        try:
            glucose_mmol = self.dexcom_client.get_glucose_mmol()

            if glucose_mmol is None:
                logger.warning("No glucose reading available")
                return False

            self._check_glucose_level(glucose_mmol)
            self._consecutive_errors = 0
            return True

        except DexcomClientError as e:
            self._consecutive_errors += 1
            logger.error(
                f"Error getting glucose reading ({self._consecutive_errors}/"
                f"{self._max_consecutive_errors}): {e}"
            )

            if self._consecutive_errors >= self._max_consecutive_errors:
                logger.critical(
                    f"Failed to get glucose reading {self._consecutive_errors} "
                    f"times in a row. Please check your connection and credentials."
                )
                # Could trigger a special alert here if desired

            return False

        except Exception as e:
            self._consecutive_errors += 1
            logger.error(f"Unexpected error during polling: {e}", exc_info=True)
            return False

    def start(self) -> None:
        """
        Start the monitoring service.

        This method blocks and runs the monitoring loop until stopped.
        """
        logger.info("Starting glucose monitoring service...")
        logger.info(
            f"Configuration: "
            f"Low threshold: {self.config.alerts.low_threshold} mmol/L, "
            f"High threshold: {self.config.alerts.high_threshold} mmol/L, "
            f"Poll interval: {self.config.monitoring.poll_interval}s, "
            f"Alert interval: {self.config.alerts.alert_interval}s"
        )

        # Test connection
        logger.info("Testing connection to Dexcom Share...")
        if not self.dexcom_client.test_connection():
            logger.error("Failed to connect to Dexcom Share")
            raise RuntimeError(
                "Cannot connect to Dexcom Share. "
                "Please check your credentials and internet connection."
            )
        logger.info("Connection test successful")

        # Startup delay
        if self.config.monitoring.startup_delay > 0:
            logger.info(
                f"Waiting {self.config.monitoring.startup_delay} seconds before "
                f"starting monitoring..."
            )
            time.sleep(self.config.monitoring.startup_delay)

        self.running = True
        logger.info("Monitoring started - Press Ctrl+C to stop")

        try:
            while self.running:
                self._poll_once()

                # Sleep until next poll
                time.sleep(self.config.monitoring.poll_interval)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop()

    def stop(self) -> None:
        """Stop the monitoring service."""
        if not self.running:
            return

        logger.info("Stopping glucose monitoring service...")
        self.running = False
        self.alert_system.shutdown()
        logger.info("Monitoring service stopped")

    def run_once(self) -> Optional[float]:
        """
        Run a single monitoring check (useful for testing).

        Returns:
            Current glucose level in mmol/L, or None if unavailable
        """
        try:
            glucose_mmol = self.dexcom_client.get_glucose_mmol()
            if glucose_mmol is not None:
                self._check_glucose_level(glucose_mmol)
            return glucose_mmol
        except Exception as e:
            logger.error(f"Error during single check: {e}")
            return None

