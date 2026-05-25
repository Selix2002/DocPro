from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

_CHIP_BASE = """
QPushButton {{
    background: {bg};
    color: {fg};
    border: 1px solid {border};
    border-radius: 16px;
    padding: 4px 14px;
    font-size: 14px;
    font-weight: {weight};
}}
QPushButton:hover {{ background: {hover}; }}
"""

_INACTIVE = _CHIP_BASE.format(
    bg="#F9FAFB", fg="#374151", border="#E5E7EB",
    weight="400", hover="#F3F4F6",
)
_ACTIVE_AMBER = _CHIP_BASE.format(
    bg="#FEF3C7", fg="#92400E", border="#FCD34D",
    weight="600", hover="#FDE68A",
)
_ACTIVE_BLUE = _CHIP_BASE.format(
    bg="#DBEAFE", fg="#1E40AF", border="#93C5FD",
    weight="600", hover="#BFDBFE",
)
_ACTIVE_GRAY = _CHIP_BASE.format(
    bg="#F3F4F6", fg="#374151", border="#D1D5DB",
    weight="600", hover="#E5E7EB",
)

_STATUS_ACTIVE = {
    "Borrador":   _CHIP_BASE.format(bg="#FEF3C7", fg="#92400E", border="#FCD34D", weight="600", hover="#FDE68A"),
    "Finalizado": _CHIP_BASE.format(bg="#DBEAFE", fg="#1E40AF", border="#93C5FD", weight="600", hover="#BFDBFE"),
    "Enviado":    _CHIP_BASE.format(bg="#D1FAE5", fg="#065F46", border="#6EE7B7", weight="600", hover="#A7F3D0"),
    "Aprobado":   _CHIP_BASE.format(bg="#CCFBF1", fg="#0F766E", border="#5EEAD4", weight="600", hover="#99F6E4"),
    "Rechazado":  _CHIP_BASE.format(bg="#FEE2E2", fg="#991B1B", border="#FCA5A5", weight="600", hover="#FECACA"),
}

_SEP = "QFrame { background: #E5E7EB; }"


class FilterBar(QWidget):
    """Chip bar that appears below the toolbar when Filtros is toggled."""

    filter_changed = Signal(object, object)  # type_val: str|None, status_val: str|None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: white; border-bottom: 1px solid #F3F4F6;")

        self._type_val:   str | None = None
        self._status_val: str | None = None

        h = QHBoxLayout(self)
        h.setContentsMargins(36, 0, 36, 0)
        h.setSpacing(6)

        label = QLabel("Tipo:")
        label.setStyleSheet("font-size:13px;color:#6B7280;background:transparent;")
        h.addWidget(label)

        self._type_chips: list[tuple[QPushButton, str | None]] = []
        for text, val in [("Todo", None), ("Cotizaciones", "quote"), ("Informes", "report")]:
            btn = QPushButton(text)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, v=val: self._set_type(v))
            self._type_chips.append((btn, val))
            h.addWidget(btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedSize(1, 22)
        sep.setStyleSheet(_SEP)
        h.addWidget(sep)

        label2 = QLabel("Estado:")
        label2.setStyleSheet("font-size:13px;color:#6B7280;background:transparent;")
        h.addWidget(label2)

        self._status_chips: list[tuple[QPushButton, str | None]] = []
        for text, val in [
            ("Todos",      None),
            ("Borrador",   "Borrador"),
            ("Finalizado", "Finalizado"),
            ("Enviado",    "Enviado"),
            ("Aprobado",   "Aprobado"),
            ("Rechazado",  "Rechazado"),
        ]:
            btn = QPushButton(text)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, v=val: self._set_status(v))
            self._status_chips.append((btn, val))
            h.addWidget(btn)

        h.addStretch()

        self._refresh_styles()

    # ── private ───────────────────────────────────────────────────────────

    def _set_type(self, val: str | None) -> None:
        if self._type_val == val:
            return
        self._type_val = val
        self._refresh_styles()
        self.filter_changed.emit(self._type_val, self._status_val)

    def _set_status(self, val: str | None) -> None:
        if self._status_val == val:
            return
        self._status_val = val
        self._refresh_styles()
        self.filter_changed.emit(self._type_val, self._status_val)

    def _refresh_styles(self) -> None:
        for btn, val in self._type_chips:
            if val == self._type_val:
                btn.setStyleSheet(_ACTIVE_AMBER if val == "quote" else
                                  _ACTIVE_BLUE  if val == "report" else
                                  _ACTIVE_GRAY)
            else:
                btn.setStyleSheet(_INACTIVE)

        for btn, val in self._status_chips:
            if val == self._status_val:
                btn.setStyleSheet(_STATUS_ACTIVE.get(val, _ACTIVE_GRAY))
            else:
                btn.setStyleSheet(_INACTIVE)
