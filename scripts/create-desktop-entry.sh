#!/bin/bash
# Create a .desktop file for Linux app menu integration
#
# Usage:
#   ./scripts/create-desktop-entry.sh
#
# This will create ~/.local/share/applications/bear-alarm.desktop

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Paths
BINARY_PATH="$HOME/.local/bin/bear-alarm"
ICON_PATH="$HOME/.local/share/icons/bear-alarm.png"
DESKTOP_FILE="$HOME/.local/share/applications/bear-alarm.desktop"

echo "🐻 Bear Alarm - Desktop Entry Creator"
echo "======================================"

# Check if binary exists in dist
if [ ! -f "$PROJECT_DIR/dist/bear-alarm" ]; then
    echo "❌ Build the application first: ./scripts/build-linux.sh"
    exit 1
fi

# Create directories
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.local/share/icons"
mkdir -p "$HOME/.local/share/applications"

# Copy binary
echo "📦 Installing binary..."
cp "$PROJECT_DIR/dist/bear-alarm" "$BINARY_PATH"
chmod +x "$BINARY_PATH"

# Copy icon
echo "🖼️  Installing icon..."
if [ -f "$PROJECT_DIR/resources/icons/bear-icon.png" ]; then
    cp "$PROJECT_DIR/resources/icons/bear-icon.png" "$ICON_PATH"
fi

# Create desktop entry
echo "📝 Creating desktop entry..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Bear Alarm
Comment=Dexcom glucose monitoring with audio alerts
Exec=$BINARY_PATH
Icon=$ICON_PATH
Terminal=false
Categories=Utility;Health;
Keywords=glucose;diabetes;dexcom;cgm;
StartupNotify=true
EOF

echo ""
echo "✅ Desktop entry created!"
echo ""
echo "Binary: $BINARY_PATH"
echo "Icon: $ICON_PATH"
echo "Desktop file: $DESKTOP_FILE"
echo ""
echo "Bear Alarm should now appear in your application menu."
echo "You may need to log out and log back in for it to appear."

