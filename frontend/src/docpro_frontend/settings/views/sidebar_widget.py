from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.widgets.nav_item import NavItem


_SECTIONS: list[dict] = [
    {
        "label": "General",
        "items": [
            {"key": "perfil",     "icon": "🏢", "text": "Perfil de empresa"},
            {"key": "numeracion", "icon": "#",  "text": "Numeración"},
            {"key": "apariencia", "icon": "☀",  "text": "Apariencia"},
        ],
    },
    {
        "label": "Integraciones",
        "items": [
            {"key": "gmail", "icon": "@",  "text": "Gmail",
             "badge_text": "Conectado", "badge_state": "ok"},
            {"key": "groq",  "icon": "✦", "text": "IA · Groq",
             "badge_text": "Conf.",     "badge_state": "warn"},
        ],
    },
    {
        "label": "Documentos",
        "items": [
            {"key": "plantillas", "icon": "☰", "text": "Plantillas",
             "badge_text": "0", "badge_state": "off"},
        ],
    },
    {
        "label": "Datos",
        "items": [
            {"key": "backup", "icon": "💾", "text": "Backup"},
        ],
    },
]


class SidebarWidget(QWidget):
    """Left sidebar (230 px): grouped nav items for each settings section."""

    tile_selected = Signal(str)  # emits section key (API-compatible with old TilesPanel)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.sidebar())
        self.setFixedWidth(230)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 16, 10, 16)
        layout.setSpacing(2)

        self._items: dict[str, NavItem] = {}

        for section in _SECTIONS:
            group_lbl = QLabel(section["label"].upper())
            group_lbl.setStyleSheet(S.nav_group_label())
            group_lbl.setContentsMargins(12, 12, 12, 6)
            layout.addWidget(group_lbl)

            for item_def in section["items"]:
                item = NavItem(
                    key=item_def["key"],
                    icon=item_def["icon"],
                    text=item_def["text"],
                    badge_text=item_def.get("badge_text", ""),
                    badge_state=item_def.get("badge_state", ""),
                )
                item.clicked.connect(self._on_item_clicked)
                layout.addWidget(item)
                self._items[item_def["key"]] = item

        layout.addStretch()

        first_key = _SECTIONS[0]["items"][0]["key"]
        self.set_active_tile(first_key)

    # ── Public (API matches old TilesPanel) ───────────────────────────

    def set_active_tile(self, key: str) -> None:
        for k, item in self._items.items():
            item.set_active(k == key)

    def update_tile_status(self, key: str, text: str, state: str) -> None:
        if key in self._items:
            self._items[key].set_badge(text, state)

    # ── Internal ──────────────────────────────────────────────────────

    def _on_item_clicked(self, key: str) -> None:
        self.set_active_tile(key)
        self.tile_selected.emit(key)
