"""Small dialogs for creating and renaming profiles."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


_DLG_STYLE = """
QDialog { background: #FFFFFF; }
QLabel  { color: #111827; background: transparent; font-size: 15px; }
QLineEdit {
    background: #FFFFFF; color: #111827;
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 8px 12px; font-size: 15px;
    selection-background-color: #FEF3C7; selection-color: #B45309;
}
QLineEdit:focus { border: 1px solid #B45309; }
QPushButton {
    background: #F3F4F6; color: #111827;
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 7px 20px; font-size: 15px; min-width: 90px;
}
QPushButton:hover { background: #E5E7EB; }
QPushButton:default {
    background: #B45309; color: #FFFFFF; border-color: #B45309;
}
QPushButton:default:hover { background: #92400E; }
"""


class _NameDialog(QDialog):
    def __init__(
        self,
        parent,
        *,
        title: str,
        label: str,
        initial: str = "",
        accept_text: str = "Guardar",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedWidth(420)
        self.setStyleSheet(_DLG_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(12)

        root.addWidget(QLabel(label))

        self._input = QLineEdit(initial)
        self._input.setMinimumHeight(36)
        self._input.selectAll()
        root.addWidget(self._input)

        buttons = QDialogButtonBox()
        cancel_btn = buttons.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        accept_btn = buttons.addButton(accept_text, QDialogButtonBox.ButtonRole.AcceptRole)
        accept_btn.setDefault(True)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(buttons)
        root.addLayout(row)

    def value(self) -> str:
        return self._input.text().strip()


def prompt_new_profile(parent) -> str | None:
    """Ask for the new profile name. Returns the trimmed name or None if cancelled."""
    dlg = _NameDialog(
        parent,
        title="Nuevo perfil",
        label="Nombre del nuevo perfil:",
        initial="",
        accept_text="Crear",
    )
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    name = dlg.value()
    if not name:
        return None
    return name


def prompt_rename_profile(parent, current_name: str) -> str | None:
    """Ask for a new name for the active profile."""
    dlg = _NameDialog(
        parent,
        title="Renombrar perfil",
        label="Nuevo nombre para el perfil:",
        initial=current_name,
        accept_text="Renombrar",
    )
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None
    name = dlg.value()
    if not name or name == current_name:
        return None
    return name


def show_error(parent, message: str) -> None:
    dlg = QMessageBox(parent)
    dlg.setWindowTitle("Perfil")
    dlg.setIcon(QMessageBox.Icon.Warning)
    dlg.setText(message)
    dlg.setStyleSheet(_DLG_STYLE)
    dlg.exec()
