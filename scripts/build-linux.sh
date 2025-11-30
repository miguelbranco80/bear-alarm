#!/bin/bash
# Build Bear Alarm for Linux
#
# This creates a standalone binary that can be run on most Linux distributions.
#
# Prerequisites:
#   - Python 3.10+
#   - uv (https://astral.sh/uv)
#
# Usage:
#   ./scripts/build-linux.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🐻 Bear Alarm - Linux Build"
echo "================================"

# Check uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is required. Install with:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/

# Build with flet pack
echo "🔨 Building application..."
uv run python -m flet pack \
    src/main.py \
    --name "bear-alarm" \
    --product-name "Bear Alarm" \
    --product-version "0.2.0" \
    --icon "resources/icons/bear-icon.png" \
    --add-data "resources:resources"

# Check if successful
if [ -f "dist/bear-alarm" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📱 Binary location: dist/bear-alarm"
    echo ""
    echo "To install system-wide:"
    echo "  sudo cp dist/bear-alarm /usr/local/bin/"
    echo ""
    echo "To create a .desktop file for your app menu:"
    echo "  ./scripts/create-desktop-entry.sh"
    
    # Make executable
    chmod +x dist/bear-alarm
else
    echo "❌ Build failed!"
    exit 1
fi

