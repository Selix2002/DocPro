from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit

from docpro_frontend.settings.styles import settings_styles as S


class CompanyProfileForm(QWidget):
    """Form block: Perfil de empresa — name, city, phone, email, firma."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("DATOS DEL EMISOR")
        title.setStyleSheet(S.d_section_title())
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)

        self._name = self._field("Nombre o razón social")
        self._city = self._field("Ciudad")
        self._phone = self._field("Teléfono")
        self._email = self._field("Correo electrónico")

        grid.addLayout(self._labeled("NOMBRE O RAZÓN SOCIAL", self._name), 0, 0, 1, 2)
        grid.addLayout(self._labeled("CIUDAD", self._city), 1, 0)
        grid.addLayout(self._labeled("TELÉFONO", self._phone), 1, 1)
        grid.addLayout(self._labeled("CORREO ELECTRÓNICO", self._email), 2, 0, 1, 2)

        layout.addLayout(grid)

        firma_title = QLabel("FIRMA")
        firma_title.setStyleSheet(S.d_section_title())
        layout.addWidget(firma_title)

        firma_grid = QGridLayout()
        firma_grid.setSpacing(12)

        self._firma_nombre = self._field("Nombre completo del responsable")
        self._firma_cargo  = self._field("Cargo o título profesional")

        firma_grid.addLayout(self._labeled("NOMBRE DEL RESPONSABLE", self._firma_nombre), 0, 0)
        firma_grid.addLayout(self._labeled("CARGO", self._firma_cargo), 0, 1)

        layout.addLayout(firma_grid)

    # ── Public ────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        return {
            "name":         self._name.text(),
            "city":         self._city.text(),
            "phone":        self._phone.text(),
            "email":        self._email.text(),
            "firma_nombre": self._firma_nombre.text(),
            "firma_cargo":  self._firma_cargo.text(),
        }

    def set_data(
        self,
        name: str,
        city: str,
        phone: str,
        email: str,
        firma_nombre: str = "",
        firma_cargo: str = "",
    ) -> None:
        self._name.setText(name)
        self._city.setText(city)
        self._phone.setText(phone)
        self._email.setText(email)
        self._firma_nombre.setText(firma_nombre)
        self._firma_cargo.setText(firma_cargo)

    # ── Internal ──────────────────────────────────────────────────────

    def _field(self, placeholder: str) -> QLineEdit:
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setStyleSheet(S.field_input())
        return inp

    def _labeled(self, label_text: str, widget: QWidget) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(5)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(S.field_label())
        col.addWidget(lbl)
        col.addWidget(widget)
        return col
