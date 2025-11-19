"""Main entry point for Bear Alarm glucose monitoring service."""

import logging
import signal
import sys
from pathlib import Path
from typing import Optional

from .config import load_config_with_env_override
from .monitor import GlucoseMonitor

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
    """Main entry point for the application."""
    global _monitor

    logger.info("=" * 60)
    logger.info("Bear Alarm - Dexcom Glucose Monitoring System")
    logger.info("=" * 60)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Load configuration
        logger.info("Loading configuration...")
        config_path = sys.argv[1] if len(sys.argv) > 1 else None
        config = load_config_with_env_override(config_path)
        logger.info("Configuration loaded successfully")

        # Validate alert sound files exist
        logger.info("Validating alert sound files...")
        low_sound = Path(config.alerts.low_alert_sound)
        high_sound = Path(config.alerts.high_alert_sound)

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

        # Create and start monitor
        _monitor = GlucoseMonitor(config)
        _monitor.start()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        logger.error(
            "Please create a config.yaml file based on config.yaml.example"
        )
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

