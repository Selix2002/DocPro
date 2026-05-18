from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor

from docpro_frontend.body.styles.body_styles import RECENT_CARD_NORMAL, RECENT_CARD_HOVER, BADGE


class RecentCard(QFrame):
    clicked = Signal(int)

    def __init__(
        self,
        doc_type: str,
        title: str,
        subtitle: str,
        status: str,
        document_id: int,
        parent=None,
    ):
        super().__init__(parent)
        self._document_id = document_id
        self.setStyleSheet(RECENT_CARD_NORMAL)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        icon_char = "🧾" if doc_type == "cot" else "📋"
        icon_color = "#B45309" if doc_type == "cot" else "#1D4ED8"
        icon = QLabel(icon_char)
        icon.setStyleSheet(
            f"font-size: 27px; color: {icon_color}; background: transparent;"
        )
        icon.setFixedWidth(33)
        layout.addWidget(icon)

        body = QFrame()
        body.setStyleSheet("background: transparent; border: none;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: 500; color: #111827; background: transparent;"
        )
        title_label.setWordWrap(False)

        sub_label = QLabel(subtitle)
        sub_label.setStyleSheet(
            "font-size: 17px; color: #9CA3AF; background: transparent;"
        )

        body_layout.addWidget(title_label)
        body_layout.addWidget(sub_label)
        layout.addWidget(body, stretch=1)

        badge = QLabel(status)
        badge.setStyleSheet(BADGE.get(status, BADGE["Borrador"]))
        badge.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout.addWidget(badge)

    def enterEvent(self, event):
        self.setStyleSheet(RECENT_CARD_HOVER)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(RECENT_CARD_NORMAL)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._document_id)
        super().mousePressEvent(event)
