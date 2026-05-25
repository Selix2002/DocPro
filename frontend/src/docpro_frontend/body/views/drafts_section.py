from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor

from docpro_frontend.body.styles.body_styles import DRAFTS_PANEL, COUNT_BADGE

class DraftsPendingSection(QWidget):
    draft_opened = Signal(int, str)  # doc_id, doc_type

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("BORRADORES PENDIENTES")
        title.setStyleSheet(
            "font-size: 15px; font-weight: 600; letter-spacing: 1px; color: #374151;"
        )
        layout.addWidget(title)
        layout.addSpacing(15)

        self._panel = QFrame()
        self._panel.setObjectName("DraftsPanel")
        self._panel.setStyleSheet(DRAFTS_PANEL)
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)

        header = QWidget()
        header.setStyleSheet("background: transparent; border-bottom: 1px solid #F3F4F6;")
        header_h = QHBoxLayout(header)
        header_h.setContentsMargins(21, 15, 21, 15)
        header_h.setSpacing(0)

        header_label = QLabel("PENDIENTES")
        header_label.setStyleSheet(
            "font-size: 17px; font-weight: 600; letter-spacing: 1px; "
            "color: #374151; background: transparent;"
        )

        self._count_badge = QLabel("")
        self._count_badge.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._count_badge.setStyleSheet(COUNT_BADGE)

        header_h.addWidget(header_label)
        header_h.addStretch()
        header_h.addWidget(self._count_badge)
        panel_layout.addWidget(header)

        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(0)
        panel_layout.addWidget(self._rows_container)

        layout.addWidget(self._panel)

        self.set_drafts([])

    def set_drafts(self, drafts: list[dict]) -> None:
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        count = len(drafts)
        self._count_badge.setText(f"{count} borrador{'es' if count != 1 else ''}")

        for i, draft in enumerate(drafts):
            row = _DraftRow(
                title=draft["title"],
                time=draft["time"],
                document_id=draft["document_id"],
                doc_type=draft.get("doc_type", "cot"),
                show_separator=i < count - 1,
            )
            row.clicked.connect(self.draft_opened)
            self._rows_layout.addWidget(row)


class _DraftRow(QWidget):
    clicked = Signal(int, str)  # doc_id, doc_type

    def __init__(self, title: str, time: str, document_id: int, doc_type: str, show_separator: bool, parent=None):
        super().__init__(parent)
        self._document_id = document_id
        self._doc_type = doc_type
        sep_style = "border-bottom: 1px solid #F9FAFB;" if show_separator else ""
        self._style_normal = f"background: transparent; {sep_style}"
        self._style_hover = f"background: #FAFAFA; {sep_style}"
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(self._style_normal)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(21, 14, 21, 14)
        layout.setSpacing(12)

        icon_char  = "🧾" if doc_type == "cot" else "📋"
        icon_color = "#B45309" if doc_type == "cot" else "#1D4ED8"
        icon = QLabel(icon_char)
        icon.setStyleSheet(f"font-size: 23px; color: {icon_color}; background: transparent;")
        icon.setFixedWidth(27)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 18px; color: #111827; background: transparent;"
        )

        time_label = QLabel(time)
        time_label.setStyleSheet("font-size: 15px; color: #9CA3AF; background: transparent;")

        layout.addWidget(icon)
        layout.addWidget(title_label, stretch=1)
        layout.addWidget(time_label)

    def enterEvent(self, event):
        self.setStyleSheet(self._style_hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._style_normal)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._document_id, self._doc_type)
        super().mousePressEvent(event)
