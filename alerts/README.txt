Alert Sounds Directory
======================

Place your custom alert sound files in this directory.

The default configuration expects a file named "alarm.wav" in this directory.

You can use different sound files for low and high glucose alerts by
configuring them in config.yaml:

  alerts:
    low_alert_sound: "alerts/low_alarm.mp3"
    high_alert_sound: "alerts/high_alarm.wav"

To add your own sound:
1. Find or create a WAV or MP3 file
2. Copy it to this directory
3. Update config.yaml to reference the filename

Supported formats:
- WAV (recommended for reliability)
- MP3 (requires pygame with MP3 support)

