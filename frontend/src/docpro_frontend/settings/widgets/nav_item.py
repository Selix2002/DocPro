from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor

from docpro_frontend.settings.styles import settings_styles as S


class NavItem(QWidget):
    """Sidebar navigation item: icon + text + optional status badge."""

    clicked = Signal(str)  # emits key

    def __init__(
        self,
        key: str,
        icon: str,
        text: str,
        badge_text: str = "",
        badge_state: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._key = key
        self._active = False
        self._badge_state = badge_state

        self.setObjectName("NavItem")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(10)

        self._icon_lbl = QLabel(icon)
        self._text_lbl = QLabel(text)

        layout.addWidget(self._icon_lbl)
        layout.addWidget(self._text_lbl, 1)

        self._badge: QLabel | None = None
        if badge_text:
            self._badge = QLabel(badge_text)
            self._badge.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            layout.addWidget(self._badge)

        self._apply_styles()

    # ── Public ────────────────────────────────────────────────────────

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_styles()

    def set_badge(self, text: str, state: str) -> None:
        self._badge_state = state
        if self._badge:
            self._badge.setText(text)
            self._badge.setStyleSheet(S.nav_badge(state))

    # ── Internal ──────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        self.setStyleSheet(S.nav_item(self._active))
        self._icon_lbl.setStyleSheet(S.nav_item_icon(self._active))
        self._text_lbl.setStyleSheet(S.nav_item_text(self._active))
        if self._badge:
            self._badge.setStyleSheet(S.nav_badge(self._badge_state))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._key)
        super().mousePressEvent(event)
