from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QAbstractItemView, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from docpro_frontend.quote.styles import quote_styles as S
from docpro_frontend.quote.views.totals_bar import TotalsBar

_COL_QTY   = 0
_COL_DESC  = 1
_COL_PRICE = 2
_COL_SUB   = 3
_COL_DEL   = 4

_HEADERS = ["Cantidad", "Descripción", "Valor unitario", "Subtotal", ""]


def _fmt_clp(value: float) -> str:
    return f"$ {int(round(value)):,}".replace(",", ".")


def _parse_float(text: str) -> float:
    clean = text.replace("$", "").replace(".", "").replace(",", ".").strip()
    try:
        return max(0.0, float(clean))
    except ValueError:
        return 0.0


class ItemsTable(QWidget):
    """
    Line-items table + totals bar.
    Signals:
        totals_changed(neto, iva, total) — fires on any qty/price change
        data_changed                     — fires on any cell or row change
    """

    totals_changed = Signal(float, float, float)
    data_changed   = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(_HEADERS)
        self._table.setStyleSheet(S.items_table())
        self._table.setShowGrid(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table.horizontalHeader().setHighlightSections(False)
        self._table.horizontalHeader().setSectionResizeMode(_COL_QTY,   QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(_COL_DESC,  QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(_COL_PRICE, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(_COL_SUB,   QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(_COL_DEL,   QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(_COL_QTY,   90)
        self._table.setColumnWidth(_COL_PRICE, 140)
        self._table.setColumnWidth(_COL_SUB,   130)
        self._table.setColumnWidth(_COL_DEL,   44)
        self._table.setMinimumHeight(40)

        layout.addWidget(self._table)

        self._add_btn = QPushButton("＋  Agregar ítem")
        self._add_btn.setStyleSheet(S.add_row_btn())
        self._add_btn.clicked.connect(self._append_empty_row)
        layout.addWidget(self._add_btn)

        self._totals = TotalsBar()
        layout.addWidget(self._totals)

        self._readonly = False

    # ── Public API ────────────────────────────────────────────────────────────

    def get_data(self) -> list[dict]:
        rows = []
        for r in range(self._table.rowCount()):
            qty_w   = self._table.cellWidget(r, _COL_QTY)
            desc_w  = self._table.cellWidget(r, _COL_DESC)
            price_w = self._table.cellWidget(r, _COL_PRICE)
            if qty_w is None or desc_w is None or price_w is None:
                continue
            qty   = _parse_float(qty_w.text())
            price = _parse_float(price_w.text())
            rows.append({
                "position":    r + 1,
                "quantity":    qty,
                "description": desc_w.text().strip(),
                "unit_price":  price,
            })
        return rows

    def set_data(self, items: list[dict]) -> None:
        self._table.setRowCount(0)
        for item in items:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._insert_row_widgets(row)
            qty_w   = self._table.cellWidget(row, _COL_QTY)
            desc_w  = self._table.cellWidget(row, _COL_DESC)
            price_w = self._table.cellWidget(row, _COL_PRICE)
            qty_w.setText(str(int(item["quantity"]) if item["quantity"] == int(item["quantity"]) else item["quantity"]))
            desc_w.setText(item.get("description", ""))
            price_w.setText(str(int(item["unit_price"]) if item["unit_price"] == int(item["unit_price"]) else item["unit_price"]))
            sub = item.get("subtotal", round(item["quantity"] * item["unit_price"], 2))
            self._set_subtotal(row, sub)
        self._adjust_height()
        self._recalc_totals()

    def set_show_iva(self, show_iva: bool) -> None:
        self._totals.set_show_iva(show_iva)

    def set_readonly(self, readonly: bool) -> None:
        self._readonly = readonly
        self._add_btn.setEnabled(not readonly)
        for r in range(self._table.rowCount()):
            for col in (_COL_QTY, _COL_DESC, _COL_PRICE):
                w = self._table.cellWidget(r, col)
                if w:
                    w.setReadOnly(readonly)
            del_btn = self._table.cellWidget(r, _COL_DEL)
            if del_btn:
                del_btn.setEnabled(not readonly)

    def clear(self) -> None:
        self._table.setRowCount(0)
        self._adjust_height()
        self._recalc_totals()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _append_empty_row(self) -> None:
        row = self._table.rowCount()
        self._table.insertRow(row)
        self._insert_row_widgets(row)
        self._set_subtotal(row, 0.0)
        self._adjust_height()
        qty_w = self._table.cellWidget(row, _COL_QTY)
        if qty_w:
            qty_w.setFocus()
        self.data_changed.emit()

    def _insert_row_widgets(self, row: int) -> None:
        self._table.setRowHeight(row, 44)

        qty_input = QLineEdit()
        qty_input.setPlaceholderText("1")
        qty_input.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        qty_input.setStyleSheet(S.item_cell_input())
        qty_input.textChanged.connect(lambda _, r=row: self._on_qty_or_price_changed(r))
        self._table.setCellWidget(row, _COL_QTY, qty_input)

        desc_input = QLineEdit()
        desc_input.setPlaceholderText("Descripción del ítem…")
        desc_input.setStyleSheet(S.item_cell_input())
        desc_input.textChanged.connect(self.data_changed)
        self._table.setCellWidget(row, _COL_DESC, desc_input)

        price_input = QLineEdit()
        price_input.setPlaceholderText("0")
        price_input.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price_input.setStyleSheet(S.item_cell_input())
        price_input.textChanged.connect(lambda _, r=row: self._on_qty_or_price_changed(r))
        self._table.setCellWidget(row, _COL_PRICE, price_input)

        sub_item = QTableWidgetItem("$ 0")
        sub_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        sub_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self._table.setItem(row, _COL_SUB, sub_item)

        del_btn = QPushButton("×")
        del_btn.setStyleSheet(S.item_del_btn())
        del_btn.clicked.connect(lambda _, r=row: self._remove_row(r))
        self._table.setCellWidget(row, _COL_DEL, del_btn)

    def _remove_row(self, row: int) -> None:
        if self._readonly:
            return
        self._table.removeRow(row)
        self._rewire_delete_buttons()
        self._adjust_height()
        self._recalc_totals()
        self.data_changed.emit()

    def _rewire_delete_buttons(self) -> None:
        for r in range(self._table.rowCount()):
            del_btn = self._table.cellWidget(r, _COL_DEL)
            if del_btn:
                try:
                    del_btn.clicked.disconnect()
                except RuntimeError:
                    pass
                del_btn.clicked.connect(lambda _, row=r: self._remove_row(row))

    def _on_qty_or_price_changed(self, row: int) -> None:
        qty_w   = self._table.cellWidget(row, _COL_QTY)
        price_w = self._table.cellWidget(row, _COL_PRICE)
        if qty_w is None or price_w is None:
            return
        qty   = _parse_float(qty_w.text())
        price = _parse_float(price_w.text())
        subtotal = round(qty * price, 2)
        self._set_subtotal(row, subtotal)
        self._recalc_totals()
        self.data_changed.emit()

    def _set_subtotal(self, row: int, value: float) -> None:
        item = self._table.item(row, _COL_SUB)
        if item is None:
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, _COL_SUB, item)
        item.setText(_fmt_clp(value))

    def _recalc_totals(self) -> None:
        neto = 0.0
        for r in range(self._table.rowCount()):
            qty_w   = self._table.cellWidget(r, _COL_QTY)
            price_w = self._table.cellWidget(r, _COL_PRICE)
            if qty_w and price_w:
                neto += round(_parse_float(qty_w.text()) * _parse_float(price_w.text()), 2)
        neto  = round(neto, 2)
        iva   = round(neto * 0.19, 2)
        total = round(neto + iva, 2)
        self._totals.update_totals(neto, iva, total)
        self.totals_changed.emit(neto, iva, total)

    def _adjust_height(self) -> None:
        rows = self._table.rowCount()
        header_h = self._table.horizontalHeader().height()
        row_h = 44
        self._table.setFixedHeight(header_h + rows * row_h + 2)
