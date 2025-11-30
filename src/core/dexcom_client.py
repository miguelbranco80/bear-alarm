"""Dexcom API client wrapper with error handling and reconnection logic."""

import logging
import time
from typing import Optional

from pydexcom import Dexcom, GlucoseReading, Region
from pydexcom.errors import (
    AccountError,
    ArgumentError,
    SessionError,
)

logger = logging.getLogger(__name__)


class DexcomClientError(Exception):
    """Base exception for Dexcom client errors."""

    pass


class DexcomClient:
    """
    Wrapper around pydexcom library with error handling and reconnection.

    This client handles authentication, session management, and provides
    robust error handling with automatic reconnection.
    """

    def __init__(self, username: str, password: str, ous: bool = False):
        """
        Initialize Dexcom client.

        Args:
            username: Dexcom Share username
            password: Dexcom Share password
            ous: True if outside US (uses different server)
        """
        self.username = username
        self.password = password
        self.region = Region.OUS if ous else Region.US
        self._client: Optional[Dexcom] = None
        self._last_connection_attempt = 0
        self._connection_retry_delay = 60  # seconds

    def _connect(self) -> None:
        """
        Establish connection to Dexcom Share.

        Raises:
            DexcomClientError: If connection fails
        """
        try:
            logger.info(f"Connecting to Dexcom Share (region: {self.region.value})...")
            self._client = Dexcom(
                username=self.username,
                password=self.password,
                region=self.region,
            )
            logger.info("Successfully connected to Dexcom Share")
            self._last_connection_attempt = time.time()
        except AccountError as e:
            logger.error(f"Account error: {e}")
            raise DexcomClientError(
                f"Failed to authenticate with Dexcom Share. "
                f"Please check your username and password: {e}"
            )
        except ArgumentError as e:
            logger.error(f"Argument error: {e}")
            raise DexcomClientError(f"Invalid arguments provided: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to Dexcom: {e}")
            raise DexcomClientError(f"Failed to connect to Dexcom Share: {e}")

    def _ensure_connected(self) -> None:
        """Ensure client is connected, reconnecting if necessary."""
        if self._client is None:
            self._connect()

    def _handle_session_error(self) -> None:
        """Handle session errors by reconnecting."""
        current_time = time.time()
        time_since_last_attempt = current_time - self._last_connection_attempt

        if time_since_last_attempt < self._connection_retry_delay:
            wait_time = self._connection_retry_delay - time_since_last_attempt
            logger.warning(
                f"Waiting {wait_time:.0f} seconds before reconnection attempt"
            )
            time.sleep(wait_time)

        logger.info("Session expired, reconnecting...")
        self._client = None
        self._connect()

    def get_current_glucose_reading(
        self, max_retries: int = 3
    ) -> Optional[GlucoseReading]:
        """
        Get the most recent glucose reading.

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            GlucoseReading object with glucose data, or None if unavailable

        Raises:
            DexcomClientError: If all retry attempts fail
        """
        self._ensure_connected()

        for attempt in range(max_retries):
            try:
                reading = self._client.get_current_glucose_reading()
                logger.debug(
                    f"Got glucose reading: {reading.mmol_l:.1f} mmol/L "
                    f"({reading.mg_dl} mg/dL) at {reading.datetime}"
                )
                return reading

            except SessionError as e:
                logger.warning(f"Session error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    self._handle_session_error()
                else:
                    raise DexcomClientError(
                        f"Failed to get glucose reading after {max_retries} attempts"
                    )

            except Exception as e:
                logger.error(f"Unexpected error getting glucose reading: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise DexcomClientError(
                        f"Failed to get glucose reading: {e}"
                    )

        return None

    def get_glucose_mmol(self) -> Optional[float]:
        """
        Get current glucose level in mmol/L.

        Returns:
            Glucose level in mmol/L, or None if unavailable

        Raises:
            DexcomClientError: If reading fails
        """
        reading = self.get_current_glucose_reading()
        if reading is None:
            return None
        return reading.mmol_l

    def get_glucose_mg_dl(self) -> Optional[float]:
        """
        Get current glucose level in mg/dL.

        Returns:
            Glucose level in mg/dL, or None if unavailable

        Raises:
            DexcomClientError: If reading fails
        """
        reading = self.get_current_glucose_reading()
        if reading is None:
            return None
        return reading.mg_dl

    def test_connection(self) -> bool:
        """
        Test connection to Dexcom Share.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self._ensure_connected()
            reading = self.get_current_glucose_reading()
            return reading is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

