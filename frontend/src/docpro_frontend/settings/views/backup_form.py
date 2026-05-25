from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.widgets.backup_action_row import BackupActionRow


class BackupForm(QWidget):
    """Form block: Backup y restauración — export and restore actions."""

    export_requested = Signal()
    restore_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("BACKUP Y RESTAURACIÓN")
        title.setStyleSheet(S.d_section_title())
        layout.addWidget(title)

        self._export_row = BackupActionRow(
            icon="💾",
            icon_color="green",
            name="Exportar copia de seguridad",
            description="Último backup: nunca",
            btn_label="Exportar",
            btn_danger=False,
        )
        self._export_row.action_clicked.connect(self.export_requested)

        self._restore_row = BackupActionRow(
            icon="📥",
            icon_color="amber",
            name="Restaurar desde backup",
            description="Reemplaza la base actual. No se puede deshacer.",
            btn_label="Restaurar",
            btn_danger=True,
        )
        self._restore_row.action_clicked.connect(self.restore_requested)

        layout.addWidget(self._export_row)
        layout.addWidget(self._restore_row)

    # ── Public ────────────────────────────────────────────────────────

    def set_last_backup(self, text: str) -> None:
        """Update the export row description (e.g. 'Último backup: ayer a las 10:30')."""
        self._export_row._desc_lbl.setText(f"Último backup: {text}")
