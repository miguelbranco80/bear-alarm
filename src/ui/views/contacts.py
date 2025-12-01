"""Contacts view - emergency contacts management."""

from typing import Callable, Optional, TYPE_CHECKING

import flet as ft

from ..theme import COLORS, SIZES, SPACING, card

if TYPE_CHECKING:
    from ...core import Config, EmergencyContactConfig


class ContactsView:
    """Emergency contacts panel."""

    def __init__(
        self,
        config: "Config",
        on_save: Callable[["Config"], None],
        on_call: Callable[[str], None],
        on_message: Callable[[str, str], None],
        page: Optional[ft.Page] = None,
    ):
        self.config = config
        self.on_save = on_save
        self.on_call = on_call
        self.on_message = on_message
        self.page = page
        self._control: Optional[ft.Control] = None
        self._contacts_list: Optional[ft.Column] = None

    def build(self) -> ft.Control:
        """Build the contacts view."""
        
        # Contacts list
        self._contacts_list = ft.Column(
            [self._create_contact_card(c, i) for i, c in enumerate(self.config.alerts.emergency_contacts)],
            spacing=SPACING["md"],
        )
        
        # Empty state
        empty_state = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.PEOPLE_OUTLINE, color=COLORS["text_muted"], size=64),
                    ft.Text(
                        "No emergency contacts",
                        size=SIZES["subheading"],
                        color=COLORS["text_muted"],
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Text(
                        "Add contacts to be notified when alerts trigger",
                        size=SIZES["caption"],
                        color=COLORS["text_muted"],
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=SPACING["md"]),
                    ft.ElevatedButton(
                        "Add Contact",
                        icon=ft.Icons.PERSON_ADD,
                        on_click=self._add_contact,
                        style=ft.ButtonStyle(
                            bgcolor=COLORS["primary"],
                            color=COLORS["text_primary"],
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=SPACING["sm"],
            ),
            padding=SPACING["xl"],
            alignment=ft.alignment.center,
        )
        
        # Header with add button
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "Emergency Contacts",
                                size=SIZES["heading"],
                                weight=ft.FontWeight.W_700,
                                color=COLORS["text_primary"],
                            ),
                            ft.Text(
                                "Get notified via iMessage when alerts trigger",
                                size=SIZES["caption"],
                                color=COLORS["text_muted"],
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PERSON_ADD,
                        icon_color=COLORS["primary"],
                        icon_size=28,
                        on_click=self._add_contact,
                        tooltip="Add contact",
                    ) if self.config.alerts.emergency_contacts else ft.Container(),
                ],
            ),
            padding=ft.padding.only(bottom=SPACING["md"]),
        )
        
        self._control = ft.Container(
            content=ft.Column(
                [
                    header,
                    self._contacts_list if self.config.alerts.emergency_contacts else empty_state,
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=SPACING["lg"],
        )
        
        return self._control

    def _create_contact_card(self, contact: "EmergencyContactConfig", index: int) -> ft.Container:
        """Create a card for a contact."""
        
        # Build notification badges
        badges = []
        if contact.message_on_low:
            badges.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.ARROW_DOWNWARD, size=12, color=COLORS["glucose_low"]),
                            ft.Text("Low", size=11, color=COLORS["glucose_low"]),
                        ],
                        spacing=2,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.15, COLORS["glucose_low"]),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )
            )
        if contact.message_on_high:
            badges.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.ARROW_UPWARD, size=12, color=COLORS["glucose_high"]),
                            ft.Text("High", size=11, color=COLORS["glucose_high"]),
                        ],
                        spacing=2,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.15, COLORS["glucose_high"]),
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=12,
                )
            )
        
        if not badges:
            badges.append(
                ft.Text(
                    "No auto-notifications",
                    size=11,
                    color=COLORS["text_muted"],
                    italic=True,
                )
            )
        
        return card(
            ft.Column(
                [
                    # Top row: toggle, name, actions
                    ft.Row(
                        [
                            ft.Switch(
                                value=contact.enabled,
                                active_color=COLORS["primary"],
                                on_change=lambda e, idx=index: self._toggle_contact(idx, e.control.value),
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        contact.name,
                                        size=SIZES["body"],
                                        weight=ft.FontWeight.W_600,
                                        color=COLORS["text_primary"] if contact.enabled else COLORS["text_muted"],
                                    ),
                                    ft.Text(
                                        contact.phone,
                                        size=SIZES["caption"],
                                        color=COLORS["text_muted"],
                                    ),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.VIDEO_CALL,
                                icon_color=COLORS["success"],
                                icon_size=24,
                                on_click=lambda _, c=contact: self.on_call(c.phone),
                                tooltip="FaceTime",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_color=COLORS["text_muted"],
                                icon_size=20,
                                on_click=lambda _, idx=index: self._edit_contact(idx),
                                tooltip="Edit",
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=COLORS["error"],
                                icon_size=20,
                                on_click=lambda _, idx=index: self._delete_contact(idx),
                                tooltip="Delete",
                            ),
                        ],
                    ),
                    # Badges row
                    ft.Row(badges, spacing=SPACING["xs"]),
                ],
                spacing=SPACING["sm"],
            ),
            padding=SPACING["md"],
        )

    def _add_contact(self, _) -> None:
        """Add a new contact."""
        from ...core import EmergencyContactConfig
        
        new_contact = EmergencyContactConfig(
            name="",
            phone="",
        )
        self.config.alerts.emergency_contacts.append(new_contact)
        self._edit_contact(len(self.config.alerts.emergency_contacts) - 1, is_new=True)

    def _toggle_contact(self, index: int, enabled: bool) -> None:
        """Toggle a contact on/off."""
        self.config.alerts.emergency_contacts[index].enabled = enabled
        self._save()
        self._refresh_contacts()

    def _edit_contact(self, index: int, is_new: bool = False) -> None:
        """Open contact editor dialog."""
        contact = self.config.alerts.emergency_contacts[index]
        
        name_field = ft.TextField(
            value=contact.name,
            label="Name",
            hint_text="e.g., Partner, Mom",
            autofocus=is_new,
        )
        phone_field = ft.TextField(
            value=contact.phone,
            label="Phone or Apple ID",
            hint_text="+1234567890 or email@icloud.com",
        )
        
        # Low alert section
        low_enabled = ft.Checkbox(value=contact.message_on_low)
        low_snooze = ft.Dropdown(
            value=str(contact.message_on_low_snooze),
            options=[
                ft.dropdown.Option("15", "15m"),
                ft.dropdown.Option("30", "30m"),
                ft.dropdown.Option("60", "1h"),
                ft.dropdown.Option("120", "2h"),
            ],
            width=80,
            text_size=12,
            dense=True,
        )
        low_message = ft.TextField(
            value=contact.low_message_text,
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        
        # High alert section
        high_enabled = ft.Checkbox(value=contact.message_on_high)
        high_snooze = ft.Dropdown(
            value=str(contact.message_on_high_snooze),
            options=[
                ft.dropdown.Option("30", "30m"),
                ft.dropdown.Option("60", "1h"),
                ft.dropdown.Option("120", "2h"),
                ft.dropdown.Option("240", "4h"),
            ],
            width=80,
            text_size=12,
            dense=True,
        )
        high_message = ft.TextField(
            value=contact.high_message_text,
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        
        def save_contact(_):
            if not name_field.value or not phone_field.value:
                return
            
            contact.name = name_field.value
            contact.phone = phone_field.value
            
            contact.message_on_low = low_enabled.value
            contact.message_on_low_snooze = int(low_snooze.value)
            contact.low_message_text = low_message.value
            
            contact.message_on_high = high_enabled.value
            contact.message_on_high_snooze = int(high_snooze.value)
            contact.high_message_text = high_message.value
            
            dialog.open = False
            self.page.update()
            self._save()
            self._refresh_contacts()
        
        def cancel(_):
            if is_new:
                del self.config.alerts.emergency_contacts[index]
            dialog.open = False
            self.page.update()
            self._refresh_contacts()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add Contact" if is_new else "Edit Contact"),
            content=ft.Container(
                content=ft.Column(
                    [
                        name_field,
                        phone_field,
                        
                        ft.Container(height=SPACING["md"]),
                        ft.Text("Auto-Notifications", weight=ft.FontWeight.W_600, size=SIZES["body"]),
                        
                        # Low alerts
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    low_enabled,
                                    ft.Text("Message on LOW alert", expand=True),
                                    ft.Text("Snooze:", size=SIZES["caption"], color=COLORS["text_muted"]),
                                    low_snooze,
                                ]),
                                low_message,
                            ], spacing=SPACING["xs"]),
                            bgcolor=ft.Colors.with_opacity(0.1, COLORS["glucose_low"]),
                            padding=SPACING["sm"],
                            border_radius=8,
                        ),
                        
                        # High alerts  
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    high_enabled,
                                    ft.Text("Message on HIGH alert", expand=True),
                                    ft.Text("Snooze:", size=SIZES["caption"], color=COLORS["text_muted"]),
                                    high_snooze,
                                ]),
                                high_message,
                            ], spacing=SPACING["xs"]),
                            bgcolor=ft.Colors.with_opacity(0.1, COLORS["glucose_high"]),
                            padding=SPACING["sm"],
                            border_radius=8,
                        ),
                    ],
                    spacing=SPACING["sm"],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=450,
                height=480,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton(
                    "Save",
                    on_click=save_contact,
                    style=ft.ButtonStyle(bgcolor=COLORS["primary"], color=COLORS["text_primary"]),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _delete_contact(self, index: int) -> None:
        """Delete a contact."""
        def confirm_delete(_):
            del self.config.alerts.emergency_contacts[index]
            dialog.open = False
            self.page.update()
            self._save()
            self._refresh_contacts()
        
        def cancel(_):
            dialog.open = False
            self.page.update()
        
        contact = self.config.alerts.emergency_contacts[index]
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Contact?"),
            content=ft.Text(f"Remove {contact.name}?"),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.TextButton(
                    "Delete",
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(color=COLORS["error"]),
                ),
            ],
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def _refresh_contacts(self) -> None:
        """Refresh the contacts list."""
        if self._contacts_list:
            self._contacts_list.controls = [
                self._create_contact_card(c, i) 
                for i, c in enumerate(self.config.alerts.emergency_contacts)
            ]
            if self.page:
                self.page.update()

    def _save(self) -> None:
        """Save config changes."""
        self.on_save(self.config)

    def update_config(self, config: "Config") -> None:
        """Update with new config."""
        self.config = config
