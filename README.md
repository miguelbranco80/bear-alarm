# Bear Alarm 🐻

A Python-based glucose monitoring system for Type 1 Diabetes that connects to Dexcom Share and triggers audio alerts when glucose levels are out of range.

## Features

- **Real-time monitoring** via Dexcom Share API (pydexcom)
- **Configurable thresholds** for low and high glucose levels (mmol/L)
- **Audio alerts** with customizable WAV or MP3 files
- **Repeating alerts** at configurable intervals until glucose normalizes
- **Docker support** for easy deployment and 24/7 operation
- **Automatic reconnection** with robust error handling
- **Environment variable overrides** for sensitive credentials

## Requirements

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (for local development) or Docker
- Dexcom Share account with username/password
- Audio output device (for alerts)

## Quick Start

### 1. Clone and Setup

```bash
cd bear-alarm
```

### 2. Create Configuration

Copy the example configuration and edit with your details:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` and add your Dexcom Share credentials:

```yaml
dexcom:
  username: "your_dexcom_share_username@example.com"
  password: "your_dexcom_share_password"
  ous: false  # Set to true if outside US

alerts:
  low_threshold: 3.0    # mmol/L
  high_threshold: 13.0  # mmol/L
  alert_sound: "alerts/alarm.wav"
  alert_interval: 300   # seconds
```

### 3. Add Alert Sound

Place your custom audio file (WAV or MP3) in the `alerts/` directory, or use the provided default `alarm.wav`.

**Supported formats:**
- WAV (recommended for reliability)
- MP3 (requires pygame with MP3 support)

### 4. Run with Docker (Recommended)

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### 5. Run Locally

**Option A: macOS App (Easiest for non-technical users)**

```bash
# Install SDL2
brew install sdl2

# Install Python dependencies (first time only)
uv sync

# Create the macOS application
./create-app.sh
```

Then double-click `Bear Alarm.app` to start monitoring. A Terminal window will open showing logs.

**Note:** The first time you run the app, it will automatically install dependencies if needed.

**Option B: Command Line**

```bash
# Install dependencies with uv
uv sync

# Run the monitor
uv run python -m src.main
```

Or using the installed script:

```bash
uv run bear-alarm
```

## Configuration

### Configuration File (`config.yaml`)

| Section | Option | Description | Default |
|---------|--------|-------------|---------|
| `dexcom.username` | Required | Dexcom Share username (email) | - |
| `dexcom.password` | Required | Dexcom Share password | - |
| `dexcom.ous` | Optional | Set to `true` if outside US | `false` |
| `alerts.low_threshold` | Optional | Low glucose threshold (mmol/L) | `3.0` |
| `alerts.high_threshold` | Optional | High glucose threshold (mmol/L) | `13.0` |
| `alerts.low_alert_sound` | Optional | Path to low alert WAV file | `alerts/alarm.wav` |
| `alerts.high_alert_sound` | Optional | Path to high alert WAV file | `alerts/alarm.wav` |
| `alerts.alert_interval` | Optional | Seconds between repeated alerts | `300` |
| `monitoring.poll_interval` | Optional | Seconds between glucose checks | `300` |
| `monitoring.startup_delay_minutes` | Optional | Minutes before first check | `0` |

### Environment Variables

You can override configuration with environment variables:

```bash
export DEXCOM_USERNAME="your_username"
export DEXCOM_PASSWORD="your_password"
export DEXCOM_OUS="false"
```

This is useful for Docker secrets or CI/CD pipelines.

## Docker Deployment

### Docker Compose (Recommended)

The `docker-compose.yml` file is pre-configured for easy deployment:

```yaml
services:
  bear-alarm:
    build: .
    restart: unless-stopped
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./alerts:/app/alerts:ro
    devices:
      - /dev/snd:/dev/snd  # Audio device access
```

### Commands

```bash
# Start in background
docker-compose up -d

# View real-time logs
docker-compose logs -f

# Stop service
docker-compose down

# Restart after config change
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build
```

### Audio in Docker

The container needs access to your audio device. This is configured in `docker-compose.yml`:

```yaml
devices:
  - /dev/snd:/dev/snd
