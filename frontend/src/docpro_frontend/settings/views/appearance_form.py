from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Signal

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.widgets.theme_chip import ThemeChip


_CHIPS = [
    ("light",  "Claro",   "Siempre modo claro"),
    ("dark",   "Oscuro",  "Siempre modo oscuro"),
    ("system", "Sistema", "Sigue Windows 11"),
]


class AppearanceForm(QWidget):
    """Form block: Apariencia — light / dark / system theme selector."""

    theme_changed = Signal(str)  # emits "light" | "dark" | "system" on every chip click

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("APARIENCIA")
        title.setStyleSheet(S.d_section_title())
        layout.addWidget(title)

        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)

        self._chips: dict[str, ThemeChip] = {}
        for key, label, subtitle in _CHIPS:
            chip = ThemeChip(key, label, subtitle, active=(key == "system"))
            chip.selected.connect(self._on_chip_selected)
            chips_row.addWidget(chip)
            self._chips[key] = chip

        layout.addLayout(chips_row)

    # ── Public ────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        active = next((k for k, c in self._chips.items() if c.is_active()), "system")
        return {"theme": active}

    def set_theme(self, mode: str) -> None:
        self._on_chip_selected(mode)

    # ── Internal ──────────────────────────────────────────────────────

    def _on_chip_selected(self, key: str) -> None:
        for k, chip in self._chips.items():
            chip.set_active(k == key)
        self.theme_changed.emit(key)
