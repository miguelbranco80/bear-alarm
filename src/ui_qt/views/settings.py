"""Settings view - app configuration."""

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QCheckBox, QSpinBox,
    QSlider, QGroupBox, QGridLayout, QFileDialog, QComboBox
)

from ...core import Config


class SettingsView(QWidget):
    """Application settings with auto-save."""

    def __init__(
        self,
        config: Config,
        on_save: Callable[[dict], None],
        on_test_sound: Callable[[str], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.on_test_sound = on_test_sound
        
        # Debounce timer for auto-save (saves 500ms after last change)
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save)
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)
        
        # Dexcom account
        dexcom_group = QGroupBox("Dexcom Account")
        dexcom_layout = QGridLayout(dexcom_group)
        dexcom_layout.setSpacing(12)
        
        dexcom_layout.addWidget(QLabel("Username:"), 0, 0)
        self._username = QLineEdit(self.config.dexcom.username)
        self._username.setPlaceholderText("Your Dexcom Share username")
        dexcom_layout.addWidget(self._username, 0, 1)
        
        dexcom_layout.addWidget(QLabel("Password:"), 1, 0)
        self._password = QLineEdit(self.config.dexcom.password)
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText("Your Dexcom Share password")
        dexcom_layout.addWidget(self._password, 1, 1)
        
        dexcom_layout.addWidget(QLabel("Region:"), 2, 0)
        self._region = QComboBox()
        self._region.addItems(["United States", "Outside US", "Japan"])
        region_index = {"us": 0, "ous": 1, "jp": 2}.get(self.config.dexcom.region, 0)
        self._region.setCurrentIndex(region_index)
        dexcom_layout.addWidget(self._region, 2, 1)
        
        content_layout.addWidget(dexcom_group)
        
        # Alert sounds
        sounds_group = QGroupBox("Alert Sounds")
        sounds_layout = QVBoxLayout(sounds_group)
        sounds_layout.setSpacing(12)
        
        # Low sound
        low_sound_layout = QHBoxLayout()
        low_sound_layout.addWidget(QLabel("Low Alert:"))
        self._low_sound_label = QLabel(Path(self.config.alerts.low_alert_sound).name)
        self._low_sound_label.setEnabled(False)
        low_sound_layout.addWidget(self._low_sound_label, 1)
        
        low_browse = QPushButton("Browse")
        low_browse.clicked.connect(lambda: self._browse_sound("low"))
        low_sound_layout.addWidget(low_browse)
        
        low_test = QPushButton("▶")
        low_test.setMaximumWidth(40)
        low_test.clicked.connect(lambda: self.on_test_sound(self._low_sound_path))
        low_sound_layout.addWidget(low_test)
        
        self._low_sound_path = self.config.alerts.low_alert_sound
        sounds_layout.addLayout(low_sound_layout)
        
        # High sound
        high_sound_layout = QHBoxLayout()
        high_sound_layout.addWidget(QLabel("High Alert:"))
        self._high_sound_label = QLabel(Path(self.config.alerts.high_alert_sound).name)
        self._high_sound_label.setEnabled(False)
        high_sound_layout.addWidget(self._high_sound_label, 1)
        
        high_browse = QPushButton("Browse")
        high_browse.clicked.connect(lambda: self._browse_sound("high"))
        high_sound_layout.addWidget(high_browse)
        
        high_test = QPushButton("▶")
        high_test.setMaximumWidth(40)
        high_test.clicked.connect(lambda: self.on_test_sound(self._high_sound_path))
        high_sound_layout.addWidget(high_test)
        
        self._high_sound_path = self.config.alerts.high_alert_sound
        sounds_layout.addLayout(high_sound_layout)
        
        # Alert interval
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Repeat Interval:"))
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 30)
        self._interval_spin.setValue(self.config.alerts.alert_interval // 60)
        self._interval_spin.setSuffix(" min")
        interval_layout.addWidget(self._interval_spin)
        interval_layout.addStretch()
        sounds_layout.addLayout(interval_layout)
        
        content_layout.addWidget(sounds_group)
        
        # Monitoring
        monitor_group = QGroupBox("Monitoring")
        monitor_layout = QVBoxLayout(monitor_group)
        monitor_layout.setSpacing(12)
        
        # Poll interval
        poll_layout = QHBoxLayout()
        poll_layout.addWidget(QLabel("Check Interval:"))
        self._poll_spin = QSpinBox()
        self._poll_spin.setRange(1, 15)
        self._poll_spin.setValue(self.config.monitoring.poll_interval // 60)
        self._poll_spin.setSuffix(" min")
        poll_layout.addWidget(self._poll_spin)
        poll_layout.addStretch()
        monitor_layout.addLayout(poll_layout)
        
        # Startup delay
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Startup Delay:"))
        self._delay_spin = QSpinBox()
        self._delay_spin.setRange(0, 60)
        self._delay_spin.setValue(self.config.monitoring.startup_delay_minutes)
        self._delay_spin.setSuffix(" min")
        delay_layout.addWidget(self._delay_spin)
        delay_layout.addStretch()
        monitor_layout.addLayout(delay_layout)
        
        # Volume warning
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume Warning:"))
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(10, 100)
        self._volume_slider.setValue(self.config.alerts.min_volume)
        self._volume_slider.setTickInterval(10)
        volume_layout.addWidget(self._volume_slider)
        self._volume_label = QLabel(f"{self.config.alerts.min_volume}%")
        self._volume_label.setMinimumWidth(40)
        self._volume_slider.valueChanged.connect(lambda v: self._volume_label.setText(f"{v}%"))
        volume_layout.addWidget(self._volume_label)
        monitor_layout.addLayout(volume_layout)
        
        content_layout.addWidget(monitor_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Connect all inputs to auto-save
        self._username.textChanged.connect(self._schedule_save)
        self._password.textChanged.connect(self._schedule_save)
        self._region.currentIndexChanged.connect(self._schedule_save)
        self._interval_spin.valueChanged.connect(self._schedule_save)
        self._poll_spin.valueChanged.connect(self._schedule_save)
        self._delay_spin.valueChanged.connect(self._schedule_save)
        self._volume_slider.valueChanged.connect(self._schedule_save)
    
    def _schedule_save(self) -> None:
        """Schedule auto-save after a short delay."""
        self._save_timer.start(500)  # Save 500ms after last change

    def _browse_sound(self, sound_type: str) -> None:
        """Browse for sound file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {sound_type.title()} Alert Sound",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.m4a)"
        )
        if file_path:
            if sound_type == "low":
                self._low_sound_path = file_path
                self._low_sound_label.setText(Path(file_path).name)
            else:
                self._high_sound_path = file_path
                self._high_sound_label.setText(Path(file_path).name)
            self._schedule_save()

    def _save(self) -> None:
        """Save settings."""
        region_codes = ["us", "ous", "jp"]
        new_config = {
            "dexcom": {
                "username": self._username.text(),
                "password": self._password.text(),
                "region": region_codes[self._region.currentIndex()],
            },
            "alerts": {
                "low_alert_sound": self._low_sound_path,
                "high_alert_sound": self._high_sound_path,
                "alert_interval": self._interval_spin.value() * 60,
                "min_volume": self._volume_slider.value(),
            },
            "monitoring": {
                "poll_interval": self._poll_spin.value() * 60,
                "startup_delay_minutes": self._delay_spin.value(),
            },
        }
        self.on_save(new_config)

    def update_config(self, config: Config) -> None:
        """Update with new config."""
        self.config = config
        self._username.setText(config.dexcom.username)
        self._password.setText(config.dexcom.password)
        region_index = {"us": 0, "ous": 1, "jp": 2}.get(config.dexcom.region, 0)
        self._region.setCurrentIndex(region_index)
        self._low_sound_path = config.alerts.low_alert_sound
        self._low_sound_label.setText(Path(config.alerts.low_alert_sound).name)
        self._high_sound_path = config.alerts.high_alert_sound
        self._high_sound_label.setText(Path(config.alerts.high_alert_sound).name)
        self._interval_spin.setValue(config.alerts.alert_interval // 60)
        self._poll_spin.setValue(config.monitoring.poll_interval // 60)
        self._delay_spin.setValue(config.monitoring.startup_delay_minutes)
        self._volume_slider.setValue(config.alerts.min_volume)

