"""Rules view - schedules and alert rule management."""

from typing import Callable, Optional, TYPE_CHECKING

import flet as ft

from ..theme import COLORS, SIZES, SPACING, card, styled_button

if TYPE_CHECKING:
    from ...core import Config, ScheduleConfig

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class RulesView:
    """Rules panel for schedule and threshold management."""

    def __init__(
        self,
        config: "Config",
        on_save: Callable[["Config"], None],
        page: Optional[ft.Page] = None,
    ):
        self.config = config
        self.on_save = on_save
        self.page = page
        self._control: Optional[ft.Control] = None
        self._schedules_list: Optional[ft.Column] = None

    def build(self) -> ft.Control:
        """Build the rules view."""
        
        # Default thresholds section
        default_section = self._create_section(
            "Default Alert Rules",
            "Applied when no schedule is active",
            [
                self._create_threshold_row(
                    "Urgent Low (always immediate)",
                    self.config.alerts.urgent_low,
                    "urgent_low",
                    COLORS["error"],
                ),
                self._create_threshold_row(
                    "Low Threshold",
                    self.config.alerts.low_threshold,
                    "low_threshold",
                    COLORS["glucose_low"],
                ),
                self._create_persist_row(
                    "Low Persistence",
                    self.config.alerts.low_persist_minutes,
                    "low_persist",
                ),
                self._create_threshold_row(
                    "High Threshold",
                    self.config.alerts.high_threshold,
                    "high_threshold",
                    COLORS["glucose_high"],
                ),
                self._create_persist_row(
                    "High Persistence",
                    self.config.alerts.high_persist_minutes,
                    "high_persist",
                ),
            ],
        )
        
        # Schedules section
        self._schedules_list = ft.Column(
            [self._create_schedule_card(s, i) for i, s in enumerate(self.config.alerts.schedules)],
            spacing=SPACING["sm"],
        )
        
        schedules_section = card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(
                                        "Schedules",
                                        size=SIZES["subheading"],
                                        weight=ft.FontWeight.W_600,
                                        color=COLORS["text_primary"],
                                    ),
                                    ft.Text(
                                        "Override default rules during specific times",
                                        size=SIZES["caption"],
                                        color=COLORS["text_muted"],
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD_CIRCLE,
                                icon_color=COLORS["primary"],
                                on_click=self._add_schedule,
                                tooltip="Add schedule",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(color=COLORS["surface_variant"], height=1),
                    self._schedules_list if self.config.alerts.schedules else ft.Text(
                        "No schedules. Add one to customize alerts for specific times.",
                        size=SIZES["caption"],
                        color=COLORS["text_muted"],
                        italic=True,
                    ),
                ],
                spacing=SPACING["md"],
            ),
            padding=SPACING["lg"],
        )
        
        # Active schedule indicator
        active = self.config.alerts.get_active_schedule()
        active_indicator = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.SCHEDULE,
                        color=COLORS["primary"] if active else COLORS["text_muted"],
                        size=16,
                    ),
                    ft.Text(
                        f"Active: {active.name}" if active else "Using default rules",
                        size=SIZES["caption"],
                        color=COLORS["primary"] if active else COLORS["text_muted"],
                    ),
                ],
                spacing=SPACING["xs"],
            ),
            padding=ft.padding.symmetric(horizontal=SPACING["lg"], vertical=SPACING["sm"]),
            bgcolor=COLORS["surface"],
            border_radius=8,
        )
        
        self._control = ft.Container(
            content=ft.Column(
                [
                    active_indicator,
                    default_section,
                    schedules_section,
                    ft.Container(height=SPACING["xl"]),
                ],
                spacing=SPACING["lg"],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=SPACING["lg"],
        )
        
        return self._control

    def _create_section(self, title: str, subtitle: str, controls: list[ft.Control]) -> ft.Container:
        """Create a settings section."""
        return card(
            ft.Column(
                [
                    ft.Column(
                        [
                            ft.Text(
                                title,
                                size=SIZES["subheading"],
                                weight=ft.FontWeight.W_600,
                                color=COLORS["text_primary"],
                            ),
                            ft.Text(
                                subtitle,
                                size=SIZES["caption"],
                                color=COLORS["text_muted"],
                            ),
                        ],
                        spacing=2,
                    ),
                    ft.Divider(color=COLORS["surface_variant"], height=1),
                    *controls,
                ],
                spacing=SPACING["md"],
            ),
            padding=SPACING["lg"],
        )

    def _create_threshold_row(
        self, label: str, value: float, key: str, color: str
    ) -> ft.Control:
        """Create a threshold input row."""
        field = ft.TextField(
            value=str(value),
            width=80,
            text_align=ft.TextAlign.CENTER,
            border_color=COLORS["surface_variant"],
            focused_border_color=color,
            text_style=ft.TextStyle(color=COLORS["text_primary"]),
            on_change=lambda e: self._on_default_change(key, e.control.value),
        )
        
        return ft.Row(
            [
                ft.Text(label, size=SIZES["body"], color=COLORS["text_primary"], expand=True),
                field,
                ft.Text("mmol/L", size=SIZES["caption"], color=COLORS["text_muted"]),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _create_persist_row(self, label: str, value: int, key: str) -> ft.Control:
        """Create a persistence input row."""
        field = ft.TextField(
            value=str(value),
            width=80,
            text_align=ft.TextAlign.CENTER,
            border_color=COLORS["surface_variant"],
            focused_border_color=COLORS["secondary"],
            text_style=ft.TextStyle(color=COLORS["text_primary"]),
            on_change=lambda e: self._on_default_change(key, e.control.value),
        )
        
        return ft.Row(
            [
                ft.Text(label, size=SIZES["body"], color=COLORS["text_primary"], expand=True),
                field,
                ft.Text("minutes", size=SIZES["caption"], color=COLORS["text_muted"]),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def _create_schedule_card(self, schedule: "ScheduleConfig", index: int) -> ft.Container:
        """Create a card for a schedule."""
        # Day chips
        day_chips = ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        DAY_NAMES[i],
                        size=10,
                        color=COLORS["text_primary"] if i in schedule.days else COLORS["text_muted"],
                    ),
                    bgcolor=COLORS["primary"] if i in schedule.days else COLORS["surface_variant"],
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                )
                for i in range(7)
            ],
            spacing=2,
        )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Switch(
                                value=schedule.enabled,
                                active_color=COLORS["primary"],
                                on_change=lambda e, idx=index: self._toggle_schedule(idx, e.control.value),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        schedule.name,
                                        size=SIZES["body"],
                                        weight=ft.FontWeight.W_600,
                                        color=COLORS["text_primary"] if schedule.enabled else COLORS["text_muted"],
                                    ),
                                    ft.Text(
                                        f"{schedule.start_time} - {schedule.end_time}",
                                        size=SIZES["caption"],
                                        color=COLORS["text_muted"],
                                    ),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT,
                                icon_color=COLORS["text_muted"],
                                icon_size=18,
                                on_click=lambda _, idx=index: self._edit_schedule(idx),
                                tooltip="Edit",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=COLORS["error"],
                                icon_size=18,
                                on_click=lambda _, idx=index: self._delete_schedule(idx),
                                tooltip="Delete",
                            ),
                        ],
                    ),
                    day_chips,
                    # Show overrides
                    ft.Row(
                        [
                            self._override_chip("Low", schedule.low_threshold, COLORS["glucose_low"]),
                            self._override_chip("High", schedule.high_threshold, COLORS["glucose_high"]),
                            self._override_chip("Low persist", schedule.low_persist_minutes, COLORS["secondary"], "m"),
                            self._override_chip("High persist", schedule.high_persist_minutes, COLORS["secondary"], "m"),
                        ],
                        spacing=4,
                        wrap=True,
                    ),
                ],
                spacing=SPACING["sm"],
            ),
            bgcolor=COLORS["surface_variant"],
            padding=SPACING["md"],
            border_radius=8,
        )

    def _override_chip(self, label: str, value: Optional[float], color: str, suffix: str = "") -> ft.Control:
        """Create a small chip showing an override value."""
        if value is None:
            return ft.Container()
        return ft.Container(
            content=ft.Text(
                f"{label}: {value}{suffix}",
                size=10,
                color=color,
            ),
            bgcolor=ft.Colors.with_opacity(0.2, color),
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=4,
        )

    def _on_default_change(self, key: str, value: str) -> None:
        """Handle default threshold change."""
        try:
            if key == "urgent_low":
                self.config.alerts.urgent_low = float(value)
            elif key == "low_threshold":
                self.config.alerts.low_threshold = float(value)
            elif key == "high_threshold":
                self.config.alerts.high_threshold = float(value)
            elif key == "low_persist":
                self.config.alerts.low_persist_minutes = int(value)
            elif key == "high_persist":
                self.config.alerts.high_persist_minutes = int(value)
            self._save()
        except ValueError:
            pass  # Invalid input, ignore

    def _add_schedule(self, _) -> None:
        """Add a new schedule."""
        from ...core import ScheduleConfig
        
        new_schedule = ScheduleConfig(
            name=f"Schedule {len(self.config.alerts.schedules) + 1}",
            priority=len(self.config.alerts.schedules) + 1,
        )
        self.config.alerts.schedules.append(new_schedule)
        # Open editor for the new schedule
        self._edit_schedule(len(self.config.alerts.schedules) - 1, is_new=True)

    def _toggle_schedule(self, index: int, enabled: bool) -> None:
        """Toggle a schedule on/off."""
        self.config.alerts.schedules[index].enabled = enabled
        self._save()
        self._refresh_schedules()

    def _edit_schedule(self, index: int, is_new: bool = False) -> None:
        """Open schedule editor dialog."""
        schedule = self.config.alerts.schedules[index]
        
        name_field = ft.TextField(
            value=schedule.name,
            label="Schedule Name",
            hint_text="e.g., Work Hours, Sleep Time",
            autofocus=is_new,
            border_radius=8,
        )
        
        start_field = ft.TextField(
            value=schedule.start_time,
            label="Start",
            hint_text="09:00",
            width=100,
            text_align=ft.TextAlign.CENTER,
            border_radius=8,
        )
        end_field = ft.TextField(
            value=schedule.end_time,
            label="End", 
            hint_text="17:00",
            width=100,
            text_align=ft.TextAlign.CENTER,
            border_radius=8,
        )
        
        # Day toggle buttons (nicer than checkboxes)
        day_toggles = {}
        def create_day_toggle(day_idx: int) -> ft.Container:
            is_selected = day_idx in schedule.days
            
            def toggle_day(_):
                current = day_toggles[day_idx].data["selected"]
                day_toggles[day_idx].data["selected"] = not current
                day_toggles[day_idx].bgcolor = COLORS["primary"] if not current else COLORS["surface_variant"]
                day_toggles[day_idx].content.color = COLORS["text_primary"] if not current else COLORS["text_muted"]
                self.page.update()
            
            container = ft.Container(
                content=ft.Text(
                    DAY_NAMES[day_idx],
                    size=12,
                    weight=ft.FontWeight.W_600,
                    color=COLORS["text_primary"] if is_selected else COLORS["text_muted"],
                    text_align=ft.TextAlign.CENTER,
                ),
                width=42,
                height=36,
                bgcolor=COLORS["primary"] if is_selected else COLORS["surface_variant"],
                border_radius=8,
                alignment=ft.alignment.center,
                on_click=toggle_day,
                data={"selected": is_selected},
            )
            day_toggles[day_idx] = container
            return container
        
        days_row = ft.Row(
            [create_day_toggle(i) for i in range(7)],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        
        # Override fields with better layout
        low_thresh = ft.TextField(
            value=str(schedule.low_threshold) if schedule.low_threshold else "",
            hint_text="—",
            width=70,
            text_align=ft.TextAlign.CENTER,
            border_radius=8,
        )
        high_thresh = ft.TextField(
            value=str(schedule.high_threshold) if schedule.high_threshold else "",
            hint_text="—",
            width=70,
            text_align=ft.TextAlign.CENTER,
            border_radius=8,
        )
        low_persist = ft.TextField(
            value=str(schedule.low_persist_minutes) if schedule.low_persist_minutes is not None else "",
            hint_text="—",
            width=70,
            text_align=ft.TextAlign.CENTER,
            border_radius=8,
        )
        high_persist = ft.TextField(
            value=str(schedule.high_persist_minutes) if schedule.high_persist_minutes is not None else "",
            hint_text="—",
            width=70,
            text_align=ft.TextAlign.CENTER,
            border_radius=8,
        )
        
        def save_schedule(_):
            schedule.name = name_field.value or f"Schedule {index + 1}"
            schedule.start_time = start_field.value
            schedule.end_time = end_field.value
            schedule.days = [i for i, toggle in day_toggles.items() if toggle.data["selected"]]
            
            schedule.low_threshold = float(low_thresh.value) if low_thresh.value else None
            schedule.high_threshold = float(high_thresh.value) if high_thresh.value else None
            schedule.low_persist_minutes = int(low_persist.value) if low_persist.value else None
            schedule.high_persist_minutes = int(high_persist.value) if high_persist.value else None
            
            dialog.open = False
            self.page.update()
            self._save()
            self._refresh_schedules()
        
        def cancel(_):
            if is_new:
                del self.config.alerts.schedules[index]
            dialog.open = False
            self.page.update()
            self._refresh_schedules()
        
        # Build nice sections
        time_section = ft.Container(
            content=ft.Column([
                ft.Text("Time Range", size=12, weight=ft.FontWeight.W_600, color=COLORS["text_muted"]),
                ft.Row(
                    [start_field, ft.Text("→", size=16, color=COLORS["text_muted"]), end_field],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=SPACING["sm"],
                ),
            ], spacing=SPACING["xs"], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COLORS["surface_variant"],
            padding=SPACING["md"],
            border_radius=12,
        )
        
        days_section = ft.Container(
            content=ft.Column([
                ft.Text("Active Days", size=12, weight=ft.FontWeight.W_600, color=COLORS["text_muted"]),
                days_row,
            ], spacing=SPACING["xs"], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COLORS["surface_variant"],
            padding=SPACING["md"],
            border_radius=12,
        )
        
        override_section = ft.Container(
            content=ft.Column([
                ft.Text("Override Thresholds", size=12, weight=ft.FontWeight.W_600, color=COLORS["text_muted"]),
                ft.Text("Leave empty to use defaults", size=10, color=COLORS["text_muted"], italic=True),
                ft.Container(height=8),
                ft.Row([
                    ft.Column([
                        ft.Text("Low", size=11, color=COLORS["glucose_low"]),
                        low_thresh,
                        ft.Text("mmol/L", size=9, color=COLORS["text_muted"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    ft.Column([
                        ft.Text("High", size=11, color=COLORS["glucose_high"]),
                        high_thresh,
                        ft.Text("mmol/L", size=9, color=COLORS["text_muted"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    ft.Column([
                        ft.Text("Low wait", size=11, color=COLORS["text_muted"]),
                        low_persist,
                        ft.Text("min", size=9, color=COLORS["text_muted"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                    ft.Column([
                        ft.Text("High wait", size=11, color=COLORS["text_muted"]),
                        high_persist,
                        ft.Text("min", size=9, color=COLORS["text_muted"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=COLORS["surface_variant"],
            padding=SPACING["md"],
            border_radius=12,
        )
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "New Schedule" if is_new else "Edit Schedule",
                size=SIZES["heading"],
                weight=ft.FontWeight.W_700,
            ),
            content=ft.Container(
                content=ft.Column(
                    [
                        name_field,
                        ft.Container(height=4),
                        time_section,
                        days_section,
                        override_section,
                    ],
                    spacing=SPACING["sm"],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=340,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_schedule,
                    style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_primary"]),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _delete_schedule(self, index: int) -> None:
        """Delete a schedule."""
        del self.config.alerts.schedules[index]
        self._save()
        self._refresh_schedules()

    def _refresh_schedules(self) -> None:
        """Refresh the schedules list."""
        if self._schedules_list:
            self._schedules_list.controls = [
                self._create_schedule_card(s, i) 
                for i, s in enumerate(self.config.alerts.schedules)
            ]
            if self.page:
                self.page.update()

    def _save(self) -> None:
        """Save config changes."""
        self.on_save(self.config)

    def update_config(self, config: "Config") -> None:
        """Update with new config."""
        self.config = config

