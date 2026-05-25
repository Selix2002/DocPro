from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel

from docpro_frontend.body.widgets.stat_card import StatCard


class TotalsSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("TOTALES")
        title.setStyleSheet(
            "font-size: 15px; font-weight: 600; letter-spacing: 1px; color: #374151;"
        )
        layout.addWidget(title)
        layout.addSpacing(15)

        grid = QGridLayout()
        grid.setSpacing(12)

        self._cards = {
            "cotizaciones": StatCard("Cotizaciones", "—", "amber"),
            "informes":     StatCard("Informes",     "—", "blue"),
            "clientes":     StatCard("Clientes",     "—"),
            "docs_total":   StatCard("Docs total",   "—"),
        }

        for i, (key, card) in enumerate(self._cards.items()):
            row, col = divmod(i, 2)
            grid.addWidget(card, row, col)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        layout.addLayout(grid)

    def set_data(
        self,
        cotizaciones: int,
        informes: int,
        clientes: int,
        docs_total: int,
    ) -> None:
        self._cards["cotizaciones"].set_value(str(cotizaciones))
        self._cards["informes"].set_value(str(informes))
        self._cards["clientes"].set_value(str(clientes))
        self._cards["docs_total"].set_value(str(docs_total))
