from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.settings.styles import settings_styles as S


class BackupActionRow(QWidget):
    """
    Backup action row: colored icon badge, name/description text, action button.
    Used for both Export and Restore actions.
    """

    action_clicked = Signal()

    def __init__(
        self,
        icon: str,
        icon_color: str,
        name: str,
        description: str,
        btn_label: str,
        btn_danger: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("BackupActionRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        # Icon badge
        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setFixedSize(36, 36)
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._icon_lbl.setStyleSheet(S.backup_icon_badge(icon_color))

        # Text column
        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._name_lbl = QLabel(name)
        self._desc_lbl = QLabel(description)
        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._desc_lbl)

        # Action button
        self._btn = QPushButton(btn_label)
        self._btn.clicked.connect(self.action_clicked)

        layout.addWidget(self._icon_lbl)
        layout.addLayout(text_col, 1)
        layout.addWidget(self._btn)

        self._apply_styles(btn_danger)

    # ── Internal ──────────────────────────────────────────────────────

    def _apply_styles(self, danger: bool) -> None:
        self.setStyleSheet(S.backup_action_row())
        self._name_lbl.setStyleSheet(S.backup_action_name())
        self._desc_lbl.setStyleSheet(S.backup_action_desc())
        self._btn.setStyleSheet(S.btn_danger_small() if danger else S.btn_small())
