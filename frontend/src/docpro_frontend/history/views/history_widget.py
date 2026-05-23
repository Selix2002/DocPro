from PySide6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt

from docpro_frontend.history.widgets.filter_bar import FilterBar
from docpro_frontend.history.widgets.history_table import HistoryTable
from docpro_frontend.history.widgets.pagination_bar import PaginationBar
from docpro_frontend.history.widgets.stats_bar import StatsBar


class HistoryWidget(QWidget):
    filter_changed  = Signal(dict)   # forwarded to DashboardWidget
    page_changed    = Signal(int)    # forwarded to DashboardWidget
    document_opened = Signal(int, str)  # doc_id, doc_type

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("HistoryContent")
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content.setStyleSheet("QWidget#HistoryContent { background: #FAFAFA; }")
        scroll.setWidget(content)

        inner = QVBoxLayout(content)
        inner.setContentsMargins(36, 36, 36, 36)
        inner.setSpacing(0)

        title = QLabel("Historial")
        title.setStyleSheet(
            "font-size: 32px; font-weight: 700; color: #111827; background: transparent;"
        )
        subtitle = QLabel("Registro de todos los documentos procesados")
        subtitle.setStyleSheet(
            "font-size: 18px; color: #9CA3AF; background: transparent;"
        )
        inner.addWidget(title)
        inner.addSpacing(4)
        inner.addWidget(subtitle)
        inner.addSpacing(28)

        self._stats = StatsBar()
        inner.addWidget(self._stats)
        inner.addSpacing(24)

        self._filter_bar = FilterBar()
        self._filter_bar.filter_changed.connect(self.filter_changed)
        inner.addWidget(self._filter_bar)
        inner.addSpacing(18)

        self._table = HistoryTable()
        self._table.row_clicked.connect(self.document_opened)
        inner.addWidget(self._table)
        inner.addSpacing(18)

        self._pagination = PaginationBar()
        self._pagination.page_requested.connect(self.page_changed)
        inner.addWidget(self._pagination)
        inner.addStretch()

    def set_loading(self, loading: bool) -> None:
        self._table.set_loading(loading)

    def get_filter_params(self) -> dict:
        return self._filter_bar.get_params()

    def set_data(self, data: dict) -> None:
        self._stats.set_stats(data["total_docs"], data["completed_this_week"], data["approved_count"])
        self._table.set_rows(data["rows"])
        self._pagination.set_state(data["current_page"], data["total_pages"])
        self._table.set_loading(False)
