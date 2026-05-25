from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from docpro_frontend.clients.styles.clients_styles import TABLE_PANEL
from docpro_frontend.clients.widgets.clients_row import ClientsRow

_HEADER_LABEL = (
    "font-size: 15px; font-weight: 600; letter-spacing: 1px; "
    "color: #6B7280; background: transparent;"
)

# Width for the two action buttons (+ and ✕), each 36px with 4px spacing = 76px
_ACTIONS_W = 76


class ClientsTable(QWidget):
    new_document_requested = Signal(int)        # client_id
    delete_requested       = Signal(int, str)   # client_id, client_name
    edit_requested         = Signal(int, dict)  # client_id, row_data

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._panel = QFrame()
        self._panel.setObjectName("ClientsPanel")
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
        header.setObjectName("ClientsTableHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setStyleSheet(
            "QWidget#ClientsTableHeader { background: #F9FAFB; border-bottom: 1px solid #E5E7EB; }"
        )
        header.setFixedHeight(60)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(21, 0, 21, 0)
        layout.setSpacing(0)

        def _h(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(_HEADER_LABEL)
            return lbl

        layout.addWidget(_h("NOMBRE"), 2)

        rut_h = _h("RUT")
        rut_h.setFixedWidth(130)
        layout.addWidget(rut_h)

        layout.addWidget(_h("EMAIL"), 2)

        phone_h = _h("TELÉFONO")
        phone_h.setFixedWidth(130)
        layout.addWidget(phone_h)

        docs_h = _h("DOCS")
        docs_h.setFixedWidth(100)
        layout.addWidget(docs_h)

        spacer_h = _h("")
        spacer_h.setFixedWidth(_ACTIONS_W)
        layout.addWidget(spacer_h)

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
            row = ClientsRow(row=data, is_last=(i == last))
            row.new_doc_clicked.connect(self.new_document_requested)
            row.delete_requested.connect(self.delete_requested)
            row.edit_requested.connect(self.edit_requested)
            self._body_layout.addWidget(row)
