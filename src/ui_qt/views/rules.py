"""Rules view - alert thresholds and schedules."""

from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QDoubleSpinBox, QSpinBox, QLineEdit,
    QDialog, QDialogButtonBox, QCheckBox, QGridLayout, QGroupBox
)

from ...core import Config, ScheduleConfig

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class RulesView(QWidget):
    """Alert rules and schedules configuration with auto-save."""

    def __init__(
        self,
        config: Config,
        on_save: Callable[[dict], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        
        # Debounce timer for auto-save
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save)
        
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)
        
        # Default thresholds section
        defaults_group = QGroupBox("Default Alert Thresholds")
        defaults_layout = QGridLayout(defaults_group)
        defaults_layout.setSpacing(8)
        defaults_layout.setColumnMinimumWidth(0, 100)  # Label column
        
        row = 0
        
        # Low threshold
        defaults_layout.addWidget(QLabel("Low Threshold:"), row, 0)
        self._low_spin = QDoubleSpinBox()
        self._low_spin.setRange(2.0, 5.0)
        self._low_spin.setSingleStep(0.1)
        self._low_spin.setValue(self.config.alerts.low_threshold)
        self._low_spin.setSuffix(" mmol/L")
        defaults_layout.addWidget(self._low_spin, row, 1)
        row += 1
        
        # High threshold
        defaults_layout.addWidget(QLabel("High Threshold:"), row, 0)
        self._high_spin = QDoubleSpinBox()
        self._high_spin.setRange(8.0, 20.0)
        self._high_spin.setSingleStep(0.5)
        self._high_spin.setValue(self.config.alerts.high_threshold)
        self._high_spin.setSuffix(" mmol/L")
        defaults_layout.addWidget(self._high_spin, row, 1)
        row += 1
        
        # Urgent low
        defaults_layout.addWidget(QLabel("Urgent Low:"), row, 0)
        self._urgent_spin = QDoubleSpinBox()
        self._urgent_spin.setRange(1.5, 3.5)
        self._urgent_spin.setSingleStep(0.1)
        self._urgent_spin.setValue(self.config.alerts.urgent_low)
        self._urgent_spin.setSuffix(" mmol/L")
        defaults_layout.addWidget(self._urgent_spin, row, 1)
        urgent_note = QLabel("(bypasses snooze)")
        urgent_note.setEnabled(False)
        defaults_layout.addWidget(urgent_note, row, 2)
        row += 1
        
        # Persistence timers
        defaults_layout.addWidget(QLabel("Low Wait:"), row, 0)
        self._low_persist = QSpinBox()
        self._low_persist.setRange(0, 30)
        self._low_persist.setValue(self.config.alerts.low_persist_minutes)
        self._low_persist.setSuffix(" min")
        defaults_layout.addWidget(self._low_persist, row, 1)
        row += 1
        
        defaults_layout.addWidget(QLabel("High Wait:"), row, 0)
        self._high_persist = QSpinBox()
        self._high_persist.setRange(0, 60)
        self._high_persist.setValue(self.config.alerts.high_persist_minutes)
        self._high_persist.setSuffix(" min")
        defaults_layout.addWidget(self._high_persist, row, 1)
        row += 1
        
        persist_note = QLabel("Wait time before alerting (0 = immediate)")
        persist_note.setEnabled(False)
        defaults_layout.addWidget(persist_note, row, 0, 1, 3)
        
        content_layout.addWidget(defaults_group)
        
        # Schedules section
        schedules_group = QGroupBox("Schedules")
        self._schedules_layout = QVBoxLayout(schedules_group)
        self._schedules_layout.setSpacing(8)
        
        schedules_note = QLabel("Override default thresholds during specific times")
        schedules_note.setEnabled(False)
        self._schedules_layout.addWidget(schedules_note)
        
        # Schedule list
        self._schedule_list = QVBoxLayout()
        self._refresh_schedules()
        self._schedules_layout.addLayout(self._schedule_list)
        
        # Add schedule button
        add_btn = QPushButton("+ Add Schedule")
        add_btn.clicked.connect(self._add_schedule)
        self._schedules_layout.addWidget(add_btn)
        
        content_layout.addWidget(schedules_group)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Connect inputs to auto-save
        self._low_spin.valueChanged.connect(self._schedule_save)
        self._high_spin.valueChanged.connect(self._schedule_save)
        self._urgent_spin.valueChanged.connect(self._schedule_save)
        self._low_persist.valueChanged.connect(self._schedule_save)
        self._high_persist.valueChanged.connect(self._schedule_save)
    
    def _schedule_save(self) -> None:
        """Schedule auto-save after a short delay."""
        self._save_timer.start(500)

    def _refresh_schedules(self) -> None:
        """Refresh schedule list."""
        # Clear existing
        while self._schedule_list.count():
            item = self._schedule_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add schedule cards
        for i, schedule in enumerate(self.config.alerts.schedules):
            card = self._create_schedule_card(schedule, i)
            self._schedule_list.addWidget(card)

    def _create_schedule_card(self, schedule: ScheduleConfig, index: int) -> QFrame:
        """Create a schedule card widget."""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QHBoxLayout(card)
        
        # Info
        info_layout = QVBoxLayout()
        
        name_label = QLabel(schedule.name)
        info_layout.addWidget(name_label)
        
        days_str = ", ".join(DAY_NAMES[d] for d in sorted(schedule.days))
        time_str = f"{schedule.start_time} - {schedule.end_time}"
        details = QLabel(f"{days_str} • {time_str}")
        details.setEnabled(False)
        info_layout.addWidget(details)
        
        layout.addLayout(info_layout, 1)
        
        # Buttons
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self._edit_schedule(index))
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self._delete_schedule(index))
        layout.addWidget(delete_btn)
        
        return card

    def _add_schedule(self) -> None:
        """Add a new schedule."""
        new_schedule = ScheduleConfig(
            name=f"Schedule {len(self.config.alerts.schedules) + 1}",
            priority=len(self.config.alerts.schedules) + 1,
        )
        self.config.alerts.schedules.append(new_schedule)
        self._refresh_schedules()
        self._edit_schedule(len(self.config.alerts.schedules) - 1)

    def _edit_schedule(self, index: int) -> None:
        """Edit a schedule."""
        schedule = self.config.alerts.schedules[index]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Schedule")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        name_edit = QLineEdit(schedule.name)
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        # Time
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time:"))
        start_edit = QLineEdit(schedule.start_time)
        start_edit.setPlaceholderText("09:00")
        start_edit.setMaximumWidth(80)
        time_layout.addWidget(start_edit)
        time_layout.addWidget(QLabel("→"))
        end_edit = QLineEdit(schedule.end_time)
        end_edit.setPlaceholderText("17:00")
        end_edit.setMaximumWidth(80)
        time_layout.addWidget(end_edit)
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # Days
        days_layout = QHBoxLayout()
        days_layout.addWidget(QLabel("Days:"))
        day_checks = []
        for i, name in enumerate(DAY_NAMES):
            cb = QCheckBox(name)
            cb.setChecked(i in schedule.days)
            day_checks.append(cb)
            days_layout.addWidget(cb)
        layout.addLayout(days_layout)
        
        # Overrides
        overrides_group = QGroupBox("Override Thresholds (leave empty for default)")
        overrides_layout = QGridLayout(overrides_group)
        
        overrides_layout.addWidget(QLabel("Low:"), 0, 0)
        low_edit = QDoubleSpinBox()
        low_edit.setRange(0, 5.0)
        low_edit.setSpecialValueText("—")
        low_edit.setValue(schedule.low_threshold or 0)
        overrides_layout.addWidget(low_edit, 0, 1)
        
        overrides_layout.addWidget(QLabel("High:"), 0, 2)
        high_edit = QDoubleSpinBox()
        high_edit.setRange(0, 20.0)
        high_edit.setSpecialValueText("—")
        high_edit.setValue(schedule.high_threshold or 0)
        overrides_layout.addWidget(high_edit, 0, 3)
        
        overrides_layout.addWidget(QLabel("Low wait:"), 1, 0)
        low_persist_edit = QSpinBox()
        low_persist_edit.setRange(-1, 30)
        low_persist_edit.setSpecialValueText("—")
        low_persist_edit.setValue(schedule.low_persist_minutes if schedule.low_persist_minutes is not None else -1)
        overrides_layout.addWidget(low_persist_edit, 1, 1)
        
        overrides_layout.addWidget(QLabel("High wait:"), 1, 2)
        high_persist_edit = QSpinBox()
        high_persist_edit.setRange(-1, 60)
        high_persist_edit.setSpecialValueText("—")
        high_persist_edit.setValue(schedule.high_persist_minutes if schedule.high_persist_minutes is not None else -1)
        overrides_layout.addWidget(high_persist_edit, 1, 3)
        
        layout.addWidget(overrides_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            schedule.name = name_edit.text() or f"Schedule {index + 1}"
            schedule.start_time = start_edit.text() or "00:00"
            schedule.end_time = end_edit.text() or "23:59"
            schedule.days = [i for i, cb in enumerate(day_checks) if cb.isChecked()]
            schedule.low_threshold = low_edit.value() if low_edit.value() > 0 else None
            schedule.high_threshold = high_edit.value() if high_edit.value() > 0 else None
            schedule.low_persist_minutes = low_persist_edit.value() if low_persist_edit.value() >= 0 else None
            schedule.high_persist_minutes = high_persist_edit.value() if high_persist_edit.value() >= 0 else None
            self._refresh_schedules()
            self._save()

    def _delete_schedule(self, index: int) -> None:
        """Delete a schedule."""
        del self.config.alerts.schedules[index]
        self._refresh_schedules()
        self._save()

    def _save(self) -> None:
        """Save rules."""
        self.config.alerts.low_threshold = self._low_spin.value()
        self.config.alerts.high_threshold = self._high_spin.value()
        self.config.alerts.urgent_low = self._urgent_spin.value()
        self.config.alerts.low_persist_minutes = self._low_persist.value()
        self.config.alerts.high_persist_minutes = self._high_persist.value()
        
        self.on_save(self.config.model_dump())

    def refresh_ui(self) -> None:
        """Refresh UI with current config."""
        self._low_spin.setValue(self.config.alerts.low_threshold)
        self._high_spin.setValue(self.config.alerts.high_threshold)
        self._urgent_spin.setValue(self.config.alerts.urgent_low)
        self._low_persist.setValue(self.config.alerts.low_persist_minutes)
        self._high_persist.setValue(self.config.alerts.high_persist_minutes)
        self._refresh_schedules()

