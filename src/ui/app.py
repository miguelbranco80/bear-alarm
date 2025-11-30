"""Main application controller for Bear Alarm UI."""

import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import flet as ft

from ..core import Config, load_config, save_config, DexcomClient, DexcomClientError, AlertSystem, prevent_sleep, allow_sleep, check_volume_status
from ..data import Database
from ..data.models import TrendDirection
from .theme import COLORS, SIZES, SPACING
from .views import DashboardView, HistoryView, SettingsView

logger = logging.getLogger(__name__)


class BearAlarmApp:
    """Main application controller."""

    def __init__(self):
        self.page: Optional[ft.Page] = None
        self.config: Optional[Config] = None
        self.db: Optional[Database] = None
        self.dexcom_client: Optional[DexcomClient] = None
        self.alert_system: Optional[AlertSystem] = None
        
        # Views
        self._dashboard: Optional[DashboardView] = None
        self._history: Optional[HistoryView] = None
        self._settings: Optional[SettingsView] = None
        self._tabs: Optional[ft.Tabs] = None
        self._volume_warning: Optional[ft.Container] = None
        
        # Monitoring state
        self._monitor_thread: Optional[threading.Thread] = None
        self._volume_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._is_snoozed = False
        self._snooze_until: Optional[datetime] = None
        
        # Current glucose state
        self._current_glucose: Optional[float] = None
        self._current_trend: str = "→"
        

    def run(self) -> None:
        """Start the application."""
        ft.app(target=self._init_app, name="Bear Alarm")

    def _init_app(self, page: ft.Page) -> None:
        """Initialize the Flet application."""
        self.page = page
        
        # Hide window while initializing to prevent glitchy resize
        page.window.visible = False
        
        # Window configuration
        page.title = "Bear Alarm"
        page.window.width = 420
        page.window.height = 700
        page.window.min_width = 380
        page.window.min_height = 600
        
        # Minimize to dock instead of closing (keeps monitoring running)
        page.window.prevent_close = True
        page.window.on_event = self._handle_window_event
        
        page.bgcolor = COLORS["background"]
        page.padding = 0
        
        # Handle Cmd+Q to quit
        def on_keyboard(e: ft.KeyboardEvent):
            if e.key == "Q" and e.meta:  # Cmd+Q on macOS
                self._confirm_quit(None)
        page.on_keyboard_event = on_keyboard
        
        # Theme
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=COLORS["primary"],
                secondary=COLORS["secondary"],
                background=COLORS["background"],
                surface=COLORS["surface"],
            ),
        )
        
        # Initialize components
        self._init_database()
        self._init_config()
        self._init_dexcom()
        self._init_alerts()
        self._init_views()
        
        # Build UI
        self._build_ui()
        
        # Show window now that UI is ready
        page.window.visible = True
        page.update()
        
        # Start monitoring
        self._start_monitoring()

    def _init_database(self) -> None:
        """Initialize SQLite database."""
        self.db = Database()
        logger.info(f"Database initialized at {self.db.db_path}")

    def _init_config(self) -> None:
        """Load configuration."""
        self.config = load_config()
        logger.info("Configuration loaded")
        
        if not self.config.is_configured:
            logger.warning("Dexcom credentials not configured")
            # Will show setup dialog after UI is built

    def _init_dexcom(self) -> None:
        """Initialize Dexcom client."""
        if self.config:
            try:
                self.dexcom_client = DexcomClient(
                    username=self.config.dexcom.username,
                    password=self.config.dexcom.password,
                    ous=self.config.dexcom.ous,
                )
                logger.info("Dexcom client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Dexcom client: {e}")

    def _init_alerts(self) -> None:
        """Initialize alert system."""
        if self.config:
            self.alert_system = AlertSystem(
                low_alert_sound=self.config.alerts.low_alert_sound,
                high_alert_sound=self.config.alerts.high_alert_sound,
                alert_interval=self.config.alerts.alert_interval,
            )
            logger.info("Alert system initialized")

    def _handle_window_event(self, e) -> None:
        """Handle window events (close -> minimize to dock)."""
        if e.data == "close":
            # Minimize to dock instead of quitting
            self.page.window.minimized = True
            self.page.update()

    def _init_views(self) -> None:
        """Initialize UI views."""
        self._dashboard = DashboardView(
            on_snooze=self._handle_snooze,
            on_cancel_snooze=self._handle_cancel_snooze,
        )
        
        self._history = HistoryView(
            get_readings=lambda hours: self.db.get_readings_for_chart(hours) if self.db else [],
            get_stats=lambda hours: self.db.get_stats(hours) if self.db else {},
        )
        
        self._settings = SettingsView(
            config=self.config,
            on_save=self._handle_save_settings,
            on_test_sound=self._handle_test_sound,
            page=self.page,
        )

    def _build_ui(self) -> None:
        """Build the main UI."""
        
        # Navigation tabs
        def on_tab_change(e):
            index = e.control.selected_index
            if index == 1:
                # Refresh history when switching to that tab
                self._history.refresh_data()
                self.page.update()
        
        self._tabs = ft.Tabs(
            selected_index=0,
            animation_duration=200,
            on_change=on_tab_change,
            tabs=[
                ft.Tab(
                    text="Dashboard",
                    icon=ft.Icons.DASHBOARD,
                    content=self._dashboard.build(),
                ),
                ft.Tab(
                    text="History",
                    icon=ft.Icons.SHOW_CHART,
                    content=self._history.build(),
                ),
                ft.Tab(
                    text="Settings",
                    icon=ft.Icons.SETTINGS,
                    content=self._settings.build(),
                ),
            ],
            label_color=COLORS["primary"],
            unselected_label_color=COLORS["text_muted"],
            indicator_color=COLORS["primary"],
            indicator_border_radius=4,
            divider_color=COLORS["surface_variant"],
            expand=True,
        )
        
        # App bar
        app_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Image(
                                src="bear-icon.png",
                                width=32,
                                height=32,
                                fit=ft.ImageFit.CONTAIN,
                                error_content=ft.Icon(
                                    ft.Icons.MONITOR_HEART,
                                    color=COLORS["primary"],
                                    size=28,
                                ),
                            ),
                            ft.Text(
                                "Bear Alarm",
                                size=SIZES["heading"],
                                weight=ft.FontWeight.W_700,
                                color=COLORS["text_primary"],
                            ),
                        ],
                        spacing=SPACING["sm"],
                    ),
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                icon_color=COLORS["secondary"],
                                on_click=self._handle_refresh,
                                tooltip="Refresh now",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=COLORS["error"],
                                on_click=self._confirm_quit,
                                tooltip="Quit (Cmd+Q)",
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=SPACING["lg"], vertical=SPACING["sm"]),
            bgcolor=COLORS["surface"],
        )
        
        # Volume warning banner (hidden by default)
        self._volume_warning_text = ft.Text(
            "",
            size=SIZES["body"],
            weight=ft.FontWeight.W_600,
            color="#000000",
        )
        self._volume_warning = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.VOLUME_OFF, color="#000000", size=20),
                    self._volume_warning_text,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=SPACING["sm"],
            ),
            bgcolor="#fbbf24",  # Warning yellow
            padding=ft.padding.symmetric(horizontal=SPACING["lg"], vertical=SPACING["sm"]),
            visible=False,
        )
        
        # Add file pickers to page overlays (required for Flet file dialogs)
        for picker in self._settings.get_file_pickers():
            self.page.overlay.append(picker)
        
        self.page.add(
            ft.Column(
                [
                    self._volume_warning,
                    app_bar,
                    self._tabs,
                ],
                spacing=0,
                expand=True,
            )
        )
        
        # Start volume monitoring thread
        self._start_volume_monitoring()
    
    def _switch_to_tab(self, index: int) -> None:
        """Switch to a specific tab."""
        if self._tabs:
            self._tabs.selected_index = index
    
    def _start_volume_monitoring(self) -> None:
        """Start background volume monitoring (every 30 seconds)."""
        self._volume_thread = threading.Thread(target=self._volume_loop, daemon=True)
        self._volume_thread.start()
    
    def _volume_loop(self) -> None:
        """Background loop to check volume every 2 seconds."""
        while not self._stop_monitoring.is_set():
            self._update_ui(self._check_volume)
            self._stop_monitoring.wait(timeout=2)  # Check every 2 seconds
    
    def _check_volume(self) -> None:
        """Check system volume and update warning banner."""
        min_vol = self.config.alerts.min_volume if self.config else 50
        is_ok, message = check_volume_status(min_vol)
        
        if not is_ok:
            self._volume_warning_text.value = message
            self._volume_warning.visible = True
        else:
            self._volume_warning.visible = False

    def _start_monitoring(self) -> None:
        """Start background glucose monitoring."""
        if not self.config or not self.config.is_configured:
            self._dashboard.update_connection_status("Configure Dexcom credentials in Settings", is_error=True)
            self._show_setup_dialog()
            return
        
        if not self.dexcom_client:
            self._dashboard.update_connection_status("No Dexcom account configured", is_error=True)
            return
        
        # Prevent system sleep while monitoring
        prevent_sleep()
        
        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Monitoring started")

    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        poll_interval = self.config.monitoring.poll_interval if self.config else 300
        
        # Initial delay if configured
        if self.config and self.config.monitoring.startup_delay > 0:
            delay = self.config.monitoring.startup_delay
            self._update_ui(lambda: self._dashboard.update_connection_status(
                f"Starting in {delay // 60} minutes..."
            ))
            
            # Wait with ability to cancel
            start = time.time()
            while time.time() - start < delay:
                if self._stop_monitoring.is_set():
                    return
                time.sleep(1)
        
        while not self._stop_monitoring.is_set():
            try:
                self._poll_glucose()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                self._update_ui(lambda: self._dashboard.update_connection_status(
                    "Connection error", is_error=True
                ))
            
            # Wait for next poll
            self._stop_monitoring.wait(timeout=poll_interval)

    def _poll_glucose(self) -> None:
        """Poll glucose from Dexcom and update UI."""
        if not self.dexcom_client:
            return
        
        try:
            glucose_mmol = self.dexcom_client.get_glucose_mmol()
            
            if glucose_mmol is None:
                self._update_ui(lambda: self._dashboard.update_connection_status(
                    "No reading available"
                ))
                return
            
            # Get trend from pydexcom
            try:
                reading = self.dexcom_client.get_current_glucose_reading()
                if reading:
                    trend = TrendDirection(reading.trend_description)
                    trend_arrow = trend.arrow
                    glucose_mgdl = reading.mg_dl
                else:
                    trend_arrow = "→"
                    glucose_mgdl = int(glucose_mmol * 18)
            except Exception:
                trend_arrow = "→"
                glucose_mgdl = int(glucose_mmol * 18)
                reading = None
            
            self._current_glucose = glucose_mmol
            self._current_trend = trend_arrow
            
            # Store in database
            if self.db:
                self.db.add_reading(
                    glucose_mmol=glucose_mmol,
                    glucose_mgdl=glucose_mgdl,
                    trend=TrendDirection(reading.trend_description) if reading else None,
                )
            
            # Update UI
            now = datetime.now()
            self._update_ui(lambda: self._dashboard.update_glucose(
                glucose_mmol, trend_arrow, now
            ))
            
            # Check thresholds and alert
            self._check_thresholds(glucose_mmol)
            
            logger.info(f"Glucose: {glucose_mmol:.1f} mmol/L {trend_arrow}")
            
        except DexcomClientError as e:
            logger.error(f"Dexcom error: {e}")
            self._update_ui(lambda: self._dashboard.update_connection_status(
                "Dexcom error", is_error=True
            ))

    def _check_thresholds(self, glucose_mmol: float) -> None:
        """Check glucose against thresholds and trigger alerts."""
        if not self.config or not self.alert_system:
            return
        
        # Check if snoozed
        if self._is_snoozed and self._snooze_until:
            if datetime.now() >= self._snooze_until:
                self._is_snoozed = False
                self._snooze_until = None
                self._update_ui(lambda: self._dashboard.update_snooze_state(None))
            else:
                return  # Still snoozed, don't alert
        
        low = self.config.alerts.low_threshold
        high = self.config.alerts.high_threshold
        
        if glucose_mmol <= low:
            logger.warning(f"LOW GLUCOSE: {glucose_mmol:.1f}")
            self.alert_system.trigger_low_alert()
        elif glucose_mmol >= high:
            logger.warning(f"HIGH GLUCOSE: {glucose_mmol:.1f}")
            self.alert_system.trigger_high_alert()
        else:
            self.alert_system.clear_alert()

    def _update_ui(self, callback) -> None:
        """Safely update UI from background thread."""
        if self.page:
            try:
                callback()
                self.page.update()
            except Exception as e:
                logger.error(f"UI update error: {e}")

    def _handle_snooze(self, minutes: int) -> None:
        """Handle snooze request."""
        self._is_snoozed = True
        self._snooze_until = datetime.now() + timedelta(minutes=minutes)
        
        # Stop current alert
        if self.alert_system:
            self.alert_system.clear_alert()
        
        # Record in database
        if self.db:
            self.db.add_snooze(minutes)
        
        # Update UI
        self._dashboard.update_snooze_state(self._snooze_until)
        self.page.update()
        
        logger.info(f"Snoozed for {minutes} minutes until {self._snooze_until}")

    def _handle_cancel_snooze(self) -> None:
        """Handle cancel snooze request."""
        self._is_snoozed = False
        self._snooze_until = None
        
        if self.db:
            self.db.cancel_snooze()
        
        self._dashboard.update_snooze_state(None)
        self.page.update()
        
        # Re-check thresholds
        if self._current_glucose:
            self._check_thresholds(self._current_glucose)
        
        logger.info("Snooze cancelled")

    def _handle_refresh(self, _) -> None:
        """Handle manual refresh request."""
        threading.Thread(target=self._poll_glucose, daemon=True).start()

    def _confirm_quit(self, _) -> None:
        """Show quit confirmation dialog."""
        def do_quit(_):
            dialog.open = False
            self.page.update()
            self._handle_quit(None)
        
        def cancel(_):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Quit Bear Alarm?"),
            content=ft.Text("Glucose monitoring will stop."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.TextButton(
                    "Quit",
                    on_click=do_quit,
                    style=ft.ButtonStyle(color=COLORS["error"]),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _handle_quit(self, _) -> None:
        """Handle quit request."""
        self._stop_monitoring.set()
        allow_sleep()
        if self.page:
            self.page.window.prevent_close = False
            self.page.window.close()

    def _handle_save_settings(self, new_config: dict) -> None:
        """Handle settings save."""
        try:
            # Create config object from dict (Pydantic handles nested dicts)
            from ..core import Config
            
            config = Config(**new_config)
            
            # Save to user config file
            save_config(config)
            
            # Reload config
            self.config = load_config()
            
            # Reinitialize Dexcom client if credentials changed
            was_configured = self.dexcom_client is not None
            self._init_dexcom()
            self._init_alerts()
            
            # Start monitoring if newly configured
            if not was_configured and self.config.is_configured and self.dexcom_client:
                self._start_monitoring()
            
            # Update dashboard status
            if self.config.is_configured:
                self._dashboard.update_connection_status("Connecting...")
            
            # Switch to Dashboard tab
            self._switch_to_tab(0)
            
            # Show confirmation
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Settings saved!", color=COLORS["text_primary"]),
                bgcolor=COLORS["success"],
            )
            self.page.snack_bar.open = True
            self.page.update()
            
            logger.info("Settings saved")
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {e}", color=COLORS["text_primary"]),
                bgcolor=COLORS["error"],
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _handle_test_sound(self, sound_path: str) -> None:
        """Handle test sound request."""
        from ..core import resolve_sound_path
        
        if self.alert_system:
            resolved_path = resolve_sound_path(sound_path)
            logger.debug(f"Testing sound: {resolved_path}")
            self.alert_system._play_sound(resolved_path)

    def _show_setup_dialog(self) -> None:
        """Show initial setup dialog."""
        def go_to_settings(_):
            dialog.open = False
            self._switch_to_tab(2)  # Settings tab
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Welcome to Bear Alarm! 🐻"),
            content=ft.Column(
                [
                    ft.Text(
                        "To get started, you need to configure your Dexcom Share credentials.",
                        size=14,
                    ),
                    ft.Container(height=8),
                    ft.Text(
                        "Go to Settings to enter your username and password.",
                        size=14,
                        color=COLORS["text_muted"],
                    ),
                ],
                tight=True,
            ),
            actions=[
                ft.TextButton("Go to Settings", on_click=go_to_settings),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def stop(self) -> None:
        """Stop the application."""
        self._stop_monitoring.set()
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        
        if self.alert_system:
            self.alert_system.shutdown()
        
        if self.db:
            self.db.close()
        
        # Allow system to sleep again
        allow_sleep()
        
        logger.info("Application stopped")

