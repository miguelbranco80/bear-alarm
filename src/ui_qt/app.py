"""Main Qt application for Bear Alarm."""

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QSystemTrayIcon, QMenu,
    QMessageBox, QFrame
)
from PySide6.QtGui import QIcon, QAction, QCloseEvent

from .theme import apply_theme, STYLESHEET
from .views import DashboardView, HistoryView, RulesView, ContactsView, SettingsView
from ..core import (
    Config, load_config, save_config, DexcomClient, DexcomClientError,
    AlertSystem, prevent_sleep, allow_sleep, check_volume_status,
    resolve_sound_path, call_facetime,
)
from ..data import Database
from ..data.models import TrendDirection

logger = logging.getLogger(__name__)


class BearAlarmApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        
        self.config: Optional[Config] = None
        self.db: Optional[Database] = None
        self.dexcom_client: Optional[DexcomClient] = None
        self.alert_system: Optional[AlertSystem] = None
        
        self._stop_monitoring = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        self._is_snoozed = False
        self._snooze_until: Optional[datetime] = None
        self._current_glucose: Optional[float] = None
        
        # Persistence tracking for smart alerts
        self._last_low_alert_start_time: Optional[datetime] = None
        self._last_high_alert_start_time: Optional[datetime] = None
        
        self._init_app()

    def _init_app(self) -> None:
        """Initialize the application."""
        self.setWindowTitle("Bear Alarm")
        self.setMinimumSize(520, 500)
        self.resize(550, 580)
        
        # Set app icon
        from ..core.paths import get_resources_dir
        icon_path = get_resources_dir() / "icons" / "bear-icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Initialize components
        self._init_database()
        self._init_config()
        self._init_dexcom()
        self._init_alerts()
        
        # Build UI
        self._build_ui()
        self._setup_tray()
        self._setup_timers()
        
        # Start monitoring
        prevent_sleep()
        self._start_monitoring()

    def _init_database(self) -> None:
        """Initialize database."""
        try:
            self.db = Database()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def _init_config(self) -> None:
        """Load configuration."""
        self.config = load_config()
        logger.info("Configuration loaded")

    def _init_dexcom(self) -> None:
        """Initialize Dexcom client."""
        if self.config and self.config.is_configured:
            try:
                self.dexcom_client = DexcomClient(
                    username=self.config.dexcom.username,
                    password=self.config.dexcom.password,
                    region=self.config.dexcom.region,
                )
                logger.info("Dexcom client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Dexcom client: {e}")

    def _init_alerts(self) -> None:
        """Initialize alert system."""
        if self.config:
            try:
                self.alert_system = AlertSystem(
                    low_alert_sound=str(self.config.alerts.get_low_sound_path()),
                    high_alert_sound=str(self.config.alerts.get_high_sound_path()),
                    alert_interval=self.config.alerts.alert_interval,
                )
                logger.info("Alert system initialized")
            except Exception as e:
                logger.error(f"Failed to initialize alert system: {e}")

    def _build_ui(self) -> None:
        """Build the main UI."""
        # Use native toolbar
        from PySide6.QtWidgets import QToolBar, QStatusBar
        from PySide6.QtGui import QAction
        
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)
        
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut("Ctrl+R")
        refresh_action.triggered.connect(self._manual_refresh)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self._confirm_quit)
        toolbar.addAction(quit_action)
        
        # Status bar for volume warning
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._volume_warning = QLabel("")
        self._status_bar.addPermanentWidget(self._volume_warning)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Tabs
        self._tabs = QTabWidget()
        
        # Dashboard
        self._dashboard = DashboardView(
            on_snooze=self._handle_snooze,
            on_cancel_snooze=self._handle_cancel_snooze,
            on_call_contact=self._handle_call_contact,
        )
        self._tabs.addTab(self._dashboard, "Dashboard")
        
        # History
        self._history = HistoryView(
            get_readings=lambda hours: self.db.get_readings_for_chart(hours) if self.db else [],
            get_stats=lambda hours: self.db.get_stats(hours) if self.db else {},
        )
        self._tabs.addTab(self._history, "History")
        
        # Rules
        self._rules = RulesView(
            config=self.config,
            on_save=self._handle_save_settings,
        )
        self._tabs.addTab(self._rules, "Rules")
        
        # Contacts
        self._contacts = ContactsView(
            config=self.config,
            on_save=self._handle_save_settings,
            on_call=self._handle_call_contact,
        )
        self._tabs.addTab(self._contacts, "Contacts")
        
        # Settings
        self._settings = SettingsView(
            config=self.config,
            on_save=self._handle_save_settings,
            on_test_sound=self._handle_test_sound,
        )
        self._tabs.addTab(self._settings, "Settings")
        
        # Tab change handler
        self._tabs.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self._tabs)
        
        # Update contacts on dashboard
        if self.config:
            self._dashboard.update_contacts(self.config.alerts.emergency_contacts)

    def _setup_tray(self) -> None:
        """Setup system tray."""
        self._tray = QSystemTrayIcon(self)
        
        # Load icon from resources
        from ..core.paths import get_resources_dir
        icon_path = get_resources_dir() / "icons" / "bear-icon.png"
        icon = QIcon(str(icon_path))
        if icon.isNull():
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        self._tray.setIcon(icon)
        self.setWindowIcon(icon)
        
        # Tray menu
        menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self._show_window)
        menu.addAction(show_action)
        
        menu.addSeparator()
        
        snooze_menu = menu.addMenu("Snooze")
        for minutes, label in [(15, "15 minutes"), (30, "30 minutes"), (60, "1 hour"), (120, "2 hours")]:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, m=minutes: self._handle_snooze(m))
            snooze_menu.addAction(action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._confirm_quit)
        menu.addAction(quit_action)
        
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _setup_timers(self) -> None:
        """Setup periodic timers."""
        # Volume check timer (every 2 seconds)
        self._volume_timer = QTimer(self)
        self._volume_timer.timeout.connect(self._check_volume)
        self._volume_timer.start(2000)

    def _start_monitoring(self) -> None:
        """Start glucose monitoring thread."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Monitoring started")

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        # Initial delay
        if self.config and self.config.monitoring.startup_delay > 0:
            delay = self.config.monitoring.startup_delay
            logger.info(f"Startup delay: {delay}s")
            self._stop_monitoring.wait(timeout=delay)
        
        while not self._stop_monitoring.is_set():
            self._fetch_glucose()
            
            poll_interval = self.config.monitoring.poll_interval if self.config else 300
            self._stop_monitoring.wait(timeout=poll_interval)

    def _fetch_glucose(self) -> None:
        """Fetch current glucose reading."""
        if not self.dexcom_client:
            return
        
        try:
            reading = self.dexcom_client.get_current_glucose_reading()
            if not reading:
                return
            
            glucose_mmol = reading.mmol_l
            glucose_mgdl = reading.mg_dl
            
            # Try to get trend direction
            trend_direction = None
            trend_arrow = "→"
            try:
                trend_direction = TrendDirection(reading.trend_description)
                trend_arrow = trend_direction.arrow
            except (ValueError, Exception):
                # Dexcom returns various trend descriptions, try to map them
                trend_map = {
                    "steady": "→", "flat": "→",
                    "rising": "↗", "fortyFiveUp": "↗",
                    "falling": "↘", "fortyFiveDown": "↘",
                    "risingQuickly": "⬆", "singleUp": "⬆",
                    "fallingQuickly": "⬇", "singleDown": "⬇",
                    "risingRapidly": "⬆⬆", "doubleUp": "⬆⬆",
                    "fallingRapidly": "⬇⬇", "doubleDown": "⬇⬇",
                }
                trend_desc = reading.trend_description.lower() if reading.trend_description else ""
                trend_arrow = trend_map.get(trend_desc, "→")
            
            self._current_glucose = glucose_mmol
            
            # Store in database
            if self.db:
                self.db.add_reading(
                    glucose_mmol=glucose_mmol,
                    glucose_mgdl=glucose_mgdl,
                    trend=trend_direction,
                )
            
            # Update UI with actual reading timestamp
            reading_time = reading.datetime
            self._dashboard.update_glucose(glucose_mmol, trend_arrow, reading_time)
            
            # Check thresholds
            self._check_thresholds(glucose_mmol)
            
            logger.info(f"Glucose: {glucose_mmol:.1f} mmol/L {trend_arrow}")
            
        except DexcomClientError as e:
            logger.error(f"Dexcom error: {e}")
            self._dashboard.update_connection_status(False, f"Error: {e}")
        except Exception as e:
            logger.error(f"Error fetching glucose: {e}")

    def _check_thresholds(self, glucose_mmol: float) -> None:
        """Check glucose thresholds and trigger alerts."""
        if not self.config or not self.alert_system:
            return
        
        low = self.config.alerts.low_threshold
        high = self.config.alerts.high_threshold
        urgent_low = self.config.alerts.urgent_low
        low_persist = self.config.alerts.low_persist_minutes
        high_persist = self.config.alerts.high_persist_minutes
        
        now = datetime.now()
        
        # Urgent low - immediate alert, bypasses snooze
        if glucose_mmol <= urgent_low:
            logger.critical(f"URGENT LOW: {glucose_mmol:.1f}")
            self.alert_system.trigger_low_alert()
            self._last_low_alert_start_time = now
            self._last_high_alert_start_time = None
            return
        
        # Check snooze
        if self._is_snoozed and self._snooze_until:
            if now >= self._snooze_until:
                self._is_snoozed = False
                self._snooze_until = None
                self._dashboard.update_snooze_state(None)
            else:
                return
        
        # Low glucose with persistence
        if glucose_mmol <= low:
            if self._last_low_alert_start_time is None:
                self._last_low_alert_start_time = now
            
            elapsed = (now - self._last_low_alert_start_time).total_seconds() / 60
            if elapsed >= low_persist:
                logger.warning(f"LOW (persistent): {glucose_mmol:.1f}")
                self.alert_system.trigger_low_alert()
            else:
                self.alert_system.clear_alert()
            self._last_high_alert_start_time = None
        
        # High glucose with persistence
        elif glucose_mmol >= high:
            if self._last_high_alert_start_time is None:
                self._last_high_alert_start_time = now
            
            elapsed = (now - self._last_high_alert_start_time).total_seconds() / 60
            if elapsed >= high_persist:
                logger.warning(f"HIGH (persistent): {glucose_mmol:.1f}")
                self.alert_system.trigger_high_alert()
            else:
                self.alert_system.clear_alert()
            self._last_low_alert_start_time = None
        
        # Normal range
        else:
            self.alert_system.clear_alert()
            self._last_low_alert_start_time = None
            self._last_high_alert_start_time = None

    def _check_volume(self) -> None:
        """Check system volume."""
        if not self.config:
            return
        
        is_ok, message = check_volume_status(self.config.alerts.min_volume)
        
        if is_ok:
            self._volume_warning.setText("")
        else:
            self._volume_warning.setText(f"⚠️ {message}")

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change."""
        if index == 1:  # History
            self._history.refresh_data()
        elif index == 2:  # Rules
            self._rules.refresh_ui()
        elif index == 3:  # Contacts
            self._contacts.refresh_ui()

    def _handle_snooze(self, minutes: int) -> None:
        """Handle snooze request."""
        self._is_snoozed = True
        self._snooze_until = datetime.now() + timedelta(minutes=minutes)
        self._dashboard.update_snooze_state(self._snooze_until)
        
        if self.alert_system:
            self.alert_system.clear_alert()
        
        logger.info(f"Snoozed for {minutes} minutes")

    def _handle_cancel_snooze(self) -> None:
        """Cancel snooze."""
        self._is_snoozed = False
        self._snooze_until = None
        self._dashboard.update_snooze_state(None)
        logger.info("Snooze cancelled")

    def _handle_call_contact(self, phone: str) -> None:
        """Initiate FaceTime call."""
        call_facetime(phone)
        self._tray.showMessage("Bear Alarm", f"Calling {phone}...", QSystemTrayIcon.MessageIcon.Information, 3000)

    def _handle_save_settings(self, new_config: dict) -> None:
        """Save settings."""
        try:
            # Merge with existing config
            current = self.config.model_dump() if self.config else {}
            
            for section, values in new_config.items():
                if section not in current:
                    current[section] = {}
                if isinstance(values, dict):
                    current[section].update(values)
                else:
                    current[section] = values
            
            # Save and reload
            self.config = Config(**current)
            save_config(self.config)
            
            # Reinitialize components
            self._init_dexcom()
            self._init_alerts()
            
            # Update views
            self._settings.update_config(self.config)
            self._dashboard.update_contacts(self.config.alerts.emergency_contacts)
            
            # Start monitoring if configured (but don't switch tabs)
            if self.config.is_configured and not self._monitor_thread:
                self._start_monitoring()
            
            logger.info("Settings saved")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def _handle_test_sound(self, sound_path: str) -> None:
        """Test alert sound."""
        try:
            resolved = resolve_sound_path(sound_path)
            if self.alert_system:
                self.alert_system.play_sound(resolved)
        except Exception as e:
            logger.error(f"Failed to play sound: {e}")

    def _manual_refresh(self) -> None:
        """Manually refresh glucose."""
        threading.Thread(target=self._fetch_glucose, daemon=True).start()

    def _show_window(self) -> None:
        """Show and raise window."""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self._show_window()

    def _confirm_quit(self) -> None:
        """Confirm before quitting."""
        reply = QMessageBox.question(
            self,
            "Quit Bear Alarm?",
            "Glucose monitoring will stop. Are you sure?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._quit()

    def _quit(self) -> None:
        """Clean shutdown."""
        self._stop_monitoring.set()
        allow_sleep()
        
        if self.alert_system:
            self.alert_system.shutdown()
        
        if self.db:
            self.db.close()
        
        self._tray.hide()
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close - minimize to tray instead."""
        event.ignore()
        self.hide()
        self._tray.showMessage(
            "Bear Alarm",
            "Running in background. Click tray to restore.",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )


def run() -> None:
    """Run the application."""
    import sys
    
    app = QApplication(sys.argv)
    app.setApplicationName("Bear Alarm")
    app.setApplicationDisplayName("Bear Alarm")
    
    # Apply theme
    apply_theme(app)
    app.setStyleSheet(STYLESHEET)
    
    # Create and show window
    window = BearAlarmApp()
    window.show()
    
    sys.exit(app.exec())

