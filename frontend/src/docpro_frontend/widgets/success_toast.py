from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer


class SuccessToast(QFrame):
    """Floating 4-second notification for successful operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SuccessToast")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            "QFrame#SuccessToast {"
            "  background: #D1FAE5;"
            "  border: 1px solid #6EE7B7;"
            "  border-radius: 8px;"
            "}"
        )

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)

        icon = QLabel("✓")
        icon.setStyleSheet("font-size: 14px; color: #065F46; background: transparent;")
        self._msg = QLabel()
        self._msg.setStyleSheet(
            "font-size: 13px; color: #065F46; background: transparent;"
        )

        lay.addWidget(icon)
        lay.addWidget(self._msg)
        self.hide()

    def show_message(self, text: str, duration_ms: int = 4000) -> None:
        self._msg.setText(text)
        self.adjustSize()
        p = self.parent()
        if p is not None:
            self.move((p.width() - self.width()) // 2, 16)
        self.show()
        self.raise_()
        self._timer.start(duration_ms)
