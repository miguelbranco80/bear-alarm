"""Theme - minimal, uses native system styling."""

from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication) -> None:
    """No custom styling - use system native."""
    pass


# No stylesheet - fully native
STYLESHEET = ""


def get_glucose_color(value: float, low: float = 3.9, high: float = 10.0) -> str:
    """Get color for glucose value - only place we use custom colors."""
    if value <= low:
        return "#cc0000"  # Dark red - readable
    elif value >= high:
        return "#cc6600"  # Dark orange - readable
    return "#006600"  # Dark green - readable

