from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.settings.styles import settings_styles as S


class AccountRow(QWidget):
    """Connected Gmail account row with avatar, info text, and disconnect button."""

    disconnect_clicked = Signal()

    def __init__(self, email: str = "", detail: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("AccountRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # Avatar: first letter of email
        self._avatar = QLabel()
        self._avatar.setFixedSize(36, 36)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Info
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self._name_lbl = QLabel()
        self._detail_lbl = QLabel()
        info_col.addWidget(self._name_lbl)
        info_col.addWidget(self._detail_lbl)

        self._disconnect_btn = QPushButton("Desconectar")
        self._disconnect_btn.clicked.connect(self.disconnect_clicked)

        layout.addWidget(self._avatar)
        layout.addLayout(info_col, 1)
        layout.addWidget(self._disconnect_btn)

        self._apply_styles()
        self.set_account(email, detail)

    # ── Public ────────────────────────────────────────────────────────

    def set_account(self, email: str, detail: str) -> None:
        initial = email[0].upper() if email else "?"
        self._avatar.setText(initial)
        self._name_lbl.setText(email)
        self._detail_lbl.setText(detail)

    # ── Internal ──────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        self.setStyleSheet(S.account_row())
        self._avatar.setStyleSheet(S.account_avatar())
        self._name_lbl.setStyleSheet(S.account_name())
        self._detail_lbl.setStyleSheet(S.account_detail())
        self._disconnect_btn.setStyleSheet(S.btn_danger_small())
