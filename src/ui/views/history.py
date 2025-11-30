"""History view - glucose charts and historical data."""

from datetime import datetime
from typing import Callable, Optional

import flet as ft

from ..theme import COLORS, SIZES, SPACING, card


class HistoryView:
    """Historical glucose data with charts."""

    def __init__(
        self,
        get_readings: Callable[[int], list[tuple[datetime, float]]],
        get_stats: Callable[[int], dict],
    ):
        self.get_readings = get_readings
        self.get_stats = get_stats
        
        self._selected_range = 24  # hours
        self._chart_container: Optional[ft.Container] = None
        self._stats_container: Optional[ft.Container] = None
        self._control: Optional[ft.Control] = None

    def build(self) -> ft.Control:
        """Build the history view."""
        
        # Time range selector
        range_selector = ft.Row(
            [
                self._create_range_button("3h", 3),
                self._create_range_button("6h", 6),
                self._create_range_button("12h", 12),
                self._create_range_button("24h", 24, selected=True),
                self._create_range_button("3d", 72),
                self._create_range_button("7d", 168),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=SPACING["xs"],
        )
        
        # Chart container
        self._chart_container = ft.Container(
            content=self._create_chart([]),
            height=250,
            padding=ft.padding.only(top=SPACING["md"]),
        )
        
        chart_card = card(
            ft.Column(
                [
                    ft.Text(
                        "Glucose History",
                        size=SIZES["subheading"],
                        weight=ft.FontWeight.W_600,
                        color=COLORS["text_primary"],
                    ),
                    range_selector,
                    self._chart_container,
                ],
                spacing=SPACING["sm"],
            ),
            padding=SPACING["lg"],
        )
        
        # Statistics cards
        self._stats_container = ft.Container(
            content=self._create_stats_grid({}),
        )
        
        self._control = ft.Container(
            content=ft.Column(
                [
                    chart_card,
                    self._stats_container,
                ],
                spacing=SPACING["md"],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=SPACING["lg"],
        )
        
        return self._control

    def _create_range_button(
        self,
        label: str,
        hours: int,
        selected: bool = False,
    ) -> ft.Container:
        """Create a time range selection button."""
        return ft.Container(
            content=ft.Text(
                label,
                size=SIZES["caption"],
                weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
                color=COLORS["primary"] if selected else COLORS["text_muted"],
                text_align=ft.TextAlign.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            bgcolor=ft.Colors.with_opacity(0.1, COLORS["primary"]) if selected else None,
            border_radius=8,
            on_click=lambda _: self._select_range(hours),
            ink=True,
        )

    def _select_range(self, hours: int) -> None:
        """Handle range selection."""
        self._selected_range = hours
        self.refresh_data()

    def _create_chart(
        self,
        data_points: list[tuple[datetime, float]],
    ) -> ft.LineChart:
        """Create the glucose line chart."""
        
        if not data_points:
            # Empty chart with placeholder
            return ft.LineChart(
                data_series=[],
                min_y=2,
                max_y=20,
                min_x=0,
                max_x=100,
                horizontal_grid_lines=ft.ChartGridLines(
                    interval=2,
                    color=ft.Colors.with_opacity(0.1, COLORS["text_muted"]),
                ),
                left_axis=ft.ChartAxis(
                    labels=[
                        ft.ChartAxisLabel(value=4, label=ft.Text("4", size=10, color=COLORS["text_muted"])),
                        ft.ChartAxisLabel(value=8, label=ft.Text("8", size=10, color=COLORS["text_muted"])),
                        ft.ChartAxisLabel(value=12, label=ft.Text("12", size=10, color=COLORS["text_muted"])),
                        ft.ChartAxisLabel(value=16, label=ft.Text("16", size=10, color=COLORS["text_muted"])),
                    ],
                    labels_size=30,
                ),
                bottom_axis=ft.ChartAxis(
                    labels=[],
                    labels_size=30,
                ),
                tooltip_bgcolor=COLORS["surface"],
                expand=True,
            )
        
        # Convert datetime to numeric x values (minutes from start)
        start_time = data_points[0][0]
        chart_points = []
        
        for timestamp, glucose in data_points:
            x = (timestamp - start_time).total_seconds() / 60  # minutes
            chart_points.append(ft.LineChartDataPoint(x, glucose))
        
        max_x = (data_points[-1][0] - start_time).total_seconds() / 60
        
        # Create threshold lines
        low_threshold_points = [
            ft.LineChartDataPoint(0, 3.9),
            ft.LineChartDataPoint(max_x, 3.9),
        ]
        high_threshold_points = [
            ft.LineChartDataPoint(0, 10.0),
            ft.LineChartDataPoint(max_x, 10.0),
        ]
        
        # Time labels for bottom axis
        time_labels = []
        if len(data_points) > 1:
            step = len(data_points) // 4
            for i in range(0, len(data_points), max(step, 1)):
                if i < len(data_points):
                    ts, _ = data_points[i]
                    x = (ts - start_time).total_seconds() / 60
                    time_labels.append(
                        ft.ChartAxisLabel(
                            value=x,
                            label=ft.Text(
                                ts.strftime("%H:%M"),
                                size=10,
                                color=COLORS["text_muted"],
                            ),
                        )
                    )
        
        return ft.LineChart(
            data_series=[
                ft.LineChartData(
                    data_points=low_threshold_points,
                    color=ft.Colors.with_opacity(0.5, COLORS["glucose_low"]),
                    stroke_width=1,
                    curved=False,
                    stroke_cap_round=False,
                ),
                ft.LineChartData(
                    data_points=high_threshold_points,
                    color=ft.Colors.with_opacity(0.5, COLORS["glucose_high"]),
                    stroke_width=1,
                    curved=False,
                    stroke_cap_round=False,
                ),
                ft.LineChartData(
                    data_points=chart_points,
                    color=COLORS["secondary"],
                    stroke_width=2,
                    curved=True,
                    stroke_cap_round=True,
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=[
                            ft.Colors.with_opacity(0.3, COLORS["secondary"]),
                            ft.Colors.with_opacity(0.0, COLORS["secondary"]),
                        ],
                    ),
                ),
            ],
            min_y=2,
            max_y=20,
            min_x=0,
            max_x=max_x if max_x > 0 else 100,
            horizontal_grid_lines=ft.ChartGridLines(
                interval=2,
                color=ft.Colors.with_opacity(0.1, COLORS["text_muted"]),
            ),
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=4, label=ft.Text("4", size=10, color=COLORS["text_muted"])),
                    ft.ChartAxisLabel(value=8, label=ft.Text("8", size=10, color=COLORS["text_muted"])),
                    ft.ChartAxisLabel(value=12, label=ft.Text("12", size=10, color=COLORS["text_muted"])),
                    ft.ChartAxisLabel(value=16, label=ft.Text("16", size=10, color=COLORS["text_muted"])),
                ],
                labels_size=30,
            ),
            bottom_axis=ft.ChartAxis(
                labels=time_labels[:5],
                labels_size=40,
            ),
            tooltip_bgcolor=COLORS["surface"],
            expand=True,
        )

    def _create_stats_grid(self, stats: dict) -> ft.Control:
        """Create statistics grid."""
        return ft.Row(
            [
                self._create_stat_card(
                    "Average",
                    f"{stats.get('avg', 0):.1f}" if stats.get('avg') else "--",
                    "mmol/L",
                    COLORS["secondary"],
                ),
                self._create_stat_card(
                    "Min / Max",
                    f"{stats.get('min', 0):.1f} - {stats.get('max', 0):.1f}" 
                    if stats.get('min') else "-- / --",
                    "mmol/L",
                    COLORS["text_primary"],
                ),
                self._create_stat_card(
                    "Time in Range",
                    f"{stats.get('time_in_range', 0):.0f}%" if stats.get('time_in_range') else "--%",
                    "3.9 - 10.0",
                    COLORS["glucose_normal"] if (stats.get('time_in_range') or 0) >= 70 else COLORS["warning"],
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
            wrap=True,
        )

    def _create_stat_card(
        self,
        title: str,
        value: str,
        subtitle: str,
        value_color: str,
    ) -> ft.Container:
        """Create a statistics card."""
        return card(
            ft.Column(
                [
                    ft.Text(
                        title,
                        size=SIZES["caption"],
                        color=COLORS["text_muted"],
                    ),
                    ft.Text(
                        value,
                        size=SIZES["heading"],
                        weight=ft.FontWeight.W_700,
                        color=value_color,
                    ),
                    ft.Text(
                        subtitle,
                        size=SIZES["caption"],
                        color=COLORS["text_muted"],
                    ),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=SPACING["md"],
        )

    def refresh_data(self) -> None:
        """Refresh chart data from database."""
        try:
            readings = self.get_readings(self._selected_range)
            stats = self.get_stats(self._selected_range)
            
            # Update chart
            self._chart_container.content = self._create_chart(readings)
            
            # Update stats
            self._stats_container.content = self._create_stats_grid(stats)
        except Exception as e:
            print(f"Error refreshing history data: {e}")
