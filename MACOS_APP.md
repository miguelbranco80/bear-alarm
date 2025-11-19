# macOS Application Guide

## For Non-Technical Users

### How to Start Monitoring

1. **Find the app**: Look for `Bear Alarm.app` in the project folder
2. **Double-click** the app icon
3. A Terminal window will open showing the monitoring status
4. The app will start checking glucose levels every 5 minutes
5. **Alerts will play** when glucose is out of range

### How to Stop Monitoring

Just **close the Terminal window** or press `Ctrl+C` in the Terminal.

### Making It Easier to Access

#### Option 1: Add to Dock
1. Drag `Bear Alarm.app` to your Dock
2. Now you can click it from the Dock anytime

#### Option 2: Move to Applications
1. Drag `Bear Alarm.app` to your Applications folder
2. Find it in Launchpad like any other app

#### Option 3: Auto-Start at Login
1. Open **System Preferences** → **Users & Groups**
2. Click **Login Items** tab
3. Click the **+** button
4. Select `Bear Alarm.app`
5. Check **Hide** if you want it to run quietly in background

## For Developers

### Creating the App

If the app doesn't exist yet, create it:

```bash
./create-app.sh
```

This creates `Bear Alarm.app` which is a standard macOS application bundle.

### What It Does

The app is a wrapper that:
1. Changes to the project directory
2. Checks if `uv` is installed
3. Checks if `config.yaml` exists
4. Opens Terminal and runs `./run.sh`
5. Shows all logs in the Terminal window

### Structure

```
Bear Alarm.app/
├── Contents/
│   ├── Info.plist          # App metadata
│   ├── MacOS/
│   │   └── bear-alarm      # Launcher script
│   └── Resources/
│       └── AppIcon.icns    # App icon (placeholder)
```

### Customizing the Icon

To add a custom icon:
1. Create or find a `.icns` file (macOS icon format)
2. Replace `Bear Alarm.app/Contents/Resources/AppIcon.icns`
3. Run: `touch "Bear Alarm.app"` to refresh the icon cache

You can convert PNG to ICNS using:
- https://cloudconvert.com/png-to-icns
- Or use `iconutil` command-line tool

### Recreating the App

If you need to recreate it (after updates):

```bash
rm -rf "Bear Alarm.app"
./create-app.sh
```

## Troubleshooting

### "App can't be opened because it is from an unidentified developer"

1. Right-click the app and select **Open**
2. Click **Open** in the dialog
3. You only need to do this once

Or disable Gatekeeper temporarily:
```bash
xattr -cr "Bear Alarm.app"
```

### "uv is not installed" error

Install uv first:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "config.yaml not found" error

Create your configuration:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your Dexcom credentials
```

### Terminal window doesn't open

The app uses AppleScript to open Terminal. Make sure:
1. Terminal.app is installed (default on macOS)
2. You have permission to run AppleScript

### App doesn't appear in Dock

After creating the app:
1. Open Finder
2. Navigate to the project folder
3. Drag `Bear Alarm.app` to the Dock

## Notes

- The app must stay in the project folder (it needs access to the code)
- Logs appear in the Terminal window
- Closing Terminal stops the monitoring
- The app works on macOS 10.13 (High Sierra) and later

