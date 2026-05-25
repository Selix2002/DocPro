from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor

from docpro_frontend.history.styles.history_styles import (
    ACTION_BTN, BADGE, ROW_HOVER, ROW_LAST_HOVER, ROW_LAST_NORMAL, ROW_NORMAL,
)


class HistoryRow(QWidget):
    row_clicked = Signal(int, str)  # doc_id, doc_type ("cot" | "inf")

    def __init__(
        self,
        doc_id: int,
        number: str,
        doc_type: str,       # "quote" | "report" (DB value)
        client_name: str,
        status: str,
        date_label: str,
        is_last: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._doc_id = doc_id
        self._nav_type = "inf" if doc_type == "report" else "cot"
        self.setObjectName("HistRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._normal = ROW_LAST_NORMAL if is_last else ROW_NORMAL
        self._hover  = ROW_LAST_HOVER  if is_last else ROW_HOVER
        self.setStyleSheet(self._normal)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(21, 14, 21, 14)
        layout.setSpacing(0)

        # Document number
        num = QLabel(number)
        num.setFixedWidth(120)
        num.setStyleSheet(
            "font-size: 17px; font-weight: 600; color: #111827; background: transparent;"
        )
        layout.addWidget(num)

        # Type badge (icon + label)
        is_quote   = doc_type == "quote"
        icon_char  = "🧾" if is_quote else "📋"
        type_text  = "Cotización" if is_quote else "Informe técnico"
        type_color = "#B45309" if is_quote else "#1D4ED8"

        type_box = QWidget()
        type_box.setFixedWidth(180)
        type_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        type_box.setStyleSheet("background: transparent;")
        type_h = QHBoxLayout(type_box)
        type_h.setContentsMargins(0, 0, 0, 0)
        type_h.setSpacing(6)

        icon_lbl = QLabel(icon_char)
        icon_lbl.setStyleSheet(
            f"font-size: 18px; color: {type_color}; background: transparent;"
        )
        type_lbl = QLabel(type_text)
        type_lbl.setStyleSheet(
            f"font-size: 17px; color: {type_color}; background: transparent;"
        )
        type_h.addWidget(icon_lbl)
        type_h.addWidget(type_lbl)
        type_h.addStretch()
        layout.addWidget(type_box)

        # Client name (stretch)
        client_lbl = QLabel(client_name)
        client_lbl.setStyleSheet(
            "font-size: 17px; color: #374151; background: transparent;"
        )
        layout.addWidget(client_lbl, stretch=1)

        # Status badge
        status_lbl = QLabel(status)
        status_lbl.setStyleSheet(BADGE.get(status, BADGE["Borrador"]))
        status_lbl.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        status_lbl.setFixedWidth(120)
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_lbl)
        layout.addSpacing(20)

        # Date
        date_lbl = QLabel(date_label)
        date_lbl.setFixedWidth(160)
        date_lbl.setStyleSheet(
            "font-size: 16px; color: #9CA3AF; background: transparent;"
        )
        layout.addWidget(date_lbl)

        # Action button — opens document editor
        action_btn = QPushButton("•••")
        action_btn.setStyleSheet(ACTION_BTN)
        action_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        action_btn.clicked.connect(
            lambda: self.row_clicked.emit(self._doc_id, self._nav_type)
        )
        layout.addWidget(action_btn)

    def enterEvent(self, event):
        self.setStyleSheet(self._hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._normal)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.row_clicked.emit(self._doc_id, self._nav_type)
        super().mousePressEvent(event)
