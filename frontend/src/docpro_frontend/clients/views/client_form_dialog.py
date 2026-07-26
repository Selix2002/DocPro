from __future__ import annotations

import re

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

# Accepts: 12.345.678-9  |  1.234.567-K  |  12345678-9  |  12345678-k
_RUT_RE = re.compile(r"^\d{1,3}([.]\d{3})*-[\dkK]$|^\d{7,8}-[\dkK]$")

_STYLE = """
QDialog { background: #FFFFFF; }
QLineEdit {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 16px;
    color: #111827;
}
QLineEdit:focus { border: 1px solid #B45309; background: #FFFBF7; }
QLineEdit:read-only { background: #F3F4F6; color: #6B7280; border-color: #E5E7EB; }
QPushButton#CancelBtn {
    background: #F3F4F6; border: 1px solid #E5E7EB;
    border-radius: 8px; padding: 9px 22px;
    font-size: 16px; color: #374151;
}
QPushButton#CancelBtn:hover { background: #E5E7EB; }
QPushButton#SaveBtn {
    background: #B45309; border: none;
    border-radius: 8px; padding: 9px 22px;
    font-size: 16px; color: white; font-weight: 600;
}
QPushButton#SaveBtn:hover { background: #92400E; }
"""


class ClientFormDialog(QDialog):
    """
    Unified create / edit dialog for a client.
    create mode: client_id=None, data=None — all fields editable
    edit mode:   client_id=int, data=dict  — RUT read-only, rest pre-filled
    Emits saved(dict) on accept; dict always contains rut/name/address/email/phone,
    and also client_id when in edit mode.
    """

    saved = Signal(dict)

    def __init__(
        self,
        client_id: int | None = None,
        data: dict | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._client_id = client_id
        is_edit = client_id is not None

        self.setWindowTitle("Editar cliente" if is_edit else "Nuevo cliente")
        self.setMinimumWidth(500)
        self.setModal(True)
        self.setStyleSheet(_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)

        title = QLabel("Editar cliente" if is_edit else "Nuevo cliente")
        title.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #111827; background: transparent;"
        )
        root.addWidget(title)
        root.addSpacing(4)

        subtitle = QLabel(
            "Edita los datos del cliente."
            if is_edit else
            "Completa los datos del nuevo cliente."
        )
        subtitle.setStyleSheet(
            "font-size: 16px; color: #6B7280; background: transparent;"
        )
        root.addWidget(subtitle)
        root.addSpacing(22)

        d = data or {}
        self._rut   = self._field("RUT *",                  "12.345.678-9",        readonly=is_edit, value=d.get("rut", ""))
        self._name  = self._field("Nombre / Razón social *", "Empresa Ejemplo SpA",                  value=d.get("name", ""))
        self._addr  = self._field("Dirección",               "Calle, número, ciudad",                value=d.get("address") or "")
        self._email = self._field("Correo electrónico",      "correo@empresa.cl",                    value=d.get("email") or "")
        self._phone = self._field("Teléfono",                "+56 9 1234 5678",                      value=d.get("phone") or ("" if is_edit else "+56 9 "))

        for field in (self._rut, self._name, self._addr, self._email, self._phone):
            root.addWidget(field["container"])
            root.addSpacing(12)

        if not is_edit:
            self._rut["input"].setMaxLength(12)
            self._rut["input"].textEdited.connect(self._on_rut_edited)

        root.addSpacing(8)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #E5E7EB;")
        root.addWidget(sep)
        root.addSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("CancelBtn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Guardar cambios" if is_edit else "Crear cliente")
        save_btn.setObjectName("SaveBtn")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    def get_data(self) -> dict:
        d: dict = {
            "rut":     self._rut["input"].text().strip(),
            "name":    self._name["input"].text().strip(),
            "address": self._addr["input"].text().strip() or None,
            "email":   self._email["input"].text().strip() or None,
            "phone":   self._phone["input"].text().strip() or None,
        }
        if self._client_id is not None:
            d["client_id"] = self._client_id
        return d

    def _on_save(self) -> None:
        rut  = self._rut["input"].text().strip()
        name = self._name["input"].text().strip()
        if not rut:
            self._rut["input"].setFocus()
            self._rut["input"].setStyleSheet(
                self._rut["input"].styleSheet()
                + "border: 1px solid #EF4444;"
            )
            return
        if not _RUT_RE.match(rut):
            QMessageBox.warning(
                self,
                "RUT inválido",
                "El RUT ingresado no tiene un formato válido.\n"
                "Ejemplo correcto: 12.345.678-9",
            )
            self._rut["input"].setFocus()
            return
        if not name:
            self._name["input"].setFocus()
            self._name["input"].setStyleSheet(
                self._name["input"].styleSheet()
                + "border: 1px solid #EF4444;"
            )
            return
        self.saved.emit(self.get_data())
        self.accept()

    @staticmethod
    def _format_rut(raw: str) -> str:
        cleaned = "".join(c for c in raw.upper() if c.isdigit() or c == "K")
        if len(cleaned) <= 1:
            return cleaned
        body, dv = cleaned[:-1], cleaned[-1]
        grouped = ""
        for i, c in enumerate(reversed(body)):
            if i > 0 and i % 3 == 0:
                grouped = "." + grouped
            grouped = c + grouped
        return f"{grouped}-{dv}"

    def _on_rut_edited(self, text: str) -> None:
        formatted = self._format_rut(text)
        if formatted != text:
            inp = self._rut["input"]
            inp.blockSignals(True)
            inp.setText(formatted)
            inp.setCursorPosition(len(formatted))
            inp.blockSignals(False)

    @staticmethod
    def _field(
        label_text: str,
        placeholder: str,
        *,
        readonly: bool = False,
        value: str = "",
    ) -> dict:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #374151; background: transparent;"
        )

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        if value:
            inp.setText(value)
        if readonly:
            inp.setReadOnly(True)

        layout.addWidget(lbl)
        layout.addWidget(inp)
        return {"container": container, "input": inp}
