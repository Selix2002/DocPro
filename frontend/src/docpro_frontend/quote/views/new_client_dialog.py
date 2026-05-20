from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QWidget, QFrame,
)
from PySide6.QtCore import Signal, Qt

from docpro_frontend.quote.styles import quote_styles as S


class NewClientDialog(QDialog):
    """
    Modal dialog for creating a client inline from the quote form.
    Emits client_saved(data: dict) on accept.
    RUT is pre-filled and read-only (came from the search field).
    """

    client_saved = Signal(dict)

    def __init__(self, rut: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo cliente")
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setStyleSheet(S.dialog_bg())

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(0)

        title = QLabel("Nuevo cliente")
        title.setStyleSheet(S.dialog_title())
        root.addWidget(title)
        root.addSpacing(4)

        subtitle = QLabel("Completa los datos del nuevo cliente.")
        subtitle.setStyleSheet(S.dialog_subtitle())
        root.addWidget(subtitle)
        root.addSpacing(20)

        self._rut   = self._field("RUT *",             "12.345.678-9", readonly=True, value=rut)
        self._name  = self._field("Nombre / Razón social *", "Empresa Ejemplo SpA")
        self._addr  = self._field("Dirección",          "Calle, número, ciudad")
        self._email = self._field("Correo electrónico", "correo@empresa.cl")
        self._phone = self._field("Teléfono",           "+56 9 1234 5678")

        for widget in (self._rut, self._name, self._addr, self._email, self._phone):
            root.addWidget(widget["container"])
            root.addSpacing(12)

        root.addSpacing(8)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: #E5E7EB;")
        root.addWidget(sep)
        root.addSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(S.btn_ghost())
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Crear cliente")
        save_btn.setStyleSheet(S.btn_primary())
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._on_save)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

    # ── Public ────────────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        return {
            "rut":     self._rut["input"].text().strip(),
            "name":    self._name["input"].text().strip(),
            "address": self._addr["input"].text().strip() or None,
            "email":   self._email["input"].text().strip() or None,
            "phone":   self._phone["input"].text().strip() or None,
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_save(self) -> None:
        name = self._name["input"].text().strip()
        rut  = self._rut["input"].text().strip()
        if not name or not rut:
            self._name["input"].setFocus()
            return
        self.client_saved.emit(self.get_data())
        self.accept()

    @staticmethod
    def _field(label_text: str, placeholder: str, readonly: bool = False, value: str = "") -> dict:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(S.field_label())

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setStyleSheet(S.field_input())
        if value:
            inp.setText(value)
        if readonly:
            inp.setReadOnly(True)

        layout.addWidget(lbl)
        layout.addWidget(inp)

        return {"container": container, "input": inp, "label": lbl}
