"""Dashboard view - main glucose display with snooze functionality."""

from datetime import datetime
from typing import Callable, Optional

import flet as ft

from ..theme import COLORS, SIZES, SPACING, card, get_glucose_color


class DashboardView:
    """Main dashboard showing current glucose and snooze controls."""

    def __init__(
        self,
        on_snooze: Callable[[int], None],
        on_cancel_snooze: Callable[[], None],
    ):
        self.on_snooze = on_snooze
        self.on_cancel_snooze = on_cancel_snooze
        
        # State
        self._glucose_value: Optional[float] = None
        self._trend_arrow: str = "→"
        self._last_update: Optional[datetime] = None
        self._snooze_until: Optional[datetime] = None
        self._is_alerting: bool = False
        self._connection_status: str = "Connecting..."
        
        # UI elements (will be created in build)
        self._glucose_text: Optional[ft.Text] = None
        self._trend_text: Optional[ft.Text] = None
        self._status_text: Optional[ft.Text] = None
        self._snooze_container: Optional[ft.Container] = None
        self._snooze_info: Optional[ft.Container] = None
        self._snooze_until_text: Optional[ft.Text] = None
        self._control: Optional[ft.Control] = None

    def build(self) -> ft.Control:
        """Build the dashboard UI."""
        
        # Glucose display
        self._glucose_text = ft.Text(
            "--.-",
            size=SIZES["glucose_display"],
            weight=ft.FontWeight.W_700,
            color=COLORS["text_secondary"],
        )
        
        self._trend_text = ft.Text(
            "",
            size=48,
            color=COLORS["text_secondary"],
        )
        
        glucose_display = ft.Row(
            [
                self._glucose_text,
                ft.Column(
                    [
                        self._trend_text,
                        ft.Text(
                            "mmol/L",
                            size=SIZES["glucose_unit"],
                            color=COLORS["text_muted"],
                        ),
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.END,
            spacing=SPACING["sm"],
        )
        
        # Status text
        self._status_text = ft.Text(
            self._connection_status,
            size=SIZES["caption"],
            color=COLORS["text_muted"],
            text_align=ft.TextAlign.CENTER,
        )
        
        # Snooze buttons
        snooze_buttons = ft.Row(
            [
                self._create_snooze_button("15m", 15),
                self._create_snooze_button("30m", 30),
                self._create_snooze_button("1h", 60),
                self._create_snooze_button("2h", 120),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=SPACING["sm"],
        )
        
        self._snooze_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "SNOOZE ALERTS",
                        size=SIZES["caption"],
                        weight=ft.FontWeight.W_600,
                        color=COLORS["text_muted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    snooze_buttons,
                ],
                spacing=SPACING["sm"],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            visible=True,
        )
        
        # Active snooze info (hidden by default)
        self._snooze_until_text = ft.Text(
            "Until --:--",
            size=SIZES["caption"],
            color=COLORS["text_muted"],
            text_align=ft.TextAlign.CENTER,
        )
        
        self._snooze_info = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.NOTIFICATIONS_PAUSED, color=COLORS["warning"], size=24),
                            ft.Text(
                                "Alerts Snoozed",
                                size=SIZES["body"],
                                weight=ft.FontWeight.W_600,
                                color=COLORS["warning"],
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=SPACING["xs"],
                    ),
                    self._snooze_until_text,
                    ft.ElevatedButton(
                        "Cancel Snooze",
                        on_click=self._handle_cancel_snooze,
                        style=ft.ButtonStyle(
                            color=COLORS["text_primary"],
                            bgcolor=COLORS["surface_variant"],
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                        height=36,
                    ),
                ],
                spacing=SPACING["xs"],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            visible=False,
            padding=SPACING["md"],
            bgcolor=ft.Colors.with_opacity(0.2, COLORS["warning"]),
            border_radius=12,
        )
        
        # Stats row
        stats_row = ft.Row(
            [
                self._create_stat_card("24h Range", "--", "mmol/L"),
                self._create_stat_card("Time in Range", "--%", "3.9-10.0"),
                self._create_stat_card("Readings", "--", "today"),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )
        
        # Main layout
        self._control = ft.Container(
            content=ft.Column(
                [
                    card(
                        ft.Column(
                            [
                                glucose_display,
                                self._status_text,
                            ],
                            spacing=SPACING["sm"],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=SPACING["xl"],
                    ),
                    self._snooze_info,
                    self._snooze_container,
                    ft.Container(height=SPACING["md"]),
                    stats_row,
                ],
                spacing=SPACING["md"],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=SPACING["lg"],
        )
        
        return self._control

    def _create_snooze_button(self, label: str, minutes: int) -> ft.ElevatedButton:
        """Create a snooze duration button."""
        return ft.ElevatedButton(
            label,
            on_click=lambda _: self._handle_snooze(minutes),
            style=ft.ButtonStyle(
                color=COLORS["text_primary"],
                bgcolor=COLORS["surface_variant"],
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            width=70,
            height=40,
        )

    def _create_stat_card(self, title: str, value: str, subtitle: str) -> ft.Container:
        """Create a statistics card."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        title,
                        size=SIZES["caption"],
                        color=COLORS["text_muted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        value,
                        size=SIZES["subheading"],
                        weight=ft.FontWeight.W_600,
                        color=COLORS["text_primary"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        subtitle,
                        size=SIZES["caption"],
                        color=COLORS["text_muted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=SPACING["sm"],
            bgcolor=COLORS["surface"],
            border_radius=12,
            width=110,
        )

    def _handle_snooze(self, minutes: int) -> None:
        """Handle snooze button click."""
        self.on_snooze(minutes)

    def _handle_cancel_snooze(self, _) -> None:
        """Handle cancel snooze click."""
        self.on_cancel_snooze()

    def update_glucose(
        self,
        glucose_mmol: Optional[float],
        trend_arrow: str = "→",
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Update the glucose display."""
        self._glucose_value = glucose_mmol
        self._trend_arrow = trend_arrow
        self._last_update = timestamp or datetime.now()
        
        if glucose_mmol is not None:
            color = get_glucose_color(glucose_mmol)
            self._glucose_text.value = f"{glucose_mmol:.1f}"
            self._glucose_text.color = color
            self._trend_text.value = trend_arrow
            self._trend_text.color = color
            
            time_str = self._last_update.strftime("%H:%M")
            self._status_text.value = f"Last reading: {time_str}"
            self._status_text.color = COLORS["text_muted"]
        else:
            self._glucose_text.value = "--.-"
            self._glucose_text.color = COLORS["text_secondary"]
            self._trend_text.value = ""

    def update_snooze_state(self, snooze_until: Optional[datetime]) -> None:
        """Update snooze display state."""
        self._snooze_until = snooze_until
        
        if snooze_until and snooze_until > datetime.now():
            # Show snooze info, hide buttons
            self._snooze_container.visible = False
            self._snooze_info.visible = True
            self._snooze_until_text.value = f"Until {snooze_until.strftime('%H:%M')}"
        else:
            # Show buttons, hide snooze info
            self._snooze_container.visible = True
            self._snooze_info.visible = False

    def update_connection_status(self, status: str, is_error: bool = False) -> None:
        """Update connection status text."""
        self._connection_status = status
        self._status_text.value = status
        self._status_text.color = COLORS["error"] if is_error else COLORS["text_muted"]

    def set_alerting(self, is_alerting: bool, alert_type: str = "") -> None:
        """Update alerting state for visual feedback."""
        self._is_alerting = is_alerting
