from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget,
)
from PySide6.QtCore import Signal, Qt

from docpro_frontend.clients.styles.clients_styles import NEW_CLIENT_BTN
from docpro_frontend.clients.widgets.filter_bar import ClientsFilterBar
from docpro_frontend.clients.widgets.clients_grid import ClientsGrid
from docpro_frontend.clients.widgets.clients_table import ClientsTable
from docpro_frontend.clients.widgets.pagination_bar import ClientsPaginationBar
from docpro_frontend.clients.widgets.stats_bar import ClientsStatsBar

_IDX_GRID  = 0
_IDX_TABLE = 1


class ClientsWidget(QWidget):
    new_document_requested = Signal(int)   # client_id — stub for Phase 6
    new_client_requested   = Signal()      # stub for Phase 6
    filter_changed         = Signal(dict)  # keys: search, sort, page_size
    page_changed           = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._page_size = 12  # grid default

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("ClientsContent")
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content.setStyleSheet("QWidget#ClientsContent { background: #F9FAFB; }")
        scroll.setWidget(content)

        inner = QVBoxLayout(content)
        inner.setContentsMargins(36, 36, 36, 36)
        inner.setSpacing(0)

        # ── Page header ───────────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(0)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title_col.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Clientes")
        title.setStyleSheet(
            "font-size: 32px; font-weight: 700; color: #111827; background: transparent;"
        )
        subtitle = QLabel("Directorio de clientes y su actividad")
        subtitle.setStyleSheet(
            "font-size: 18px; color: #9CA3AF; background: transparent;"
        )
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        new_btn = QPushButton("+ Nuevo cliente")
        new_btn.setStyleSheet(NEW_CLIENT_BTN)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self.new_client_requested)

        header_row.addLayout(title_col, stretch=1)
        header_row.addWidget(new_btn, alignment=Qt.AlignmentFlag.AlignBottom)

        inner.addLayout(header_row)
        inner.addSpacing(28)

        # ── Stats bar ─────────────────────────────────────────────────────
        self._stats = ClientsStatsBar()
        inner.addWidget(self._stats)
        inner.addSpacing(24)

        # ── Filter bar ────────────────────────────────────────────────────
        self._filter_bar = ClientsFilterBar()
        self._filter_bar.filter_changed.connect(self._on_filter_changed)
        self._filter_bar.view_changed.connect(self._on_view_changed)
        inner.addWidget(self._filter_bar)
        inner.addSpacing(18)

        # ── Content stack ─────────────────────────────────────────────────
        self._stack = QStackedWidget()
        self._grid  = ClientsGrid()
        self._table = ClientsTable()
        self._stack.addWidget(self._grid)   # _IDX_GRID
        self._stack.addWidget(self._table)  # _IDX_TABLE
        self._grid.new_document_requested.connect(self.new_document_requested)
        self._table.new_document_requested.connect(self.new_document_requested)
        inner.addWidget(self._stack)
        inner.addSpacing(18)

        # ── Pagination ────────────────────────────────────────────────────
        self._pagination = ClientsPaginationBar()
        self._pagination.page_requested.connect(self.page_changed)
        inner.addWidget(self._pagination)
        inner.addStretch()

    # ── public ────────────────────────────────────────────────────────────

    def set_loading(self, loading: bool) -> None:
        self._grid.set_loading(loading)
        self._table.set_loading(loading)

    def set_data(self, data: dict) -> None:
        self._stats.set_stats(
            data["total_clients"],
            data["new_this_month"],
            data["total_docs"],
            data["potential_income"],
        )
        self._grid.set_rows(data["rows"])
        self._table.set_rows(data["rows"])
        self._pagination.set_state(data["current_page"], data["total_pages"])
        self.set_loading(False)

    # ── private ───────────────────────────────────────────────────────────

    def _on_filter_changed(self, params: dict) -> None:
        params["page_size"] = self._page_size
        self.filter_changed.emit(params)

    def _on_view_changed(self, view: str) -> None:
        if view == "grid":
            self._stack.setCurrentIndex(_IDX_GRID)
            self._page_size = 12
        else:
            self._stack.setCurrentIndex(_IDX_TABLE)
            self._page_size = 15
        params = self._filter_bar.get_params()
        params["page_size"] = self._page_size
        self.filter_changed.emit(params)
