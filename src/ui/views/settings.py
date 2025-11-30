"""Settings view - configuration options."""

from pathlib import Path
from typing import Callable, Optional, TYPE_CHECKING

import flet as ft

from ..theme import COLORS, SIZES, SPACING, card, styled_button

if TYPE_CHECKING:
    from ...core import Config


class SettingsView:
    """Settings panel for all configuration options."""

    def __init__(
        self,
        config: "Config",
        on_save: Callable[[dict], None],
        on_test_sound: Callable[[str], None],
        page: Optional[ft.Page] = None,
    ):
        self.config = config
        self.on_save = on_save
        self.on_test_sound = on_test_sound
        self.page = page
        
        # Form fields
        self._fields: dict[str, ft.Control] = {}
        self._has_changes = False
        self._control: Optional[ft.Control] = None
        self._file_pickers: dict[str, ft.FilePicker] = {}

    def build(self) -> ft.Control:
        """Build the settings view."""
        
        # Dexcom credentials section
        dexcom_section = self._create_section(
            "Dexcom Account",
            [
                self._create_text_field(
                    "dexcom.username",
                    "Username",
                    self.config.dexcom.username,
                    hint="Your Dexcom Share username",
                ),
                self._create_text_field(
                    "dexcom.password",
                    "Password",
                    self.config.dexcom.password,
                    password=True,
                    hint="Your Dexcom Share password",
                ),
                self._create_switch(
                    "dexcom.ous",
                    "Outside US",
                    self.config.dexcom.ous,
                    subtitle="Enable if you're outside the United States",
                ),
            ],
        )
        
        # Alert thresholds section
        alerts_section = self._create_section(
            "Alert Thresholds",
            [
                self._create_slider(
                    "alerts.low_threshold",
                    "Low Glucose Threshold",
                    self.config.alerts.low_threshold,
                    min_val=2.0,
                    max_val=5.0,
                    divisions=30,
                    unit="mmol/L",
                    color=COLORS["glucose_low"],
                ),
                self._create_slider(
                    "alerts.high_threshold",
                    "High Glucose Threshold",
                    self.config.alerts.high_threshold,
                    min_val=8.0,
                    max_val=20.0,
                    divisions=24,
                    unit="mmol/L",
                    color=COLORS["glucose_high"],
                ),
            ],
        )
        
        # Alert sounds section
        sounds_section = self._create_section(
            "Alert Sounds",
            [
                self._create_file_picker(
                    "alerts.low_alert_sound",
                    "Low Alert Sound",
                    self.config.alerts.low_alert_sound,
                ),
                self._create_file_picker(
                    "alerts.high_alert_sound",
                    "High Alert Sound",
                    self.config.alerts.high_alert_sound,
                ),
                self._create_slider(
                    "alerts.alert_interval",
                    "Alert Repeat Interval",
                    self.config.alerts.alert_interval // 60,
                    min_val=1,
                    max_val=30,
                    divisions=29,
                    unit="minutes",
                    color=COLORS["secondary"],
                    is_integer=True,
                ),
            ],
        )
        
        # Monitoring section
        monitoring_section = self._create_section(
            "Monitoring",
            [
                self._create_slider(
                    "monitoring.poll_interval",
                    "Check Interval",
                    self.config.monitoring.poll_interval // 60,
                    min_val=1,
                    max_val=15,
                    divisions=14,
                    unit="minutes",
                    color=COLORS["secondary"],
                    is_integer=True,
                ),
                self._create_slider(
                    "monitoring.startup_delay_minutes",
                    "Startup Delay",
                    self.config.monitoring.startup_delay_minutes,
                    min_val=0,
                    max_val=60,
                    divisions=12,
                    unit="minutes",
                    color=COLORS["text_muted"],
                    is_integer=True,
                ),
                self._create_slider(
                    "alerts.min_volume",
                    "Minimum Volume Warning",
                    self.config.alerts.min_volume,
                    min_val=10,
                    max_val=100,
                    divisions=9,
                    unit="%",
                    color=COLORS["warning"],
                    is_integer=True,
                ),
            ],
        )
        
        # Save button
        save_button = ft.Container(
            content=styled_button(
                "Save Settings",
                self._handle_save,
                icon=ft.Icons.SAVE,
                width=200,
            ),
            alignment=ft.alignment.center,
            padding=SPACING["lg"],
        )
        
        self._control = ft.Container(
            content=ft.Column(
                [
                    dexcom_section,
                    alerts_section,
                    sounds_section,
                    monitoring_section,
                    save_button,
                    ft.Container(height=SPACING["xl"]),
                ],
                spacing=SPACING["lg"],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=SPACING["lg"],
        )
        
        return self._control

    def _create_section(self, title: str, controls: list[ft.Control]) -> ft.Container:
        """Create a settings section."""
        return card(
            ft.Column(
                [
                    ft.Text(
                        title,
                        size=SIZES["subheading"],
                        weight=ft.FontWeight.W_600,
                        color=COLORS["text_primary"],
                    ),
                    ft.Divider(color=COLORS["surface_variant"], height=1),
                    *controls,
                ],
                spacing=SPACING["md"],
            ),
            padding=SPACING["lg"],
        )

    def _create_text_field(
        self,
        key: str,
        label: str,
        value: str,
        password: bool = False,
        hint: str = "",
    ) -> ft.Control:
        """Create a text input field."""
        field = ft.TextField(
            label=label,
            value=value,
            password=password,
            can_reveal_password=password,
            hint_text=hint,
            border_color=COLORS["surface_variant"],
            focused_border_color=COLORS["primary"],
            label_style=ft.TextStyle(color=COLORS["text_muted"]),
            text_style=ft.TextStyle(color=COLORS["text_primary"]),
            on_change=lambda _: self._mark_changed(),
        )
        self._fields[key] = field
        return field

    def _create_switch(
        self,
        key: str,
        label: str,
        value: bool,
        subtitle: str = "",
    ) -> ft.Control:
        """Create a switch toggle."""
        switch = ft.Switch(
            value=value,
            active_color=COLORS["primary"],
            on_change=lambda _: self._mark_changed(),
        )
        self._fields[key] = switch
        
        controls = [
            ft.Text(
                label,
                size=SIZES["body"],
                color=COLORS["text_primary"],
            ),
        ]
        if subtitle:
            controls.append(
                ft.Text(
                    subtitle,
                    size=SIZES["caption"],
                    color=COLORS["text_muted"],
                )
            )
        
        return ft.Row(
            [
                ft.Column(controls, spacing=2, expand=True),
                switch,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _create_slider(
        self,
        key: str,
        label: str,
        value: float,
        min_val: float,
        max_val: float,
        divisions: int,
        unit: str,
        color: str,
        is_integer: bool = False,
    ) -> ft.Control:
        """Create a slider with label."""
        display_value = int(value) if is_integer else value
        value_text = ft.Text(
            f"{display_value} {unit}" if is_integer else f"{value:.1f} {unit}",
            size=SIZES["body"],
            weight=ft.FontWeight.W_600,
            color=color,
        )
        
        def on_change(e):
            val = e.control.value
            if is_integer:
                value_text.value = f"{int(val)} {unit}"
            else:
                value_text.value = f"{val:.1f} {unit}"
            value_text.update()
            self._mark_changed()
        
        slider = ft.Slider(
            value=float(value),
            min=min_val,
            max=max_val,
            divisions=divisions,
            active_color=color,
            inactive_color=ft.Colors.with_opacity(0.3, color),
            on_change=on_change,
        )
        self._fields[key] = slider
        
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(
                            label,
                            size=SIZES["body"],
                            color=COLORS["text_primary"],
                        ),
                        value_text,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                slider,
            ],
            spacing=SPACING["xs"],
        )

    def _create_file_picker(
        self,
        key: str,
        label: str,
        value: str,
    ) -> ft.Control:
        """Create a file picker for sound files."""
        path_text = ft.Text(
            Path(value).name if value else "No file selected",
            size=SIZES["caption"],
            color=COLORS["text_muted"],
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )
        
        self._fields[key] = {"path": value, "text": path_text}
        
        def on_file_picked(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                file_path = e.files[0].path
                self._fields[key]["path"] = file_path
                self._fields[key]["text"].value = Path(file_path).name
                self._mark_changed()
                if self.page:
                    self.page.update()
        
        # Create file picker for this field
        file_picker = ft.FilePicker(on_result=on_file_picked)
        self._file_pickers[key] = file_picker
        
        def browse_file(_):
            file_picker.pick_files(
                allowed_extensions=["mp3", "wav", "ogg", "m4a"],
                dialog_title=f"Select {label}",
            )
        
        def test_sound(_):
            current_path = self._fields[key]["path"]
            if current_path:
                self.on_test_sound(current_path)
        
        return ft.Column(
            [
                ft.Text(
                    label,
                    size=SIZES["body"],
                    color=COLORS["text_primary"],
                ),
                ft.Row(
                    [
                        ft.Container(
                            content=path_text,
                            bgcolor=COLORS["surface_variant"],
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            border_radius=8,
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.FOLDER_OPEN,
                            icon_color=COLORS["text_muted"],
                            on_click=browse_file,
                            tooltip="Browse for file",
                        ),
                        ft.IconButton(
                            icon=ft.Icons.PLAY_ARROW,
                            icon_color=COLORS["secondary"],
                            on_click=test_sound,
                            tooltip="Test sound",
                        ),
                    ],
                    spacing=SPACING["xs"],
                ),
            ],
            spacing=SPACING["xs"],
        )

    def _mark_changed(self) -> None:
        """Mark that settings have been changed."""
        self._has_changes = True

    def _handle_save(self, _) -> None:
        """Handle save button click."""
        new_config = {
            "dexcom": {
                "username": self._fields["dexcom.username"].value,
                "password": self._fields["dexcom.password"].value,
                "ous": self._fields["dexcom.ous"].value,
            },
            "alerts": {
                "low_threshold": round(self._fields["alerts.low_threshold"].value, 1),
                "high_threshold": round(self._fields["alerts.high_threshold"].value, 1),
                "low_alert_sound": self._fields["alerts.low_alert_sound"]["path"],
                "high_alert_sound": self._fields["alerts.high_alert_sound"]["path"],
                "alert_interval": int(self._fields["alerts.alert_interval"].value) * 60,
                "min_volume": int(self._fields["alerts.min_volume"].value),
            },
            "monitoring": {
                "poll_interval": int(self._fields["monitoring.poll_interval"].value) * 60,
                "startup_delay_minutes": int(self._fields["monitoring.startup_delay_minutes"].value),
            },
        }
        
        self.on_save(new_config)
        self._has_changes = False

    def update_config(self, config: "Config") -> None:
        """Update settings with new config values."""
        self.config = config
    
    def get_file_pickers(self) -> list[ft.FilePicker]:
        """Get all file pickers to add to page overlays."""
        return list(self._file_pickers.values())
