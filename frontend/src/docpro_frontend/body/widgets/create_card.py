from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor

from docpro_frontend.body.styles.body_styles import CREATE_CARD, BORDER_NORMAL, BORDER_AMBER, BORDER_BLUE


class CreateCard(QFrame):
    clicked = Signal()

    def __init__(self, label: str, next_label: str, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self._border_hover = BORDER_AMBER if color == "amber" else BORDER_BLUE
        self._apply_style(BORDER_NORMAL)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        icon_char = "🧾" if color == "amber" else "📋"
        icon_color = "#B45309" if color == "amber" else "#1D4ED8"
        icon = QLabel(icon_char)
        icon.setStyleSheet(f"font-size: 39px; color: {icon_color}; background: transparent;")
        layout.addWidget(icon)
        layout.addSpacing(12)

        name_label = QLabel(label)
        name_label.setStyleSheet(
            "font-size: 20px; font-weight: 500; color: #111827; background: transparent;"
        )
        layout.addWidget(name_label)

        self._next_label_widget = QLabel(next_label)
        self._next_label_widget.setStyleSheet(
            "font-size: 17px; color: #9CA3AF; background: transparent;"
        )
        layout.addWidget(self._next_label_widget)

    def set_next_label(self, text: str) -> None:
        self._next_label_widget.setText(text)

    def _apply_style(self, border: str) -> None:
        self.setStyleSheet(CREATE_CARD.format(border=border))

    def enterEvent(self, event):
        self._apply_style(self._border_hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(BORDER_NORMAL)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
