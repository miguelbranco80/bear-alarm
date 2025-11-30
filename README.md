# Bear Alarm 🐻

A cross-platform glucose monitoring application for Type 1 Diabetes that connects to Dexcom Share and triggers audio alerts when glucose levels are out of range.

## ✨ Features

- **Beautiful Desktop UI** - Modern Flet-based interface with dashboard, history charts, and settings
- **Real-time Monitoring** - Connects to Dexcom Share API for live glucose data
- **SNOOZE Button** - Silence alerts for 15min, 30min, 1hr, or 2hr at any time
- **Historical Charts** - View glucose trends over 3h, 6h, 12h, 24h, 3d, or 7d
- **SQLite Database** - Stores all readings locally for historical analysis
- **Cross-Platform** - Runs on macOS, Windows, and Linux
- **Configurable Thresholds** - Set your own low and high glucose limits
- **Audio Alerts** - Customizable WAV or MP3 alert sounds

## 🚀 Quick Start

### Prerequisites

Install [uv](https://astral.sh/uv) (fast Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Run

```bash
cd bear-alarm
uv sync
uv run bear-alarm
```

On first launch, you'll be prompted to configure your Dexcom credentials in the Settings tab.

## 📦 Build Standalone App

Build a packaged application that doesn't require Python:

```bash
# macOS
./scripts/build-macos.sh
cp -r "dist/Bear Alarm.app" /Applications/

# Windows
.\scripts\build-windows.ps1

# Linux
./scripts/build-linux.sh
```

## ⚙️ Configuration

### GUI Configuration (Recommended)

Settings are configured through the Settings tab in the app. Your configuration is automatically saved to:

| Platform | Location |
|----------|----------|
| macOS | `~/Library/Application Support/BearAlarm/config.yaml` |
| Windows | `%LOCALAPPDATA%\BearAlarm\config.yaml` |
| Linux | `~/.local/share/bear-alarm/config.yaml` |

### Environment Variables

For CLI mode or automation, set environment variables:
```bash
export DEXCOM_USERNAME="your_username"
export DEXCOM_PASSWORD="your_password"
export DEXCOM_OUS="true"  # if outside US
```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| **Dexcom Username** | Your Dexcom Share email | (required) |
| **Dexcom Password** | Your Dexcom Share password | (required) |
| **Outside US** | Use non-US Dexcom server | false |
| **Low Threshold** | Alert when glucose ≤ this (mmol/L) | 3.9 |
| **High Threshold** | Alert when glucose ≥ this (mmol/L) | 10.0 |
| **Alert Interval** | Seconds between repeated alerts | 300 |
| **Poll Interval** | Seconds between glucose checks | 300 |

## 📁 Project Structure

```
bear-alarm/
├── src/
│   ├── main.py              # Entry point
│   ├── cli.py               # CLI mode (headless)
│   ├── core/                # Business logic
│   │   ├── config.py        # Configuration management
│   │   ├── paths.py         # Path resolution (dev vs packaged)
│   │   ├── dexcom_client.py
│   │   ├── monitor.py
│   │   └── alerts.py
│   ├── data/                # SQLite layer
│   │   ├── database.py
│   │   └── models.py
│   └── ui/                  # Flet UI
│       ├── app.py
│       ├── theme.py
│       └── views/
├── resources/
│   ├── defaults.yaml        # Default configuration
│   ├── sounds/              # Alert audio files
│   └── icons/               # App icons
├── scripts/                 # Build scripts
└── pyproject.toml
```

## 🗄️ Data Storage

All data is stored in the user data directory:

| Platform | Location |
|----------|----------|
| macOS | `~/Library/Application Support/BearAlarm/` |
| Windows | `%LOCALAPPDATA%\BearAlarm\` |
| Linux | `~/.local/share/bear-alarm/` |

Contents:
- `bear_alarm.db` - SQLite database with glucose readings
- `config.yaml` - User configuration

## 🔧 Troubleshooting

### "Failed to authenticate with Dexcom Share"
- Verify your Dexcom Share username and password
- Ensure Dexcom Share is enabled in your mobile app
- Enable "Outside US" if you're not in the United States

### No glucose readings
- Ensure CGM is active and transmitting
- Check Share is enabled in Dexcom app
- Verify someone is following the account

## 🖥️ CLI Mode

For headless operation (servers, etc.):
```bash
export DEXCOM_USERNAME="your_username"
export DEXCOM_PASSWORD="your_password"
uv run bear-alarm-cli
```

## ⚠️ Disclaimer

This software is not a medical device and should not replace proper medical care. Always consult healthcare professionals for diabetes management.

## 🙏 Acknowledgments

- [Flet](https://flet.dev/) - Cross-platform UI
- [pydexcom](https://github.com/gagebenne/pydexcom) - Dexcom API
- [uv](https://astral.sh/uv) - Python package manager
