from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Signal

from docpro_frontend.body.widgets.create_card import CreateCard


class CreateSection(QWidget):
    create_quote_requested = Signal()
    create_report_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("CREAR NUEVO")
        title.setStyleSheet(
            "font-size: 15px; font-weight: 600; letter-spacing: 1px; color: #374151;"
        )
        layout.addWidget(title)
        layout.addSpacing(15)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(15)

        self._card_quote = CreateCard(
            label="Cotización",
            next_label="—",
            color="amber",
        )
        self._card_report = CreateCard(
            label="Informe técnico",
            next_label="—",
            color="blue",
        )

        cards_row.addWidget(self._card_quote)
        cards_row.addWidget(self._card_report)
        layout.addLayout(cards_row)

        self._card_quote.clicked.connect(self.create_quote_requested)
        self._card_report.clicked.connect(self.create_report_requested)

    def set_next_numbers(self, next_quote: str, next_report: str) -> None:
        self._card_quote.set_next_label(f"Próxima: {next_quote}")
        self._card_report.set_next_label(f"Próximo: {next_report}")
