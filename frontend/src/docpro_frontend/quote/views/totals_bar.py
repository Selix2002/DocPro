from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from docpro_frontend.quote.styles import quote_styles as S


def _fmt_clp(value: float) -> str:
    return f"$ {int(round(value)):,}".replace(",", ".")


class TotalsBar(QWidget):
    """Read-only totals display: Neto / IVA / Total. Updated via update_totals()."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TotalsBlock")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.totals_block())

        outer = QHBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.addStretch()

        table = QVBoxLayout()
        table.setSpacing(4)

        self._neto_row   = self._make_row("Neto",      S.totals_label, S.totals_value)
        self._iva_row    = self._make_row("IVA (19%)", S.totals_label, S.totals_value)
        self._total_row  = self._make_row("Total",     S.totals_total_label, S.totals_total_value)

        for row in (self._neto_row, self._iva_row, self._total_row):
            table.addLayout(row["layout"])

        outer.addLayout(table)

        self.update_totals(0.0, 0.0, 0.0)

    # ── Public ────────────────────────────────────────────────────────────────

    def update_totals(self, neto: float, iva: float, total: float) -> None:
        self._neto_row["value"].setText(_fmt_clp(neto))
        self._iva_row["value"].setText(_fmt_clp(iva))
        self._total_row["value"].setText(_fmt_clp(total))

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_row(label_text: str, label_style_fn, value_style_fn) -> dict:
        row = QHBoxLayout()
        row.setSpacing(0)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(label_style_fn())
        lbl.setFixedWidth(100)

        val = QLabel("$ 0")
        val.setStyleSheet(value_style_fn())
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val.setFixedWidth(160)

        row.addWidget(lbl)
        row.addWidget(val)

        return {"layout": row, "value": val}
