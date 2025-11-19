#!/bin/bash
# Create macOS Application Bundle for Bear Alarm

APP_NAME="Bear Alarm"
APP_DIR="$APP_NAME.app"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Creating $APP_NAME.app..."

# Create app bundle structure
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>bear-alarm</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.bearalarm.monitor</string>
    <key>CFBundleName</key>
    <string>Bear Alarm</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create launcher script
cat > "$APP_DIR/Contents/MacOS/bear-alarm" << 'EOF'
#!/bin/bash

# Get the project directory (parent of .app)
PROJECT_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
cd "$PROJECT_DIR"

# Open Terminal and run the monitor
osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "cd '$PROJECT_DIR' && ./run.sh; echo ''; echo 'Press any key to close...'; read -n 1; exit"
end tell
APPLESCRIPT
EOF

chmod +x "$APP_DIR/Contents/MacOS/bear-alarm"

# Create a simple icon (optional - you can replace this with a custom icon later)
# For now, we'll create a placeholder
cat > "$APP_DIR/Contents/Resources/AppIcon.icns" << 'EOF'
EOF

echo ""
echo "✅ Created $APP_NAME.app"
echo ""
echo "To use it:"
echo "1. Double-click '$APP_NAME.app' to start monitoring"
echo "2. A Terminal window will open showing the logs"
echo "3. Close the Terminal window (or press Ctrl+C) to stop"
echo ""
echo "You can:"
echo "- Move '$APP_NAME.app' to your Applications folder"
echo "- Drag it to your Dock for quick access"
echo "- Add it to Login Items to start automatically"
echo ""

