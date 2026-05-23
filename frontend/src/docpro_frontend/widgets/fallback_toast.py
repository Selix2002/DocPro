from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer


class FallbackToast(QFrame):
    """Floating 3-second notification shown when a Groq fallback model was used."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FallbackToast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "QFrame#FallbackToast {"
            "  background: #FEF3C7;"
            "  border: 1px solid #FCD34D;"
            "  border-radius: 8px;"
            "}"
        )

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)

        icon = QLabel("⚠")
        icon.setStyleSheet("font-size: 14px; color: #92400E; background: transparent;")
        self._msg = QLabel()
        self._msg.setStyleSheet(
            "font-size: 13px; color: #92400E; background: transparent;"
        )

        lay.addWidget(icon)
        lay.addWidget(self._msg)
        self.hide()

    def show_message(self, model_id: str) -> None:
        self._msg.setText(f"Modelo no disponible. Se usó {model_id} en su lugar.")
        self.adjustSize()
        p = self.parent()
        if p is not None:
            self.move((p.width() - self.width()) // 2, 16)
        self.show()
        self.raise_()
        self._timer.start(3000)
