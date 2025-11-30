#!/bin/bash
# Build Bear Alarm for macOS
#
# This creates a .app bundle that can be dragged to Applications.
#
# Prerequisites:
#   - Python 3.10+
#   - uv (https://astral.sh/uv)
#
# Usage:
#   ./scripts/build-macos.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "🐻 Bear Alarm - macOS Build"
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
    --name "Bear Alarm" \
    --product-name "Bear Alarm" \
    --product-version "0.2.0" \
    --bundle-id "com.bearalarm.app" \
    --icon "resources/icons/AppIcon.icns" \
    --add-data "resources:resources"

# Check if successful
if [ -d "dist/Bear Alarm.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📱 App location: dist/Bear Alarm.app"
    echo ""
    echo "To install:"
    echo "  cp -r 'dist/Bear Alarm.app' /Applications/"
    echo ""
    echo "Or drag 'dist/Bear Alarm.app' to your Applications folder"
else
    echo "❌ Build failed!"
    exit 1
fi

