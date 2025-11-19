#!/bin/bash
# Bear Alarm - Glucose Monitor Launcher

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    osascript -e 'display dialog "uv is not installed. Please install it first:\n\ncurl -LsSf https://astral.sh/uv/install.sh | sh" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    osascript -e 'display dialog "config.yaml not found. Please create it from config.yaml.example" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Run the monitor
uv run python -m src.main
