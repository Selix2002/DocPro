from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from docpro_frontend.header.views.menu_bar import MenuBar
from docpro_frontend.header.views.toolbar import Toolbar


class HeaderWidget(QWidget):
    tab_changed = Signal(str)
    new_quote_requested = Signal()
    new_report_requested = Signal()
    import_pdf_requested = Signal()
    settings_requested = Signal()
    search_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._menu_bar = MenuBar()
        self._toolbar = Toolbar()

        layout.addWidget(self._menu_bar)
        layout.addWidget(self._toolbar)

        self._menu_bar.tab_changed.connect(self.tab_changed)
        self._menu_bar.new_quote_requested.connect(self.new_quote_requested)
        self._menu_bar.new_report_requested.connect(self.new_report_requested)
        self._menu_bar.import_pdf_requested.connect(self.import_pdf_requested)
        self._menu_bar.settings_requested.connect(self.settings_requested)
        self._toolbar.search_changed.connect(self.search_changed)
