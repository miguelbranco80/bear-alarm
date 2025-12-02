# Bear Alarm 🐻

A macOS glucose monitoring application for Type 1 Diabetes that connects to Dexcom Share and triggers audio alerts when glucose levels are out of range.

## ✨ Features

- **Native macOS UI** - Built with Qt (PySide6) for a native experience
- **Real-time Monitoring** - Connects to Dexcom Share API for live glucose data
- **Smart Alerts** - Configurable thresholds with persistence timers
- **Snooze** - Silence alerts for 15min, 30min, 1hr, or 2hr
- **Historical Charts** - View glucose trends over 3h, 6h, 12h, 24h, 3d, or 7d
- **Emergency Contacts** - Auto-message via iMessage on alerts
- **FaceTime Integration** - Quick call buttons for emergency contacts
- **Schedules** - Different alert rules for different times of day
- **System Integration** - Prevents sleep while monitoring, volume warnings

## 🚀 Quick Start

### Prerequisites

Install [uv](https://astral.sh/uv) (fast Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Run (Development)

```bash
cd bear-alarm
uv sync
uv run bear-alarm
```

On first launch, configure your Dexcom credentials in the Settings tab.

## 📦 Build Standalone App

Build a packaged `.app` that doesn't require Python:

```bash
# Install PyInstaller if needed
uv pip install pyinstaller

# Build
python scripts/build.py

# Install
cp -r "dist/Bear Alarm.app" /Applications/
```

## ⚙️ Configuration

Settings are configured through the app's Settings and Rules tabs. Configuration is saved to:

```
~/Library/Application Support/BearAlarm/config.yaml
```

### Environment Variables (optional)

For automation or CI:
```bash
export DEXCOM_USERNAME="your_username"
export DEXCOM_PASSWORD="your_password"
export DEXCOM_OUS="true"  # if outside US
```

## 📁 Project Structure

```
bear-alarm/
├── src/
│   ├── main_qt.py           # Qt app entry point
│   ├── cli.py               # CLI mode (headless)
│   ├── core/                # Business logic
│   │   ├── config.py        # Configuration (Pydantic)
│   │   ├── paths.py         # Path resolution
│   │   ├── dexcom_client.py # Dexcom Share API
│   │   ├── alerts.py        # Audio alerts
│   │   ├── system.py        # macOS integration
│   │   └── emergency.py     # FaceTime/iMessage
│   ├── data/                # SQLite layer
│   │   ├── database.py
│   │   └── models.py
│   └── ui_qt/               # Qt UI
│       ├── app.py           # Main window
│       ├── theme.py
│       └── views/           # Dashboard, History, etc.
├── resources/
│   ├── sounds/              # Alert audio files
│   └── icons/               # App icons
├── scripts/
│   └── build.py             # macOS build script
└── pyproject.toml
```

## 🗄️ Data Storage

All data is stored in:
```
~/Library/Application Support/BearAlarm/
```

Contents:
- `bear_alarm.db` - SQLite database with glucose readings
- `config.yaml` - User configuration

## 🖥️ CLI Mode

For headless operation (e.g., on a server):
```bash
export DEXCOM_USERNAME="your_username"
export DEXCOM_PASSWORD="your_password"
uv run bear-alarm-cli
```

Note: Audio alerts and iMessage/FaceTime features require macOS.

## ⚠️ Disclaimer

This software is not a medical device and should not replace proper medical care. Always consult healthcare professionals for diabetes management.

## 🙏 Acknowledgments

- [PySide6](https://doc.qt.io/qtforpython/) - Qt for Python
- [pydexcom](https://github.com/gagebenne/pydexcom) - Dexcom API
- [uv](https://astral.sh/uv) - Python package manager
