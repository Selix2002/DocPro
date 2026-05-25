from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from docpro_frontend.clients.widgets.client_card import ClientCard

_COLUMNS = 3


class ClientsGrid(QWidget):
    new_document_requested = Signal(int)        # client_id
    delete_requested       = Signal(int, str)   # client_id, client_name
    edit_requested         = Signal(int, dict)  # client_id, row_data

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._loading_label = QLabel("Cargando…")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setStyleSheet(
            "font-size: 18px; color: #9CA3AF; padding: 30px; background: transparent;"
        )
        self._loading_label.hide()
        outer.addWidget(self._loading_label)

        self._container = QWidget()
        self._container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._container.setStyleSheet("background: transparent;")
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(18)
        outer.addWidget(self._container)

    def set_loading(self, loading: bool) -> None:
        self._loading_label.setVisible(loading)
        self._container.setVisible(not loading)

    def set_rows(self, rows: list[dict]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, row in enumerate(rows):
            card = ClientCard()
            card.set_data(row)
            card.new_doc_clicked.connect(self.new_document_requested)
            card.delete_requested.connect(self.delete_requested)
            card.edit_requested.connect(self.edit_requested)
            self._grid.addWidget(card, i // _COLUMNS, i % _COLUMNS)
