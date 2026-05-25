from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QTextEdit, QPushButton,
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

import docpro_frontend.theme as _th


class SuggestionBubble(QFrame):
    """Floating suggestion card: shows AI-improved text with Apply / Reject actions.

    Parented to the top-level window so it floats over all other widgets.
    Only one instance is kept per window; reuse via show_suggestion().
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SuggestionBubble")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setWindowFlag(Qt.WindowType.SubWindow, False)

        self._field: QTextEdit | None = None
        self._suggestion: str = ""

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(shadow)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())
        root.addWidget(self._build_body())
        root.addWidget(self._build_footer())

        self._apply_style()
        self.hide()

    # ── Public ────────────────────────────────────────────────────────

    def show_suggestion(self, field: QTextEdit, suggestion: str) -> None:
        self._field = field
        self._suggestion = suggestion
        self._preview.setPlainText(suggestion)
        self._position_near(field)
        self.show()
        self.raise_()

    # ── Builders ──────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        t = _th.current
        header = QWidget()
        header.setObjectName("BubbleHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setStyleSheet(
            f"QWidget#BubbleHeader {{"
            f"  background: {t['purple']};"
            f"  border-radius: 10px 10px 0 0;"
            f"}}"
        )
        header.setFixedHeight(38)

        h = QHBoxLayout(header)
        h.setContentsMargins(14, 0, 10, 0)
        h.setSpacing(8)

        icon = QLabel("✦")
        icon.setStyleSheet("font-size: 13px; color: #EDE9FE; background: transparent;")

        title = QLabel("Sugerencia de IA")
        title.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #FFFFFF; background: transparent;"
        )

        close = QPushButton("✕")
        close.setFixedSize(22, 22)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setStyleSheet(
            "QPushButton {"
            "  background: transparent; border: none;"
            "  color: #C4B5FD; font-size: 12px;"
            "}"
            "QPushButton:hover { color: #FFFFFF; }"
        )
        close.clicked.connect(self.hide)

        h.addWidget(icon)
        h.addSpacing(2)
        h.addWidget(title)
        h.addStretch()
        h.addWidget(close)

        return header

    def _build_body(self) -> QWidget:
        t = _th.current
        body = QWidget()
        body.setObjectName("BubbleBody")
        body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body.setStyleSheet(
            f"QWidget#BubbleBody {{ background: {t['surface']}; }}"
        )

        lay = QVBoxLayout(body)
        lay.setContentsMargins(14, 12, 14, 12)

        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMaximumHeight(180)
        self._preview.setStyleSheet(
            f"QTextEdit {{"
            f"  background: {t['surface_alt']};"
            f"  border: 1px solid {t['border']};"
            f"  border-radius: 6px;"
            f"  padding: 8px;"
            f"  font-size: 13px;"
            f"  color: {t['text']};"
            f"}}"
        )
        lay.addWidget(self._preview)

        return body

    def _build_footer(self) -> QWidget:
        t = _th.current
        footer = QWidget()
        footer.setObjectName("BubbleFooter")
        footer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        footer.setStyleSheet(
            f"QWidget#BubbleFooter {{"
            f"  background: {t['surface']};"
            f"  border-top: 1px solid {t['border']};"
            f"  border-radius: 0 0 10px 10px;"
            f"}}"
        )
        footer.setFixedHeight(50)

        h = QHBoxLayout(footer)
        h.setContentsMargins(14, 0, 14, 0)
        h.setSpacing(8)
        h.addStretch()

        self._reject_btn = QPushButton("✕  Rechazar")
        self._reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reject_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: transparent;"
            f"  border: 1px solid {t['border']};"
            f"  border-radius: 7px;"
            f"  padding: 5px 14px;"
            f"  font-size: 12px; font-weight: 500;"
            f"  color: {t['muted']};"
            f"}}"
            f"QPushButton:hover {{ background: {t['border_soft']}; color: {t['text']}; }}"
        )
        self._reject_btn.clicked.connect(self.hide)

        self._apply_btn = QPushButton("✓  Aplicar")
        self._apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: {t['green']};"
            f"  border: none;"
            f"  border-radius: 7px;"
            f"  padding: 5px 14px;"
            f"  font-size: 12px; font-weight: 600;"
            f"  color: #FFFFFF;"
            f"}}"
            f"QPushButton:hover {{ background: {t['green_text']}; }}"
        )
        self._apply_btn.clicked.connect(self._on_apply)

        h.addWidget(self._reject_btn)
        h.addWidget(self._apply_btn)

        return footer

    # ── Internal ──────────────────────────────────────────────────────

    def _apply_style(self) -> None:
        t = _th.current
        self.setStyleSheet(
            f"QFrame#SuggestionBubble {{"
            f"  background: {t['surface']};"
            f"  border: 1px solid #DDD6FE;"
            f"  border-radius: 10px;"
            f"}}"
        )

    def _on_apply(self) -> None:
        if self._field is not None:
            self._field.setPlainText(self._suggestion)
        self.hide()

    def _position_near(self, field: QTextEdit) -> None:
        win = self.parent()
        if win is None:
            return

        w = max(field.width(), 340)
        self.setFixedWidth(w)
        self.adjustSize()

        # Try to place bubble just below the field
        bottom_left = field.mapTo(win, QPoint(0, field.height() + 6))
        x, y = bottom_left.x(), bottom_left.y()

        # If it overflows the bottom, place above instead
        if y + self.height() > win.height() - 8:
            above = field.mapTo(win, QPoint(0, -self.height() - 6))
            y = above.y()

        # Clamp horizontally
        x = max(8, min(x, win.width() - w - 8))

        self.move(x, max(8, y))
