from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.header.styles.header_styles import TAB_BTN

_TABS = ["Inicio", "Cotizaciones", "Informes", "Historial", "Clientes"]


class TabBar(QWidget):
    tab_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setStyleSheet(TAB_BTN)

        self._buttons: dict[str, QPushButton] = {}
        for name in _TABS:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked=False, n=name: self._on_click(n))
            layout.addWidget(btn)
            self._buttons[name] = btn

        self._set_active("Inicio")

    def _set_active(self, name: str) -> None:
        for n, btn in self._buttons.items():
            btn.setProperty("active", n == name)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_click(self, name: str) -> None:
        self._set_active(name)
        self.tab_changed.emit(name)
