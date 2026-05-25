from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from docpro_frontend.body.styles.body_styles import SUMMARY_CARD

_ROWS = [
    ("Cotizaciones emitidas", "cotizaciones", "—"),
    ("Informes emitidos",     "informes",     "—"),
    ("Clientes activos",      "clientes",     "—"),
    ("PDFs exportados",       "pdfs",         "—"),
]


class MonthSummarySection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("RESUMEN DEL MES")
        title.setStyleSheet(
            "font-size: 15px; font-weight: 600; letter-spacing: 1px; color: #374151;"
        )
        layout.addWidget(title)
        layout.addSpacing(15)

        card = QFrame()
        card.setObjectName("SummaryCard")
        card.setStyleSheet(SUMMARY_CARD)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self._values: dict[str, QLabel] = {}
        for i, (display, key, default) in enumerate(_ROWS):
            row = QWidget()
            row_h = QHBoxLayout(row)
            row_h.setContentsMargins(21, 15, 21, 15)
            row_h.setSpacing(0)

            lbl = QLabel(display)
            lbl.setStyleSheet(
                "font-size: 18px; color: #6B7280; border: none; background: transparent;"
            )

            val = QLabel(default)
            val.setStyleSheet(
                "font-size: 21px; font-weight: 600; color: #111827; "
                "border: none; background: transparent;"
            )
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            row_h.addWidget(lbl)
            row_h.addWidget(val)
            self._values[key] = val
            card_layout.addWidget(row)

            if i < len(_ROWS) - 1:
                sep = QWidget()
                sep.setFixedHeight(1)
                sep.setStyleSheet("background: #F3F4F6;")
                sep.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                card_layout.addWidget(sep)

        layout.addWidget(card)

    def set_data(self, data: dict) -> None:
        for key, label in self._values.items():
            if key in data:
                label.setText(str(data[key]))
