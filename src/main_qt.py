"""Qt-based entry point for Bear Alarm."""

import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)


def main() -> None:
    """Main entry point."""
    from src.ui_qt.app import run
    run()


if __name__ == "__main__":
    main()


