from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.widgets.account_row import AccountRow


class GmailForm(QWidget):
    """Form block: Gmail — shows connected account or connect button."""

    connect_requested = Signal()
    disconnect_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("GMAIL")
        title.setStyleSheet(S.d_section_title())
        layout.addWidget(title)

        # Connected state
        self._account_row = AccountRow()
        self._account_row.disconnect_clicked.connect(self.disconnect_requested)

        # Disconnected state
        self._connect_btn = QPushButton("Conectar cuenta de Gmail")
        self._connect_btn.setStyleSheet(S.btn_ghost())
        self._connect_btn.clicked.connect(self.connect_requested)

        layout.addWidget(self._account_row)
        layout.addWidget(self._connect_btn)

        self.set_connected(False, "", "")

    # ── Public ────────────────────────────────────────────────────────

    def set_connected(self, connected: bool, email: str, detail: str) -> None:
        self._account_row.setVisible(connected)
        self._connect_btn.setVisible(not connected)
        if connected:
            self._account_row.set_account(email, detail)
