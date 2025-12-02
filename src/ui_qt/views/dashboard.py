"""Dashboard view - main glucose display."""

from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGroupBox
)
from PySide6.QtGui import QFont

from ..theme import get_glucose_color


class DashboardSignals(QObject):
    """Signals for dashboard updates."""
    glucose_updated = Signal(float, str, datetime)
    snooze_updated = Signal(object)  # datetime or None
    connection_status = Signal(bool, str)


class DashboardView(QWidget):
    """Main dashboard showing current glucose."""

    def __init__(
        self,
        on_snooze: Callable[[int], None],
        on_cancel_snooze: Callable[[], None],
        on_call_contact: Callable[[str], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.on_snooze = on_snooze
        self.on_cancel_snooze = on_cancel_snooze
        self.on_call_contact = on_call_contact
        self.signals = DashboardSignals()
        
        self._current_glucose: Optional[float] = None
        self._snooze_until: Optional[datetime] = None
        self._setup_ui()
        
        # Connect signals
        self.signals.glucose_updated.connect(self._on_glucose_updated)
        self.signals.snooze_updated.connect(self._on_snooze_updated)
        self.signals.connection_status.connect(self._on_connection_status)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Main glucose display
        glucose_group = QGroupBox("Current Glucose")
        glucose_layout = QVBoxLayout(glucose_group)
        glucose_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glucose_layout.setSpacing(4)
        
        # Glucose value
        self._glucose_label = QLabel("--.-")
        self._glucose_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(64)
        font.setBold(True)
        self._glucose_label.setFont(font)
        glucose_layout.addWidget(self._glucose_label)
        
        # Unit and trend row
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._unit_label = QLabel("mmol/L")
        info_layout.addWidget(self._unit_label)
        
        self._trend_label = QLabel("")
        trend_font = QFont()
        trend_font.setPointSize(20)
        self._trend_label.setFont(trend_font)
        info_layout.addWidget(self._trend_label)
        
        glucose_layout.addLayout(info_layout)
        
        # Status text
        self._status_label = QLabel("Waiting for data...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        glucose_layout.addWidget(self._status_label)
        
        layout.addWidget(glucose_group)
        
        # Snooze buttons
        snooze_group = QGroupBox("Snooze Alerts")
        snooze_layout = QHBoxLayout(snooze_group)
        snooze_layout.setSpacing(8)
        
        for minutes, label in [(15, "15m"), (30, "30m"), (60, "1h"), (120, "2h")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, m=minutes: self.on_snooze(m))
            snooze_layout.addWidget(btn)
        
        layout.addWidget(snooze_group)
        
        # Emergency contacts
        self._contacts_group = QGroupBox("Emergency Call")
        self._contacts_layout = QHBoxLayout(self._contacts_group)
        self._contacts_layout.setSpacing(8)
        self._contacts_group.hide()
        layout.addWidget(self._contacts_group)
        
        # Last check
        self._last_check_label = QLabel("Last check: --")
        self._last_check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._last_check_label)
        
        # Spacer pushes snooze banner to bottom
        layout.addStretch()
        
        # Snooze active banner - single line at bottom
        self._snooze_banner = QFrame()
        snooze_banner_layout = QHBoxLayout(self._snooze_banner)
        snooze_banner_layout.setContentsMargins(12, 8, 12, 8)
        
        self._snooze_label = QLabel("")
        snooze_font = QFont()
        snooze_font.setBold(True)
        self._snooze_label.setFont(snooze_font)
        snooze_banner_layout.addWidget(self._snooze_label, 1)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(lambda: self.on_cancel_snooze())
        snooze_banner_layout.addWidget(cancel_btn)
        
        self._snooze_banner.hide()
        layout.addWidget(self._snooze_banner)

    def _on_glucose_updated(self, value: float, trend: str, timestamp: datetime) -> None:
        """Handle glucose update."""
        self._current_glucose = value
        self._glucose_label.setText(f"{value:.1f}")
        self._trend_label.setText(trend)
        
        color = get_glucose_color(value)
        self._glucose_label.setStyleSheet(f"color: {color};")
        self._trend_label.setStyleSheet(f"color: {color};")
        
        # Show age of reading
        from datetime import timezone
        now = datetime.now(timezone.utc)
        reading_utc = timestamp.replace(tzinfo=timezone.utc) if timestamp.tzinfo is None else timestamp
        age_minutes = (now - reading_utc).total_seconds() / 60
        
        if age_minutes > 15:
            self._status_label.setText(f"⚠️ Data is {int(age_minutes)} min old!")
        else:
            self._status_label.setText(f"Updated {timestamp.strftime('%H:%M')}")
        
        self._last_check_label.setText(f"Reading from: {timestamp.strftime('%H:%M:%S')}")

    def _on_snooze_updated(self, until: Optional[datetime]) -> None:
        """Handle snooze state update."""
        self._snooze_until = until
        if until:
            self._snooze_label.setText(f"ALERTS SNOOZED UNTIL {until.strftime('%H:%M')}")
            self._snooze_banner.show()
        else:
            self._snooze_banner.hide()

    def _on_connection_status(self, connected: bool, message: str) -> None:
        """Handle connection status update."""
        prefix = "❌ " if not connected else ""
        self._status_label.setText(f"{prefix}{message}")

    def update_glucose(self, value: float, trend: str, timestamp: datetime) -> None:
        """Update glucose display (thread-safe via signal)."""
        self.signals.glucose_updated.emit(value, trend, timestamp)

    def update_snooze_state(self, until: Optional[datetime]) -> None:
        """Update snooze state (thread-safe via signal)."""
        self.signals.snooze_updated.emit(until)

    def update_connection_status(self, connected: bool, message: str) -> None:
        """Update connection status (thread-safe via signal)."""
        self.signals.connection_status.emit(connected, message)

    def update_contacts(self, contacts: list) -> None:
        """Update emergency contacts display."""
        # Clear existing
        while self._contacts_layout.count():
            item = self._contacts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        has_contacts = False
        for contact in contacts:
            if contact.enabled:
                has_contacts = True
                btn = QPushButton(f"Call {contact.name}")
                btn.clicked.connect(lambda checked, phone=contact.phone: self.on_call_contact(phone))
                self._contacts_layout.addWidget(btn)
        
        self._contacts_group.setVisible(has_contacts)
