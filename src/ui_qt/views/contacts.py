"""Contacts view - emergency contacts management."""

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QTextEdit, QGroupBox, QGridLayout
)

from ...core import Config, EmergencyContactConfig, call_facetime, send_imessage


class ContactsView(QWidget):
    """Emergency contacts management."""

    def __init__(
        self,
        config: Config,
        on_save: Callable[[dict], None],
        on_call: Callable[[str], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.config = config
        self.on_save = on_save
        self.on_call = on_call
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Subtitle (same style as other views)
        subtitle = QLabel("Auto-message contacts during glucose alerts")
        subtitle.setEnabled(False)
        layout.addWidget(subtitle)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setSpacing(12)
        
        self._contact_list = QVBoxLayout()
        self._refresh_contacts()
        self._content_layout.addLayout(self._contact_list)
        
        add_btn = QPushButton("+ Add Contact")
        add_btn.clicked.connect(self._add_contact)
        self._content_layout.addWidget(add_btn)
        
        self._content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _refresh_contacts(self) -> None:
        """Refresh contact list."""
        while self._contact_list.count():
            item = self._contact_list.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, contact in enumerate(self.config.alerts.emergency_contacts):
            card = self._create_contact_card(contact, i)
            self._contact_list.addWidget(card)

    def _create_contact_card(self, contact: EmergencyContactConfig, index: int) -> QFrame:
        """Create a contact card."""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        # Top row
        top = QHBoxLayout()
        
        enable_cb = QCheckBox()
        enable_cb.setChecked(contact.enabled)
        enable_cb.stateChanged.connect(lambda state, i=index: self._toggle_contact(i, state == Qt.CheckState.Checked.value))
        top.addWidget(enable_cb)
        
        info = QVBoxLayout()
        info.setSpacing(2)
        
        name = QLabel(contact.name)
        font = name.font()
        font.setBold(True)
        name.setFont(font)
        name.setEnabled(contact.enabled)
        info.addWidget(name)
        
        phone = QLabel(contact.phone or "No phone")
        phone.setEnabled(False)
        info.addWidget(phone)
        top.addLayout(info, 1)
        
        call_btn = QPushButton("Call")
        call_btn.setToolTip("FaceTime")
        call_btn.clicked.connect(lambda: self.on_call(contact.phone))
        top.addWidget(call_btn)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(lambda: self._edit_contact(index))
        top.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self._delete_contact(index))
        top.addWidget(delete_btn)
        
        layout.addLayout(top)
        
        # Alert settings summary
        alerts = []
        if contact.message_on_low:
            alerts.append(f"Low alert: {contact.message_on_low_snooze}min snooze")
        if contact.message_on_high:
            alerts.append(f"High alert: {contact.message_on_high_snooze}min snooze")
        
        if alerts:
            alerts_label = QLabel(" • ".join(alerts))
            alerts_label.setEnabled(False)  # Grayed out secondary text
            layout.addWidget(alerts_label)
        
        return card

    def _add_contact(self) -> None:
        """Add new contact."""
        new_contact = EmergencyContactConfig(
            name=f"Contact {len(self.config.alerts.emergency_contacts) + 1}"
        )
        self.config.alerts.emergency_contacts.append(new_contact)
        self._refresh_contacts()
        self._edit_contact(len(self.config.alerts.emergency_contacts) - 1)

    def _edit_contact(self, index: int) -> None:
        """Edit contact."""
        contact = self.config.alerts.emergency_contacts[index]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Contact")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        # Basic info
        basic_group = QGroupBox("Contact Info")
        basic_layout = QGridLayout(basic_group)
        
        basic_layout.addWidget(QLabel("Name:"), 0, 0)
        name_edit = QLineEdit(contact.name)
        basic_layout.addWidget(name_edit, 0, 1)
        
        basic_layout.addWidget(QLabel("Phone:"), 1, 0)
        phone_edit = QLineEdit(contact.phone)
        phone_edit.setPlaceholderText("+1234567890")
        basic_layout.addWidget(phone_edit, 1, 1)
        
        layout.addWidget(basic_group)
        
        # Low alert
        low_group = QGroupBox("Low Glucose Alert")
        low_layout = QVBoxLayout(low_group)
        
        low_enable = QCheckBox("Auto-message on low alert")
        low_enable.setChecked(contact.message_on_low)
        low_layout.addWidget(low_enable)
        
        low_snooze_layout = QHBoxLayout()
        low_snooze_layout.addWidget(QLabel("Snooze:"))
        low_snooze = QComboBox()
        low_snooze.addItems(["15 min", "30 min", "1 hour", "2 hours", "4 hours"])
        snooze_values = [15, 30, 60, 120, 240]
        current_idx = snooze_values.index(contact.message_on_low_snooze) if contact.message_on_low_snooze in snooze_values else 1
        low_snooze.setCurrentIndex(current_idx)
        low_snooze_layout.addWidget(low_snooze)
        low_snooze_layout.addStretch()
        low_layout.addLayout(low_snooze_layout)
        
        low_msg = QTextEdit(contact.low_message_text)
        low_msg.setMaximumHeight(60)
        low_msg.setPlaceholderText("Message to send on low alert")
        low_layout.addWidget(low_msg)
        
        layout.addWidget(low_group)
        
        # High alert
        high_group = QGroupBox("High Glucose Alert")
        high_layout = QVBoxLayout(high_group)
        
        high_enable = QCheckBox("Auto-message on high alert")
        high_enable.setChecked(contact.message_on_high)
        high_layout.addWidget(high_enable)
        
        high_snooze_layout = QHBoxLayout()
        high_snooze_layout.addWidget(QLabel("Snooze:"))
        high_snooze = QComboBox()
        high_snooze.addItems(["30 min", "1 hour", "2 hours", "4 hours", "8 hours"])
        snooze_values_high = [30, 60, 120, 240, 480]
        current_idx_high = snooze_values_high.index(contact.message_on_high_snooze) if contact.message_on_high_snooze in snooze_values_high else 1
        high_snooze.setCurrentIndex(current_idx_high)
        high_snooze_layout.addWidget(high_snooze)
        high_snooze_layout.addStretch()
        high_layout.addLayout(high_snooze_layout)
        
        high_msg = QTextEdit(contact.high_message_text)
        high_msg.setMaximumHeight(60)
        high_msg.setPlaceholderText("Message to send on high alert")
        high_layout.addWidget(high_msg)
        
        layout.addWidget(high_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            contact.name = name_edit.text() or f"Contact {index + 1}"
            contact.phone = phone_edit.text()
            contact.message_on_low = low_enable.isChecked()
            contact.message_on_low_snooze = snooze_values[low_snooze.currentIndex()]
            contact.low_message_text = low_msg.toPlainText()
            contact.message_on_high = high_enable.isChecked()
            contact.message_on_high_snooze = snooze_values_high[high_snooze.currentIndex()]
            contact.high_message_text = high_msg.toPlainText()
            self._refresh_contacts()
            self._save()

    def _toggle_contact(self, index: int, enabled: bool) -> None:
        """Toggle contact enabled state."""
        self.config.alerts.emergency_contacts[index].enabled = enabled
        self._refresh_contacts()
        self._save()

    def _delete_contact(self, index: int) -> None:
        """Delete contact."""
        del self.config.alerts.emergency_contacts[index]
        self._refresh_contacts()
        self._save()

    def _save(self) -> None:
        """Save contacts."""
        self.on_save(self.config.model_dump())

    def refresh_ui(self) -> None:
        """Refresh UI."""
        self._refresh_contacts()
