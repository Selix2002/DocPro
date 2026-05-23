from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QComboBox
from PySide6.QtCore import Signal, Qt, QTimer

from docpro_frontend.clients.styles.clients_styles import (
    SEARCH_BOX, SORT_COMBO, VIEW_TOGGLE_ACTIVE, VIEW_TOGGLE_NORMAL,
)

_SORT_OPTIONS = ["Más reciente", "Nombre (A-Z)", "Más documentos"]


class ClientsFilterBar(QWidget):
    filter_changed = Signal(dict)  # keys: search, sort
    view_changed   = Signal(str)   # "grid" | "list"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sort = "Más reciente"
        self._view = "grid"

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._emit_filter)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar cliente por nombre, RUT, email…")
        self._search.setStyleSheet(SEARCH_BOX)
        self._search.textChanged.connect(lambda: self._debounce.start(300))
        layout.addWidget(self._search, stretch=1)

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(_SORT_OPTIONS)
        self._sort_combo.setStyleSheet(SORT_COMBO)
        self._sort_combo.currentTextChanged.connect(self._on_sort_changed)
        layout.addWidget(self._sort_combo)

        toggle_container = QWidget()
        toggle_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        toggle_container.setStyleSheet("background: transparent;")
        toggle_h = QHBoxLayout(toggle_container)
        toggle_h.setContentsMargins(0, 0, 0, 0)
        toggle_h.setSpacing(4)

        self._grid_btn = QPushButton("⊞ Grid")
        self._grid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._grid_btn.setStyleSheet(VIEW_TOGGLE_ACTIVE)
        self._grid_btn.clicked.connect(lambda: self._on_view_click("grid"))
        toggle_h.addWidget(self._grid_btn)

        self._list_btn = QPushButton("≡ Lista")
        self._list_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._list_btn.setStyleSheet(VIEW_TOGGLE_NORMAL)
        self._list_btn.clicked.connect(lambda: self._on_view_click("list"))
        toggle_h.addWidget(self._list_btn)

        layout.addWidget(toggle_container)

    # ── public ────────────────────────────────────────────────────────────

    def get_params(self) -> dict:
        return {
            "search": self._search.text().strip(),
            "sort":   self._sort,
        }

    # ── private ───────────────────────────────────────────────────────────

    def _on_sort_changed(self, text: str) -> None:
        self._sort = text
        self._emit_filter()

    def _on_view_click(self, view: str) -> None:
        if view == self._view:
            return
        self._view = view
        self._grid_btn.setStyleSheet(VIEW_TOGGLE_ACTIVE if view == "grid" else VIEW_TOGGLE_NORMAL)
        self._list_btn.setStyleSheet(VIEW_TOGGLE_ACTIVE if view == "list" else VIEW_TOGGLE_NORMAL)
        self.view_changed.emit(view)

    def _emit_filter(self) -> None:
        self.filter_changed.emit(self.get_params())