```

If audio doesn't work, you may need to:

1. Uncomment `privileged: true` in `docker-compose.yml`
2. Ensure your user is in the `audio` group: `sudo usermod -aG audio $USER`
3. Restart Docker daemon

## How It Works

1. **Startup**: Asks how many minutes to wait before starting (useful for meal timing)
2. **Authentication**: Connects to Dexcom Share using your credentials
3. **Polling**: Checks glucose levels every 5 minutes (configurable)
4. **Threshold Check**: Compares reading against configured thresholds
5. **Alert Trigger**: 
   - If glucose ≤ low threshold: plays low alert sound
   - If glucose ≥ high threshold: plays high alert sound
   - If glucose returns to normal: stops alerts
6. **Repeat**: Continues playing alerts at configured intervals until glucose normalizes
7. **Stay Awake**: Uses `caffeinate` to prevent Mac from sleeping during monitoring

### Alert Priority

- Low glucose alerts take priority over high glucose alerts
- Alerts repeat every 5 minutes (configurable) until resolved
- Only one alert plays at a time

## Troubleshooting

### "Configuration file not found"

Create `config.yaml` from the example:

```bash
cp config.yaml.example config.yaml
```

### "Failed to authenticate with Dexcom Share"

- Verify your Dexcom Share username and password
- Ensure Dexcom Share is enabled in your Dexcom mobile app
- Check if you need to set `ous: true` (for non-US users)

### "Alert sound file not found" or "Cannot start monitoring"

The application validates alert sound files at startup and will not start if they're missing or invalid.

- Ensure `alerts/alarm.wav` (or your configured sound file) exists
- Check the path in `config.yaml` is correct
- Verify the file is a valid WAV or MP3 format (`.wav`, `.mp3`, `.mpeg`)
- Make sure the path points to a file, not a directory

### Audio not playing in Docker

1. Check audio device is accessible:
   ```bash
   docker-compose exec bear-alarm ls -l /dev/snd
   ```

2. Verify user is in audio group on host:
   ```bash
   groups $USER
   ```

3. Try enabling privileged mode in `docker-compose.yml`:
   ```yaml
   privileged: true
   ```

### Connection errors

- Check internet connection
- Verify Dexcom Share service is operational
- Review logs for specific error messages:
  ```bash
  docker-compose logs -f
  ```

### No glucose readings available

- Ensure your Dexcom CGM is active and transmitting
- Check that Share is enabled in the Dexcom mobile app
- Verify someone is following the account (Share requires a follower)

### Mac goes to sleep / monitoring stops

The app uses `caffeinate` to prevent sleep automatically. If monitoring stops:
- Make sure the Terminal window stays open
- Check that the app is still running (look for the Terminal window)
- The display can sleep (screen off) but the Mac stays awake

## macOS Application

### Creating a Double-Clickable App

For non-technical users, you can create a macOS application bundle:

```bash
./create-app.sh
```

This creates `Bear Alarm.app` that can be:
- **Double-clicked** to start monitoring
- **Moved to Applications folder** for easy access
- **Added to Dock** for quick launching
- **Added to Login Items** to start automatically at login

When you double-click the app:
1. A Terminal window opens automatically
2. Shows real-time logs
3. Close the window (or press Ctrl+C) to stop monitoring

### Adding to Login Items (Auto-start)

1. Open **System Preferences** → **Users & Groups**
2. Click **Login Items** tab
3. Click **+** button
4. Select `Bear Alarm.app`
5. Check **Hide** if you want it to run in background

## Development

### Local Development Setup

This project uses [uv](https://github.com/astral-sh/uv) for fast, reliable Python package management.

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Run the application
uv run python -m src.main

# Or use the installed script
uv run bear-alarm

# Run tests (if implemented)
uv run pytest
```

**Alternative with pip:**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Run the monitor
python -m src.main
```

### Project Structure

```
bear-alarm/
├── src/
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration management
│   ├── dexcom_client.py  # Dexcom API wrapper
│   ├── monitor.py        # Monitoring service
│   └── alerts.py         # Alert system
├── alerts/               # Alert sound files
├── config.yaml          # User configuration (gitignored)
├── config.yaml.example  # Configuration template
├── pyproject.toml       # Python dependencies
├── Dockerfile           # Docker image definition
└── docker-compose.yml   # Docker Compose configuration
```

## Security Notes

- `config.yaml` is gitignored to protect credentials
- Never commit your actual `config.yaml` with credentials
- Use environment variables for sensitive data in production
- Consider using Docker secrets for enhanced security

## License

This project is provided as-is for personal use in managing Type 1 Diabetes.

## Disclaimer

This software is not a medical device and should not be used as a replacement for proper medical care. Always consult with healthcare professionals for diabetes management. The alerts are supplementary and should not be relied upon as the sole means of glucose monitoring.

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review logs for error messages
3. Verify Dexcom Share is working via the mobile app
4. Ensure all configuration is correct

## Acknowledgments

- Built with [pydexcom](https://github.com/gagebenne/pydexcom) by Gage Benne
- Uses Dexcom Share API for real-time glucose data

