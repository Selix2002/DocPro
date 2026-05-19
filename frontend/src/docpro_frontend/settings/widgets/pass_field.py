from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Qt

from docpro_frontend.settings.styles import settings_styles as S


class PassField(QWidget):
    """Password QLineEdit with a show/hide toggle button."""

    def __init__(self, placeholder: str = "", parent=None):
        super().__init__(parent)
        self._visible = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setEchoMode(QLineEdit.EchoMode.Password)

        self._toggle = QPushButton("👁")
        self._toggle.clicked.connect(self._toggle_visibility)
        self._toggle.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(self._input, 1)
        layout.addWidget(self._toggle)

        self._apply_styles()

    # ── Public ────────────────────────────────────────────────────────

    def text(self) -> str:
        return self._input.text()

    def set_text(self, value: str) -> None:
        self._input.setText(value)

    # ── Internal ──────────────────────────────────────────────────────

    def _toggle_visibility(self) -> None:
        self._visible = not self._visible
        mode = QLineEdit.EchoMode.Normal if self._visible else QLineEdit.EchoMode.Password
        self._input.setEchoMode(mode)

    def _apply_styles(self) -> None:
        self._input.setStyleSheet(S.field_input())
        self._toggle.setStyleSheet(S.pass_toggle_btn())
