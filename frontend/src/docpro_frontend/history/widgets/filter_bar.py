from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
)
from PySide6.QtCore import Signal, Qt, QTimer

from docpro_frontend.history.styles.history_styles import (
    FILTER_CHIP_ACTIVE, FILTER_CHIP_NORMAL, PAGE_SIZE_COMBO, SEARCH_BOX, SORT_COMBO,
)

_TYPE_OPTIONS   = [("Todos", None), ("Cotizaciones", "quote"), ("Informes", "report")]
_STATUS_OPTIONS = [
    ("Todos",      None),
    ("Finalizado", "Finalizado"),
    ("Enviado",    "Enviado"),
    ("Aprobado",   "Aprobado"),
    ("Rechazado",  "Rechazado"),
    ("Borrador",   "Borrador"),
]
_SORT_OPTIONS  = ["Más reciente", "Más antiguo", "A-Z"]
_PAGE_SIZES    = ["5", "10", "20", "40"]


class FilterBar(QWidget):
    filter_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._type_filter:   str | None = None
        self._status_filter: str | None = None
        self._sort      = "Más reciente"
        self._page_size = 5

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._emit)

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(12)

        # ── Row 1: search · sort · page-size ──────────────────────────────
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(10)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar por número, cliente…")
        self._search.setStyleSheet(SEARCH_BOX)
        self._search.textChanged.connect(lambda: self._debounce.start(300))
        row1.addWidget(self._search, stretch=1)

        self._sort_combo = QComboBox()
        self._sort_combo.addItems(_SORT_OPTIONS)
        self._sort_combo.setStyleSheet(SORT_COMBO)
        self._sort_combo.currentTextChanged.connect(self._on_sort_changed)
        row1.addWidget(self._sort_combo)

        page_size_lbl = QLabel("Filas:")
        page_size_lbl.setStyleSheet(
            "font-size: 17px; color: #6B7280; background: transparent;"
        )
        row1.addWidget(page_size_lbl)

        self._page_size_combo = QComboBox()
        self._page_size_combo.addItems(_PAGE_SIZES)
        self._page_size_combo.setStyleSheet(PAGE_SIZE_COMBO)
        self._page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        row1.addWidget(self._page_size_combo)

        main.addLayout(row1)

        # ── Row 2: type chips · status chips ──────────────────────────────
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(8)

        self._type_btns:   dict[str | None, QPushButton] = {}
        self._status_btns: dict[str | None, QPushButton] = {}

        for label, value in _TYPE_OPTIONS:
            btn = self._chip(label, value == self._type_filter)
            btn.clicked.connect(lambda _, v=value: self._on_type_click(v))
            self._type_btns[value] = btn
            row2.addWidget(btn)

        row2.addSpacing(24)

        for label, value in _STATUS_OPTIONS:
            btn = self._chip(label, value == self._status_filter)
            btn.clicked.connect(lambda _, v=value: self._on_status_click(v))
            self._status_btns[value] = btn
            row2.addWidget(btn)

        row2.addStretch()
        main.addLayout(row2)

    # ── public ────────────────────────────────────────────────────────────

    def get_params(self) -> dict:
        return {
            "search":        self._search.text().strip(),
            "type_filter":   self._type_filter,
            "status_filter": self._status_filter,
            "sort":          self._sort,
            "page_size":     self._page_size,
        }

    # ── private ───────────────────────────────────────────────────────────

    @staticmethod
    def _chip(label: str, active: bool) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(FILTER_CHIP_ACTIVE if active else FILTER_CHIP_NORMAL)
        return btn

    def _on_type_click(self, value: str | None) -> None:
        self._type_filter = value
        for v, btn in self._type_btns.items():
            btn.setStyleSheet(FILTER_CHIP_ACTIVE if v == value else FILTER_CHIP_NORMAL)
        self._emit()

    def _on_status_click(self, value: str | None) -> None:
        self._status_filter = value
        for v, btn in self._status_btns.items():
            btn.setStyleSheet(FILTER_CHIP_ACTIVE if v == value else FILTER_CHIP_NORMAL)
        self._emit()

    def _on_sort_changed(self, text: str) -> None:
        self._sort = text
        self._emit()

    def _on_page_size_changed(self, text: str) -> None:
        try:
            self._page_size = int(text)
        except ValueError:
            self._page_size = 5
        self._emit()

    def _emit(self) -> None:
        self.filter_changed.emit(self.get_params())
