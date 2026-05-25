from PySide6.QtCore import (
    QEasingCurve, QEvent, QObject, QPoint, QRect, QVariantAnimation, Signal, Qt,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QVBoxLayout,
)

_ROW_H       = 58
_MAX_VISIBLE = 6
_V_PAD       = 8
_ANIM_MS     = 190

_TYPE = {
    "cot": ("COT", "#FEF3C7", "#92400E"),
    "inf": ("IT",  "#DBEAFE", "#1E40AF"),
}
_STATUS = {
    "Borrador":   ("#FEF3C7", "#92400E"),
    "Finalizado": ("#DBEAFE", "#1E40AF"),
    "Enviado":    ("#D1FAE5", "#065F46"),
}


class _Row(QFrame):
    activated = Signal()

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result
        self.setFixedHeight(_ROW_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._on = False
        self._build(result)
        self._repaint(False)

    def _build(self, r: dict) -> None:
        h = QHBoxLayout(self)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(12)

        type_text, type_bg, type_fg = _TYPE.get(r["doc_type"], ("DOC", "#F3F4F6", "#374151"))
        badge = QLabel(type_text)
        badge.setFixedSize(40, 24)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        badge.setStyleSheet(
            f"background:{type_bg};color:{type_fg};"
            "border-radius:6px;font-size:12px;font-weight:700;"
        )
        h.addWidget(badge)

        col = QVBoxLayout()
        col.setSpacing(1)
        col.setContentsMargins(0, 0, 0, 0)

        num = QLabel(r["number"])
        num.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        num.setStyleSheet(
            "font-size:16px;font-weight:600;color:#111827;background:transparent;"
        )
        client = QLabel(r["client_name"])
        client.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        client.setStyleSheet("font-size:14px;color:#6B7280;background:transparent;")
        col.addWidget(num)
        col.addWidget(client)
        h.addLayout(col, stretch=1)

        st_bg, st_fg = _STATUS.get(r["status"], ("#F3F4F6", "#374151"))
        status = QLabel(r["status"])
        status.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        status.setStyleSheet(
            f"background:{st_bg};color:{st_fg};"
            "border-radius:6px;padding:2px 8px;"
            "font-size:12px;font-weight:600;"
        )
        h.addWidget(status)

    def set_highlighted(self, on: bool) -> None:
        if self._on == on:
            return
        self._on = on
        self._repaint(on)

    def _repaint(self, on: bool) -> None:
        bg = "#F9FAFB" if on else "white"
        self.setStyleSheet(
            f"QFrame{{background:{bg};border-bottom:1px solid #F3F4F6;}}"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.activated.emit()
        super().mousePressEvent(event)


class SearchDropdown(QFrame):
    result_selected = Signal(int, str)  # doc_id, doc_type

    def __init__(self, main_win, search_field):
        super().__init__(main_win)
        self._main_win = main_win
        self._sf       = search_field
        self._rows: list[_Row] = []
        self._hi       = -1
        self._closing  = False

        self.setObjectName("SearchDropdown")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QFrame#SearchDropdown {
                background: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(shadow)

        self._body = QVBoxLayout(self)
        self._body.setContentsMargins(0, _V_PAD, 0, _V_PAD)
        self._body.setSpacing(0)

        # QVariantAnimation drives resize() directly — correct for floating widgets
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(_ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(lambda v: self.resize(self.width(), int(v)))
        self._on_closed_connected = False

        self.resize(0, 0)
        self.hide()

        # Key navigation on the search field
        search_field.installEventFilter(self)
        # Reposition on window move/resize
        main_win.installEventFilter(self)
        # Click-outside detection (replaces unreliable FocusOut approach)
        QApplication.instance().installEventFilter(self)

    # ── public API ────────────────────────────────────────────────────────

    def show_results(self, results: list) -> None:
        # Reset all state unconditionally — same code path every time
        self._closing = False
        self._hi = -1
        self._disconnect_on_closed()
        self._anim.stop()
        if not self.isHidden():
            self.hide()
        self._clear_rows()

        if not results:
            return

        for r in results:
            row = _Row(r)
            row.activated.connect(lambda rr=r: self._select(rr))
            self._rows.append(row)
            self._body.addWidget(row)

        n        = min(len(results), _MAX_VISIBLE)
        target_h = n * _ROW_H + _V_PAD * 2

        self._reposition()
        self.resize(self._sf.width(), 0)
        self.show()
        self.raise_()
        self._open_anim(target_h)

    def navigate(self, delta: int) -> None:
        if not self._rows:
            return
        nxt = max(0, min(len(self._rows) - 1, self._hi + delta))
        if nxt == self._hi:
            return
        if self._hi >= 0:
            self._rows[self._hi].set_highlighted(False)
        self._hi = nxt
        self._rows[self._hi].set_highlighted(True)

    def activate_selected(self) -> None:
        if 0 <= self._hi < len(self._rows):
            self._select(self._rows[self._hi].result)

    # ── private ───────────────────────────────────────────────────────────

    def _select(self, r: dict) -> None:
        self._close_anim()
        self.result_selected.emit(r["doc_id"], r["doc_type"])

    def _clear_rows(self) -> None:
        for row in self._rows:
            self._body.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

    def _reposition(self) -> None:
        pt    = self._sf.mapToGlobal(QPoint(0, self._sf.height() + 6))
        local = self._main_win.mapFromGlobal(pt)
        w     = self._sf.width()
        self.move(local)
        self.setFixedWidth(w)

    def _open_anim(self, target_h: int) -> None:
        self._anim.setStartValue(0)
        self._anim.setEndValue(target_h)
        self._anim.start()

    def _close_anim(self) -> None:
        if self._closing:
            return
        self._closing = True
        self._disconnect_on_closed()
        self._anim.stop()
        self._anim.setStartValue(self.height())
        self._anim.setEndValue(0)
        self._anim.finished.connect(self._on_closed)
        self._on_closed_connected = True
        self._anim.start()

    def _disconnect_on_closed(self) -> None:
        if self._on_closed_connected:
            self._anim.finished.disconnect(self._on_closed)
            self._on_closed_connected = False

    def _on_closed(self) -> None:
        self._anim.finished.disconnect(self._on_closed)
        self._on_closed_connected = False
        self._closing = False
        self.hide()
        self._clear_rows()

    def _is_click_outside(self, global_pos: QPoint) -> bool:
        """True if global_pos lands outside both the search field and this dropdown."""
        sf_rect = QRect(
            self._sf.mapToGlobal(QPoint(0, 0)),
            self._sf.size(),
        )
        dd_rect = QRect(
            self._main_win.mapToGlobal(self.pos()),
            self.size(),
        )
        return not sf_rect.contains(global_pos) and not dd_rect.contains(global_pos)

    # ── event filter ──────────────────────────────────────────────────────

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        # ── search field: key navigation ──────────────────────────────────
        if obj is self._sf and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Down:
                self.navigate(+1)
                return True
            if key == Qt.Key.Key_Up:
                self.navigate(-1)
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.activate_selected()
                return True
            if key == Qt.Key.Key_Escape:
                self._close_anim()
                return True

        # ── main window: reposition on resize/move ────────────────────────
        elif obj is self._main_win:
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
                if not self.isHidden():
                    self._reposition()

        # ── application-level: close on click outside ─────────────────────
        elif (
            obj is not self._sf
            and obj is not self._main_win
            and event.type() == QEvent.Type.MouseButtonPress
            and not self.isHidden()
        ):
            gpos = event.globalPosition().toPoint()
            if self._is_click_outside(gpos):
                self._close_anim()

        return super().eventFilter(obj, event)
