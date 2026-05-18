from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.header.styles.header_styles import BTN_GHOST, BTN_AMBER, BTN_BLUE, BTN_ICON


class ActionBar(QWidget):
    new_quote_requested = Signal()
    new_report_requested = Signal()
    import_pdf_requested = Signal()
    settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        btn_import = QPushButton("↑  Importar PDF")
        btn_import.setStyleSheet(BTN_GHOST)
        btn_import.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import.clicked.connect(self.import_pdf_requested)

        btn_quote = QPushButton("+  Nueva cotización")
        btn_quote.setStyleSheet(BTN_AMBER)
        btn_quote.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_quote.clicked.connect(self.new_quote_requested)

        btn_report = QPushButton("+  Nuevo informe")
        btn_report.setStyleSheet(BTN_BLUE)
        btn_report.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_report.clicked.connect(self.new_report_requested)

        btn_settings = QPushButton("⚙")
        btn_settings.setStyleSheet(BTN_ICON)
        btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_settings.clicked.connect(self.settings_requested)

        layout.addWidget(btn_import)
        layout.addWidget(btn_quote)
        layout.addWidget(btn_report)
        layout.addWidget(btn_settings)
