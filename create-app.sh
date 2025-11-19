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

# Get the directory where the .app is located (the project directory)
APP_PATH="$(cd "$(dirname "$0")/../../.." && pwd)"

# Open Terminal and run the monitor
osascript <<APPLESCRIPT
tell application "Terminal"
    do script "cd '$APP_PATH' && ./run.sh; echo ''; echo 'Press any key to close...'; read -n 1; exit"
    activate
end tell
APPLESCRIPT
EOF

chmod +x "$APP_DIR/Contents/MacOS/bear-alarm"

# Apply bear icon if bear-icon.png exists
if [ -f "bear-icon.png" ]; then
    echo "Applying bear icon..."
    ICONSET="AppIcon.iconset"
    mkdir -p "$ICONSET"
    
    sips -z 16 16 bear-icon.png --out "$ICONSET/icon_16x16.png" > /dev/null 2>&1
    sips -z 32 32 bear-icon.png --out "$ICONSET/icon_16x16@2x.png" > /dev/null 2>&1
    sips -z 32 32 bear-icon.png --out "$ICONSET/icon_32x32.png" > /dev/null 2>&1
    sips -z 64 64 bear-icon.png --out "$ICONSET/icon_32x32@2x.png" > /dev/null 2>&1
    sips -z 128 128 bear-icon.png --out "$ICONSET/icon_128x128.png" > /dev/null 2>&1
    sips -z 256 256 bear-icon.png --out "$ICONSET/icon_128x128@2x.png" > /dev/null 2>&1
    sips -z 256 256 bear-icon.png --out "$ICONSET/icon_256x256.png" > /dev/null 2>&1
    sips -z 512 512 bear-icon.png --out "$ICONSET/icon_256x256@2x.png" > /dev/null 2>&1
    sips -z 512 512 bear-icon.png --out "$ICONSET/icon_512x512.png" > /dev/null 2>&1
    sips -z 1024 1024 bear-icon.png --out "$ICONSET/icon_512x512@2x.png" > /dev/null 2>&1
    
    iconutil -c icns "$ICONSET" -o "$APP_DIR/Contents/Resources/AppIcon.icns"
    rm -rf "$ICONSET"
    
    # Force macOS to recognize the new icon
    touch "$APP_DIR"
    touch "$APP_DIR/Contents/Info.plist"
    
    echo "Bear icon applied 🐻"
else
    # Create empty placeholder
    touch "$APP_DIR/Contents/Resources/AppIcon.icns"
    echo "No bear-icon.png found, using default icon"
fi

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
echo "If the bear icon doesn't appear, run: killall Finder"
echo ""

