from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from docpro_frontend.services import asset_service
from docpro_frontend.settings.styles import settings_styles as S

_FIRMA_FILENAME = "firma_imagen.png"
_THUMB_W, _THUMB_H = 160, 80


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

        self._name  = self._field("Nombre o razón social")
        self._city  = self._field("Ciudad")
        self._phone = self._field("Teléfono")
        self._email = self._field("Correo electrónico")

        grid.addLayout(self._labeled("NOMBRE O RAZÓN SOCIAL", self._name),  0, 0, 1, 2)
        grid.addLayout(self._labeled("CIUDAD",                self._city),   1, 0)
        grid.addLayout(self._labeled("TELÉFONO",              self._phone),  1, 1)
        grid.addLayout(self._labeled("CORREO ELECTRÓNICO",    self._email),  2, 0, 1, 2)

        layout.addLayout(grid)

        firma_title = QLabel("FIRMA")
        firma_title.setStyleSheet(S.d_section_title())
        layout.addWidget(firma_title)

        firma_grid = QGridLayout()
        firma_grid.setSpacing(12)

        self._firma_nombre = self._field("Nombre completo del responsable")
        self._firma_cargo  = self._field("Cargo o título profesional")

        firma_grid.addLayout(self._labeled("NOMBRE DEL RESPONSABLE", self._firma_nombre), 0, 0)
        firma_grid.addLayout(self._labeled("CARGO",                   self._firma_cargo),  0, 1)

        layout.addLayout(firma_grid)

        # ── Imagen de firma ───────────────────────────────────────────
        # Stores just the filename (resolved to abs path via asset_service).
        self._firma_imagen_path: str = ""

        img_label = QLabel("IMAGEN DE FIRMA")
        img_label.setStyleSheet(S.field_label())
        layout.addWidget(img_label)

        img_row = QHBoxLayout()
        img_row.setSpacing(12)

        self._firma_thumbnail = QLabel("Sin imagen")
        self._firma_thumbnail.setFixedSize(_THUMB_W, _THUMB_H)
        self._firma_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._firma_thumbnail.setStyleSheet(
            "border: 1px solid #D1D5DB; background: #F9FAFB; color: #9CA3AF; font-size: 11px;"
        )
        img_row.addWidget(self._firma_thumbnail)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._btn_upload = QPushButton("Subir imagen…")
        self._btn_upload.setStyleSheet(S.btn_ghost())
        self._btn_upload.clicked.connect(self._on_upload_imagen)
        btn_col.addWidget(self._btn_upload)

        self._btn_remove = QPushButton("Eliminar")
        self._btn_remove.setStyleSheet(S.btn_danger_small())
        self._btn_remove.clicked.connect(self._on_remove_imagen)
        self._btn_remove.setVisible(False)
        btn_col.addWidget(self._btn_remove)

        img_row.addLayout(btn_col)
        img_row.addStretch()
        layout.addLayout(img_row)

    # ── Public ────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        return {
            "name":          self._name.text(),
            "city":          self._city.text(),
            "phone":         self._phone.text(),
            "email":         self._email.text(),
            "firma_nombre":  self._firma_nombre.text(),
            "firma_cargo":   self._firma_cargo.text(),
            "firma_imagen":  self._firma_imagen_path,
        }

    def set_data(
        self,
        name:         str,
        city:         str,
        phone:        str,
        email:        str,
        firma_nombre: str = "",
        firma_cargo:  str = "",
        firma_imagen: str = "",
    ) -> None:
        self._name.setText(name)
        self._city.setText(city)
        self._phone.setText(phone)
        self._email.setText(email)
        self._firma_nombre.setText(firma_nombre)
        self._firma_cargo.setText(firma_cargo)
        self._set_thumbnail(firma_imagen)

    # ── Handlers ──────────────────────────────────────────────────────

    def _on_upload_imagen(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen de firma",
            str(Path.home()),
            "Imágenes (*.png *.jpg *.jpeg *.bmp)",
        )
        if not path:
            return
        filename = asset_service.store(Path(path), _FIRMA_FILENAME)
        self._set_thumbnail(filename)

    def _on_remove_imagen(self) -> None:
        asset_service.remove(_FIRMA_FILENAME)
        self._firma_imagen_path = ""
        self._firma_thumbnail.setPixmap(QPixmap())
        self._firma_thumbnail.setText("Sin imagen")
        self._btn_remove.setVisible(False)

    # ── Internal ──────────────────────────────────────────────────────

    def _set_thumbnail(self, filename: str) -> None:
        # Accept either a bare filename (new) or absolute legacy path (fallback).
        abs_path = asset_service.resolve(filename) if filename else None
        if abs_path is None and filename and Path(filename).exists():
            abs_path = Path(filename)
            filename = abs_path.name
        if abs_path is not None:
            px = QPixmap(str(abs_path)).scaled(
                _THUMB_W, _THUMB_H,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._firma_thumbnail.setText("")
            self._firma_thumbnail.setPixmap(px)
            self._firma_imagen_path = filename
            self._btn_remove.setVisible(True)
        else:
            self._firma_imagen_path = ""
            self._firma_thumbnail.setPixmap(QPixmap())
            self._firma_thumbnail.setText("Sin imagen")
            self._btn_remove.setVisible(False)

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
