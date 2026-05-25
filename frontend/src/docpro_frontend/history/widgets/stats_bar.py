from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from docpro_frontend.history.styles.history_styles import STAT_CARD


class StatsBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self._total_val    = QLabel("—")
        self._week_val     = QLabel("—")
        self._approved_val = QLabel("—")

        layout.addWidget(_build_card("Documentos procesados",   self._total_val,    "#B45309"))
        layout.addWidget(_build_card("Completados esta semana", self._week_val,     "#065F46"))
        layout.addWidget(_build_card("Cotizaciones aprobadas",  self._approved_val, "#047857"))
        layout.addStretch()

    def set_stats(self, total: int, week: int, approved: int = 0) -> None:
        self._total_val.setText(str(total))
        self._week_val.setText(str(week))
        self._approved_val.setText(str(approved))


def _build_card(title: str, value_lbl: QLabel, color: str) -> QFrame:
    card = QFrame()
    card.setObjectName("HistStatCard")
    card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    card.setStyleSheet(STAT_CARD)
    card.setFixedWidth(270)

    layout = QVBoxLayout(card)
    layout.setContentsMargins(24, 18, 24, 18)
    layout.setSpacing(6)

    title_lbl = QLabel(title)
    title_lbl.setStyleSheet("font-size: 16px; color: #6B7280; background: transparent;")
    value_lbl.setStyleSheet(
        f"font-size: 36px; font-weight: 700; color: {color}; background: transparent;"
    )

    layout.addWidget(title_lbl)
    layout.addWidget(value_lbl)
    return card
