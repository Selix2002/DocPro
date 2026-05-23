from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Signal, Qt

from docpro_frontend.history.styles.history_styles import TABLE_PANEL
from docpro_frontend.history.widgets.history_row import HistoryRow

_HEADER_LABEL = (
    "font-size: 15px; font-weight: 600; letter-spacing: 1px; "
    "color: #6B7280; background: transparent;"
)


class HistoryTable(QWidget):
    row_clicked = Signal(int, str)  # doc_id, doc_type

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._panel = QFrame()
        self._panel.setObjectName("HistoryPanel")
        self._panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._panel.setStyleSheet(TABLE_PANEL)
        panel_v = QVBoxLayout(self._panel)
        panel_v.setContentsMargins(0, 0, 0, 0)
        panel_v.setSpacing(0)

        panel_v.addWidget(self._build_header())

        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(0)
        panel_v.addWidget(self._body)

        self._loading_label = QLabel("Cargando…")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setStyleSheet(
            "font-size: 18px; color: #9CA3AF; padding: 30px; background: transparent;"
        )
        self._loading_label.hide()
        panel_v.addWidget(self._loading_label)

        outer.addWidget(self._panel)

    @staticmethod
    def _build_header() -> QWidget:
        header = QWidget()
        header.setObjectName("TableHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setStyleSheet(
            "QWidget#TableHeader { background: #F9FAFB; border-bottom: 1px solid #E5E7EB; }"
        )
        layout = QHBoxLayout(header)
        layout.setContentsMargins(21, 12, 21, 12)
        layout.setSpacing(0)

        def _h(text: str, width: int = 0) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(_HEADER_LABEL)
            if width:
                lbl.setFixedWidth(width)
            return lbl

        layout.addWidget(_h("DOCUMENTO", 120))
        layout.addWidget(_h("TIPO", 180))
        layout.addWidget(_h("CLIENTE"), 1)   # stretch=1
        layout.addWidget(_h("ESTADO", 120))
        layout.addSpacing(20)
        layout.addWidget(_h("FECHA", 160))
        layout.addWidget(_h("", 36))         # aligns with action button
        return header

    def set_loading(self, loading: bool) -> None:
        self._body.setVisible(not loading)
        self._loading_label.setVisible(loading)

    def set_rows(self, rows: list[dict]) -> None:
        while self._body_layout.count():
            item = self._body_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        last = len(rows) - 1
        for i, data in enumerate(rows):
            row = HistoryRow(
                doc_id=data["doc_id"],
                number=data["number"],
                doc_type=data["doc_type"],
                client_name=data["client_name"],
                status=data["status"],
                date_label=data["date_label"],
                is_last=(i == last),
            )
            row.row_clicked.connect(self.row_clicked)
            self._body_layout.addWidget(row)
