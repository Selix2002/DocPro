from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor

from docpro_frontend.settings.styles import settings_styles as S


class ThemeChip(QFrame):
    """
    Propuesta A theme-option card: visual mini-preview + label + subtitle
    + active checkmark.  key is one of 'light' | 'dark' | 'system'.
    """

    selected = Signal(str)

    def __init__(
        self,
        key: str,
        label: str,
        subtitle: str,
        active: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._key = key
        self._active = active

        self.setObjectName("ThemeOption")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Visual preview
        self._preview = self._build_preview(key)
        layout.addWidget(self._preview)

        # Label
        self._label_lbl = QLabel(label)
        self._label_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label_lbl)

        # Subtitle
        self._sub_lbl = QLabel(subtitle)
        self._sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._sub_lbl)

        # Active check
        self._check = QLabel("✓")
        self._check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._check.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout.addWidget(self._check, 0, Qt.AlignmentFlag.AlignHCenter)

        self._apply_styles()

    # ── Public ────────────────────────────────────────────────────────

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_styles()

    def is_active(self) -> bool:
        return self._active

    # ── Internal ──────────────────────────────────────────────────────

    def _build_preview(self, key: str) -> QWidget:
        container = QFrame()
        container.setObjectName("ThemePreview")
        container.setFixedHeight(56)
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        if key == "system":
            container.setStyleSheet(S.theme_preview_system())
            return container

        dark = (key == "dark")
        container.setStyleSheet(S.theme_preview_container())

        inner = QVBoxLayout(container)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        bar = QWidget()
        bar.setFixedHeight(14)
        bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        bar.setStyleSheet(S.theme_preview_bar(dark))

        body = QWidget()
        body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body.setStyleSheet(S.theme_preview_body(dark))

        inner.addWidget(bar)
        inner.addWidget(body, 1)

        return container

    def _apply_styles(self) -> None:
        self.setStyleSheet(S.theme_option(self._active))
        self._label_lbl.setStyleSheet(S.theme_option_label())
        self._sub_lbl.setStyleSheet(S.theme_option_sub())
        self._check.setStyleSheet(S.theme_check(self._active))
        self._check.setVisible(self._active)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self._key)
        super().mousePressEvent(event)
