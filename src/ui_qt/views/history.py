"""History view - glucose charts and statistics."""

from datetime import datetime, timedelta
from typing import Callable, Optional

from PySide6.QtCore import Qt, QMargins
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QGridLayout, QButtonGroup
)
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis



class HistoryView(QWidget):
    """Glucose history with charts."""

    def __init__(
        self,
        get_readings: Callable[[int], list],
        get_stats: Callable[[int], dict],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.get_readings = get_readings
        self.get_stats = get_stats
        self._selected_range = 6
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Time range selector
        range_group = QButtonGroup(self)
        range_layout = QHBoxLayout()
        range_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._range_buttons = {}
        for hours, label in [(3, "3h"), (6, "6h"), (12, "12h"), (24, "24h"), (72, "3d"), (168, "7d")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(hours == self._selected_range)
            btn.clicked.connect(lambda checked, h=hours: self._select_range(h))
            range_group.addButton(btn)
            self._range_buttons[hours] = btn
            range_layout.addWidget(btn)
        
        layout.addLayout(range_layout)
        
        # Chart
        self._chart = QChart()
        self._chart.legend().hide()
        self._chart.setMargins(QMargins(10, 10, 10, 10))
        
        self._series = QLineSeries()
        self._series.setColor(QColor("#007AFF"))  # Apple blue
        pen = QPen(QColor("#007AFF"))
        pen.setWidth(2)
        self._series.setPen(pen)
        self._chart.addSeries(self._series)
        
        # Axes
        self._axis_x = QDateTimeAxis()
        self._axis_x.setFormat("HH:mm")
        self._chart.addAxis(self._axis_x, Qt.AlignmentFlag.AlignBottom)
        self._series.attachAxis(self._axis_x)
        
        self._axis_y = QValueAxis()
        self._axis_y.setRange(2, 20)
        self._axis_y.setLabelFormat("%.1f")
        self._chart.addAxis(self._axis_y, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(self._axis_y)
        
        chart_view = QChartView(self._chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        chart_view.setMinimumHeight(250)
        layout.addWidget(chart_view)
        
        # Stats
        stats_group = QGroupBox("Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self._stat_labels = {}
        for i, (key, label) in enumerate([("avg", "Average"), ("min", "Lowest"), ("max", "Highest"), ("in_range", "In Range")]):
            title = QLabel(label)
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_layout.addWidget(title, 0, i)
            
            value = QLabel("—")
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = value.font()
            font.setPointSize(16)
            font.setBold(True)
            value.setFont(font)
            self._stat_labels[key] = value
            stats_layout.addWidget(value, 1, i)
        
        layout.addWidget(stats_group)
        layout.addStretch()

    def _select_range(self, hours: int) -> None:
        """Select time range."""
        if hours == self._selected_range:
            return
        
        self._selected_range = hours
        for h, btn in self._range_buttons.items():
            btn.setChecked(h == hours)
        self.refresh_data()

    def refresh_data(self) -> None:
        """Refresh chart and stats."""
        readings = self.get_readings(self._selected_range)
        stats = self.get_stats(self._selected_range)
        
        self._series.clear()
        if readings:
            min_time = datetime.now() - timedelta(hours=self._selected_range)
            max_time = datetime.now()
            
            # Readings are tuples: (timestamp, glucose_mmol)
            for ts, value in readings:
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                self._series.append(ts.timestamp() * 1000, value)
            
            self._axis_x.setRange(min_time, max_time)
            
            values = [v for _, v in readings]
            if values:
                self._axis_y.setRange(max(0, min(values) - 1), max(values) + 1)
        
        if stats:
            if stats.get("avg") is not None:
                self._stat_labels["avg"].setText(f"{stats['avg']:.1f}")
            if stats.get("min") is not None:
                self._stat_labels["min"].setText(f"{stats['min']:.1f}")
            if stats.get("max") is not None:
                self._stat_labels["max"].setText(f"{stats['max']:.1f}")
            if stats.get("time_in_range") is not None:
                self._stat_labels["in_range"].setText(f"{stats['time_in_range']:.0f}%")
