"""Main entry point for Bear Alarm - launches the GUI application."""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point - launches the GUI application."""
    logger.info("=" * 60)
    logger.info("Bear Alarm - Dexcom Glucose Monitoring System")
    logger.info("=" * 60)
    
    try:
        from .ui import BearAlarmApp
        
        app = BearAlarmApp()
        app.run()
        
    except ImportError as e:
        logger.error(f"Failed to import UI components: {e}")
        logger.error("Make sure Flet is installed: pip install flet")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
