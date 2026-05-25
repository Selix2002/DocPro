import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

_SQLITE_MAGIC = b"SQLite format 3\x00"


def _is_valid_sqlite(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(16) == _SQLITE_MAGIC
    except OSError:
        return False


class BackupService:
    def export(self, db_path: Path, parent: QWidget | None = None) -> str | None:
        """
        Opens a save dialog and copies the SQLite DB to the chosen path.
        Returns an ISO timestamp string on success, None if cancelled.
        """
        default_name = f"docpro_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        dest, _ = QFileDialog.getSaveFileName(
            parent,
            "Exportar copia de seguridad",
            str(Path.home() / default_name),
            "Base de datos SQLite (*.db)",
        )
        if not dest:
            return None
        shutil.copy2(db_path, dest)
        return datetime.now().isoformat()

    def restore(self, db_path: Path, parent: QWidget | None = None) -> bool:
        """
        Opens an open dialog, asks for confirmation, and overwrites db_path.
        Returns True if the restore was performed (caller must reload).
        """
        src, _ = QFileDialog.getOpenFileName(
            parent,
            "Restaurar desde backup",
            str(Path.home()),
            "Base de datos SQLite (*.db)",
        )
        if not src:
            return False

        if not _is_valid_sqlite(src):
            QMessageBox.critical(
                parent,
                "Archivo inválido",
                "El archivo seleccionado no es una base de datos SQLite válida.",
            )
            return False

        reply = QMessageBox.warning(
            parent,
            "Restaurar backup",
            "Esto reemplazará toda la base de datos actual.\n"
            "La acción no se puede deshacer. ¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return False

        shutil.copy2(src, db_path)
        return True
