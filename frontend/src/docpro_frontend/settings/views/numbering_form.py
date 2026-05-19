from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.widgets.counter_row import CounterRow


class NumberingForm(QWidget):
    """Form block: Numeración — prefix and counter for quotes and reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("NUMERACIÓN DE DOCUMENTOS")
        title.setStyleSheet(S.d_section_title())
        layout.addWidget(title)

        self._quotes = CounterRow("Cotizaciones", "COT-", 1)
        self._reports = CounterRow("Informes técnicos", "IT-", 1)

        layout.addWidget(self._quotes)
        layout.addWidget(self._reports)

    # ── Public ────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        return {
            "quote_prefix":  self._quotes.get_prefix(),
            "quote_number":  self._quotes.get_number(),
            "report_prefix": self._reports.get_prefix(),
            "report_number": self._reports.get_number(),
        }

    def set_data(
        self,
        quote_prefix: str,
        quote_number: int,
        report_prefix: str,
        report_number: int,
    ) -> None:
        self._quotes.set_values(quote_prefix, quote_number)
        self._reports.set_values(report_prefix, report_number)
