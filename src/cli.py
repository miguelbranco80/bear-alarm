"""CLI entry point for Bear Alarm - headless monitoring mode."""

import logging
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .core import load_config, GlucoseMonitor, resolve_sound_path, prevent_sleep

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Global monitor instance for signal handling
_monitor: Optional[GlucoseMonitor] = None


def signal_handler(signum: int, frame) -> None:
    """
    Handle shutdown signals gracefully.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name}, shutting down...")

    if _monitor:
        _monitor.stop()

    sys.exit(0)


def main() -> None:
    """Main entry point for CLI mode."""
    global _monitor

    logger.info("=" * 60)
    logger.info("Bear Alarm CLI - Dexcom Glucose Monitoring System")
    logger.info("=" * 60)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        
        if not config.is_configured:
            logger.error("Dexcom credentials not configured!")
            logger.error("Please set DEXCOM_USERNAME and DEXCOM_PASSWORD environment variables")
            logger.error("Or run the GUI app to configure: uv run bear-alarm")
            sys.exit(1)
        
        logger.info("Configuration loaded successfully")

        # Validate alert sound files exist
        logger.info("Validating alert sound files...")
        low_sound = resolve_sound_path(config.alerts.low_alert_sound)
        high_sound = resolve_sound_path(config.alerts.high_alert_sound)

        errors = []
        
        # Check if files exist
        if not low_sound.exists():
            errors.append(f"Low alert sound file not found: {low_sound}")
        elif not low_sound.is_file():
            errors.append(f"Low alert sound path is not a file: {low_sound}")
        elif low_sound.suffix.lower() not in ['.wav', '.mp3', '.mpeg']:
            errors.append(
                f"Low alert sound has unsupported format: {low_sound.suffix}. "
                f"Use WAV or MP3"
            )

        if not high_sound.exists():
            errors.append(f"High alert sound file not found: {high_sound}")
        elif not high_sound.is_file():
            errors.append(f"High alert sound path is not a file: {high_sound}")
        elif high_sound.suffix.lower() not in ['.wav', '.mp3', '.mpeg']:
            errors.append(
                f"High alert sound has unsupported format: {high_sound.suffix}. "
                f"Use WAV or MP3"
            )

        if errors:
            for error in errors:
                logger.error(error)
            logger.error(
                "Cannot start monitoring. Please fix the issues above."
            )
            sys.exit(1)

        logger.info(
            f"Alert sound files validated: "
            f"low={low_sound.name}, high={high_sound.name}"
        )

        # Ask user for startup delay
        default_delay_minutes = config.monitoring.startup_delay_minutes
        print()
        print("=" * 60)
        delay_input = input(
            f"Minutes to wait before starting monitoring? "
            f"[default: {default_delay_minutes}]: "
        ).strip()
        
        if delay_input == "":
            delay_minutes = default_delay_minutes
        else:
            try:
                delay_minutes = int(delay_input)
                if delay_minutes < 0:
                    logger.error("Delay cannot be negative, using 0")
                    delay_minutes = 0
            except ValueError:
                logger.error(f"Invalid input '{delay_input}', using default {default_delay_minutes}")
                delay_minutes = default_delay_minutes
        
        # Override config with user's choice
        config.monitoring.startup_delay_minutes = delay_minutes
        
        # Show when monitoring will start
        if delay_minutes > 0:
            start_time = datetime.now() + timedelta(minutes=delay_minutes)
            logger.info(
                f"Monitoring will start in {delay_minutes} minute(s) "
                f"at {start_time.strftime('%I:%M:%S %p')}"
            )
        else:
            logger.info("Starting monitoring immediately")
        
        print("=" * 60)
        print()

        # Prevent system sleep while monitoring
        prevent_sleep()

        # Create and start monitor
        _monitor = GlucoseMonitor(config)
        _monitor.start()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Run the GUI to configure: uv run bear-alarm")
        sys.exit(1)

    except ValueError as e:
        logger.error(f"Invalid configuration: {e}")
        sys.exit(1)

    except RuntimeError as e:
        logger.error(f"Failed to start monitoring: {e}")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        if _monitor:
            _monitor.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()

