"""Theme and styling for Bear Alarm UI."""

import flet as ft

# Color palette - Warm, health-focused theme
COLORS = {
    # Primary colors
    "background": "#1a1a2e",
    "surface": "#16213e",
    "surface_variant": "#0f3460",
    
    # Accent colors
    "primary": "#e94560",
    "primary_light": "#ff6b6b",
    "secondary": "#00d9ff",
    
    # Glucose state colors
    "glucose_low": "#ff6b6b",
    "glucose_normal": "#4ade80",
    "glucose_high": "#fbbf24",
    "glucose_very_high": "#f97316",
    
    # Text colors
    "text_primary": "#ffffff",
    "text_secondary": "#a0aec0",
    "text_muted": "#718096",
    
    # Status colors
    "success": "#4ade80",
    "warning": "#fbbf24",
    "error": "#ef4444",
    "info": "#00d9ff",
}

# Typography
FONTS = {
    "display": "JetBrains Mono",  # For glucose numbers
    "heading": "Space Grotesk",
    "body": "Inter",
}

# Sizing
SIZES = {
    "glucose_display": 72,
    "glucose_unit": 24,
    "heading": 24,
    "subheading": 18,
    "body": 14,
    "caption": 12,
    "button": 16,
}

# Spacing
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
}


def get_glucose_color(glucose_mmol: float, low_threshold: float = 3.9, high_threshold: float = 10.0) -> str:
    """Get color based on glucose level."""
    if glucose_mmol <= low_threshold:
        return COLORS["glucose_low"]
    elif glucose_mmol >= high_threshold + 3:
        return COLORS["glucose_very_high"]
    elif glucose_mmol >= high_threshold:
        return COLORS["glucose_high"]
    else:
        return COLORS["glucose_normal"]


def styled_button(
    text: str,
    on_click,
    icon: str = None,
    color: str = None,
    bgcolor: str = None,
    width: int = None,
    height: int = 48,
    disabled: bool = False,
) -> ft.ElevatedButton:
    """Create a styled button."""
    return ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(icon, size=20) if icon else None,
                ft.Text(text, size=SIZES["button"], weight=ft.FontWeight.W_600),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            tight=True,
        ),
        on_click=on_click,
        width=width,
        height=height,
        style=ft.ButtonStyle(
            color=color or COLORS["text_primary"],
            bgcolor=bgcolor or COLORS["primary"],
            shape=ft.RoundedRectangleBorder(radius=12),
            elevation=0,
        ),
        disabled=disabled,
    )


def card(content: ft.Control, padding: int = SPACING["md"]) -> ft.Container:
    """Create a styled card container."""
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=COLORS["surface"],
        border_radius=16,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
    )


def section_title(text: str) -> ft.Text:
    """Create a section title."""
    return ft.Text(
        text,
        size=SIZES["subheading"],
        weight=ft.FontWeight.W_600,
        color=COLORS["text_secondary"],
    )

