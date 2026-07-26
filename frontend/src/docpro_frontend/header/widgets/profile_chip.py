"""Profile switcher chip: shows the active profile and opens a menu with
list of profiles + actions to create / rename."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QPushButton


_CHIP_STYLE = """
QPushButton {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 11px;
    padding: 7px 14px;
    font-size: 16px;
    font-weight: 500;
    color: #374151;
    text-align: left;
}
QPushButton:hover { background: #F3F4F6; }
QPushButton::menu-indicator { image: none; width: 0; }
"""

_MENU_STYLE = """
QMenu {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 6px 0;
    color: #111827;
}
QMenu::item {
    padding: 8px 20px 8px 32px;
    font-size: 15px;
}
QMenu::item:selected {
    background: #FEF3C7;
    color: #B45309;
}
QMenu::separator {
    height: 1px;
    background: #E5E7EB;
    margin: 6px 8px;
}
QMenu::icon { padding-left: 12px; }
"""


class ProfileChip(QPushButton):
    """Compact button that shows the active profile and a dropdown menu."""

    switch_requested = Signal(str)   # slug
    new_profile_requested = Signal()
    rename_profile_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(_CHIP_STYLE)
        self.setMinimumHeight(38)
        self._active_slug: str = ""
        self._profiles: list[dict] = []
        self._menu = QMenu(self)
        self._menu.setStyleSheet(_MENU_STYLE)
        self.setMenu(self._menu)

    # ── Public API ────────────────────────────────────────────────────

    def set_profiles(self, profiles: list[dict], active_slug: str) -> None:
        self._profiles = list(profiles)
        self._active_slug = active_slug
        active = next((p for p in profiles if p["slug"] == active_slug), None)
        label = active["name"] if active else "Perfil"
        self.setText(f"{label}  ▾")
        self._rebuild_menu()

    # ── Internal ──────────────────────────────────────────────────────

    def _rebuild_menu(self) -> None:
        self._menu.clear()
        for p in self._profiles:
            mark = "•  " if p["slug"] == self._active_slug else "    "
            action = QAction(f"{mark}{p['name']}", self._menu)
            slug = p["slug"]
            action.triggered.connect(lambda _=False, s=slug: self.switch_requested.emit(s))
            if slug == self._active_slug:
                f = action.font()
                f.setBold(True)
                action.setFont(f)
            self._menu.addAction(action)
        self._menu.addSeparator()

        new_action = QAction("+  Nuevo perfil…", self._menu)
        new_action.triggered.connect(self.new_profile_requested)
        self._menu.addAction(new_action)

        rename_action = QAction("Renombrar perfil actual…", self._menu)
        rename_action.triggered.connect(self.rename_profile_requested)
        self._menu.addAction(rename_action)
