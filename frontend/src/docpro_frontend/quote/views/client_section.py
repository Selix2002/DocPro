from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, QPushButton,
    QGridLayout,
)
from PySide6.QtCore import Signal, Qt

from docpro_frontend.quote.styles import quote_styles as S


class ClientSection(QFrame):
    """
    Destinatario card.
    Signals:
        rut_entered(rut)      — user typed a RUT (len >= 3)
        client_data_changed() — user edited any non-RUT client field
    Methods:
        fill_client(...)      — auto-populate fields after lookup (fields remain editable)
        show_not_found()      — show "Nuevo" badge
        clear_client_fields() — clear non-RUT fields
        get_client_data()     — return current field values as dict
        set_readonly(bool)    — lock all fields
    """

    rut_entered         = Signal(str)
    client_data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SectionBlock")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.section_block())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_head())

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(14)

        grid = QGridLayout()
        grid.setSpacing(14)

        # Row 0: RUT | Nombre
        self._rut_widget = self._build_rut_field()
        self._name       = self._build_field("SEÑOR/ES *",   "Nombre del destinatario")
        grid.addWidget(self._rut_widget["container"], 0, 0)
        grid.addWidget(self._name["container"],       0, 1)

        # Row 1: Dirección (full width)
        self._address = self._build_field("DIRECCIÓN", "Calle, número, ciudad")
        grid.addWidget(self._address["container"], 1, 0, 1, 2)

        # Row 2: Email | Teléfono
        self._email = self._build_field("CORREO ELECTRÓNICO", "correo@empresa.cl")
        self._phone = self._build_field("TELÉFONO",           "+56 9 1234 5678")
        grid.addWidget(self._email["container"], 2, 0)
        grid.addWidget(self._phone["container"], 2, 1)

        body_layout.addLayout(grid)
        root.addWidget(body)

        # Wire RUT input
        self._rut_input.textEdited.connect(self._on_rut_edited)

        # Relay edits from client fields so the form can trigger autosave
        for field in (self._name, self._address, self._email, self._phone):
            field["input"].textEdited.connect(lambda _: self.client_data_changed.emit())

    # ── Public ────────────────────────────────────────────────────────────────

    def fill_client(
        self,
        name: str,
        address: str | None,
        email: str | None,
        phone: str | None,
    ) -> None:
        self._name["input"].setText(name or "")
        self._address["input"].setText(address or "")
        self._email["input"].setText(email or "")
        self._phone["input"].setText(phone or "")
        self._set_badge("found")

    def show_not_found(self) -> None:
        self._set_badge("new")

    def clear_client_fields(self) -> None:
        for field in (self._name, self._address, self._email, self._phone):
            field["input"].clear()
        self._set_badge(None)

    def get_client_data(self) -> dict:
        return {
            "rut":     self._rut_input.text().strip(),
            "name":    self._name["input"].text().strip(),
            "address": self._address["input"].text().strip() or None,
            "email":   self._email["input"].text().strip() or None,
            "phone":   self._phone["input"].text().strip() or None,
        }

    def get_rut(self) -> str:
        return self._rut_input.text().strip()

    def set_rut(self, rut: str) -> None:
        self._rut_input.setText(rut)

    def reset(self) -> None:
        self._rut_input.clear()
        self.clear_client_fields()
        self._set_badge(None)

    def set_readonly(self, readonly: bool) -> None:
        self._rut_input.setReadOnly(readonly)
        for field in (self._name, self._address, self._email, self._phone):
            field["input"].setReadOnly(readonly)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_head(self) -> QWidget:
        head = QWidget()
        head.setObjectName("SectionHead")
        head.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        head.setStyleSheet(S.section_head())
        head.setFixedHeight(46)

        h = QHBoxLayout(head)
        h.setContentsMargins(20, 0, 20, 0)

        icon = QLabel("🏢")
        icon.setStyleSheet(S.section_head_icon())

        label = QLabel("Destinatario")
        label.setStyleSheet(S.section_head_label())

        h.addWidget(icon)
        h.addSpacing(8)
        h.addWidget(label)
        h.addStretch()
        return head

    def _build_rut_field(self) -> dict:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel("RUT CLIENTE *")
        lbl.setStyleSheet(S.field_label())

        row = QHBoxLayout()
        row.setSpacing(6)

        self._rut_input = QLineEdit()
        self._rut_input.setPlaceholderText("12.345.678-9")
        self._rut_input.setStyleSheet(S.rut_input())
        row.addWidget(self._rut_input, 1)

        self._rut_badge = QLabel("")
        self._rut_badge.setVisible(False)
        row.addWidget(self._rut_badge)

        layout.addWidget(lbl)
        layout.addLayout(row)
        return {"container": container, "input": self._rut_input}

    @staticmethod
    def _build_field(label_text: str, placeholder: str) -> dict:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(S.field_label())

        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setStyleSheet(S.field_input())

        layout.addWidget(lbl)
        layout.addWidget(inp)
        return {"container": container, "input": inp}

    def _on_rut_edited(self, text: str) -> None:
        rut = text.strip()
        if len(rut) < 3:
            self._set_badge(None)
            return
        self.rut_entered.emit(rut)

    def _set_badge(self, state: str | None) -> None:
        if state == "found":
            self._rut_badge.setText("✓ Encontrado")
            self._rut_badge.setStyleSheet(S.rut_badge_found())
            self._rut_badge.setVisible(True)
        elif state == "new":
            self._rut_badge.setText("+ Nuevo")
            self._rut_badge.setStyleSheet(S.rut_badge_new())
            self._rut_badge.setVisible(True)
        else:
            self._rut_badge.setVisible(False)
