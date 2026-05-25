from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit
from PySide6.QtCore import Signal, Qt

from docpro_frontend.header.styles.header_styles import TOOLBAR, TOOLBAR_BTN, TOOLBAR_SEARCH


class Toolbar(QWidget):
    search_changed  = Signal(str)
    filter_toggled  = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setObjectName("Toolbar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(TOOLBAR)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(36, 0, 36, 0)
        layout.setSpacing(12)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar documentos, clientes, RUT…")
        self._search.setStyleSheet(TOOLBAR_SEARCH)
        self._search.setMaximumWidth(540)
        self._search.textChanged.connect(self.search_changed)
        layout.addWidget(self._search)

        self._btn_filter = QPushButton("≡  Filtros")
        self._btn_filter.setStyleSheet(TOOLBAR_BTN)
        self._btn_filter.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_filter.setCheckable(True)
        self._btn_filter.clicked.connect(self.filter_toggled)
        layout.addWidget(self._btn_filter)

        layout.addStretch()

    @property
    def search_field(self):
        return self._search
