from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt

from docpro_frontend.clients.styles.clients_styles import STAT_CARD


class ClientsStatsBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self._total_val  = QLabel("—")
        self._new_val    = QLabel("—")
        self._docs_val   = QLabel("—")
        self._income_val = QLabel("—")

        layout.addWidget(_build_card("Total de clientes",    self._total_val,  "#B45309"))
        layout.addWidget(_build_card("Nuevos este mes",      self._new_val,    "#059669"))
        layout.addWidget(_build_card("Documentos generados", self._docs_val,   "#1D4ED8"))
        layout.addWidget(_build_card("Ingresos totales",     self._income_val, "#B45309"))
        layout.addStretch()

    def set_stats(
        self,
        total_clients: int,
        new_this_month: int,
        total_docs: int,
        potential_income: float,
    ) -> None:
        self._total_val.setText(str(total_clients))
        self._new_val.setText(str(new_this_month))
        self._docs_val.setText(str(total_docs))
        formatted = f"{int(potential_income):,}".replace(",", ".")
        self._income_val.setText(f"${formatted}")


def _build_card(title: str, value_lbl: QLabel, color: str) -> QFrame:
    card = QFrame()
    card.setObjectName("ClientStatCard")
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
