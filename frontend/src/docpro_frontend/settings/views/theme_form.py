from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QDialog,
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


_FONT_OPTIONS = ["Arial", "Helvetica", "Verdana", "Georgia", "Times New Roman"]
_HEADER_FILENAME = "header.png"
_THUMB_W, _THUMB_H = 240, 60

_COLOR_DIALOG_STYLE = """
QColorDialog, QDialog {
    background: #FFFFFF;
    color: #111827;
}
QColorDialog QLabel, QDialog QLabel {
    color: #111827;
    background: transparent;
}
QColorDialog QLineEdit, QColorDialog QSpinBox,
QDialog QLineEdit, QDialog QSpinBox {
    background: #FFFFFF;
    color: #111827;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    padding: 2px 4px;
    selection-background-color: #FEF3C7;
    selection-color: #B45309;
}
QColorDialog QSpinBox::up-button, QColorDialog QSpinBox::down-button,
QDialog QSpinBox::up-button, QDialog QSpinBox::down-button {
    background: #F3F4F6;
    border: 1px solid #D1D5DB;
    width: 16px;
}
QColorDialog QPushButton, QDialog QPushButton {
    background: #FFFFFF;
    color: #111827;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 6px 14px;
    min-width: 60px;
}
QColorDialog QPushButton:hover, QDialog QPushButton:hover {
    background: #F3F4F6;
}
QColorDialog QPushButton:default, QDialog QPushButton:default {
    background: #B45309;
    color: #FFFFFF;
    border: 1px solid #B45309;
}
QColorDialog QPushButton:default:hover, QDialog QPushButton:default:hover {
    background: #92400E;
}
"""

DEFAULTS = {
    "primary": "#111111",
    "accent":  "#EBEBEB",
    "text":    "#1A1A1A",
    "font_family": "Arial",
    "header_imagen": "",
}


class ThemeForm(QWidget):
    """Per-profile document theme: colors, font, header image."""

    theme_changed = Signal()  # emits on any user change (colors, font, header)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("PLANTILLA DE DOCUMENTOS")
        title.setStyleSheet(S.d_section_title())
        layout.addWidget(title)

        # ── Colors ──
        color_grid = QGridLayout()
        color_grid.setSpacing(12)

        self._primary_btn, primary_col = self._color_field("COLOR PRIMARIO", "primary")
        self._accent_btn,  accent_col  = self._color_field("COLOR DE ACENTO", "accent")
        self._text_btn,    text_col    = self._color_field("COLOR DE TEXTO",  "text")

        color_grid.addLayout(primary_col, 0, 0)
        color_grid.addLayout(accent_col,  0, 1)
        color_grid.addLayout(text_col,    0, 2)
        layout.addLayout(color_grid)

        # ── Font ──
        font_row = QVBoxLayout()
        font_row.setSpacing(5)
        font_label = QLabel("FUENTE")
        font_label.setStyleSheet(S.field_label())
        self._font_combo = QComboBox()
        self._font_combo.addItems(_FONT_OPTIONS)
        self._font_combo.setStyleSheet(S.field_combobox())
        self._font_combo.currentTextChanged.connect(lambda _: self.theme_changed.emit())
        font_row.addWidget(font_label)
        font_row.addWidget(self._font_combo)
        layout.addLayout(font_row)

        # ── Header image ──
        self._header_filename: str = ""

        hdr_label = QLabel("IMAGEN DE ENCABEZADO")
        hdr_label.setStyleSheet(S.field_label())
        layout.addWidget(hdr_label)

        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(12)

        self._hdr_thumbnail = QLabel("Sin imagen")
        self._hdr_thumbnail.setFixedSize(_THUMB_W, _THUMB_H)
        self._hdr_thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hdr_thumbnail.setStyleSheet(
            "border: 1px solid #D1D5DB; background: #F9FAFB; color: #9CA3AF; font-size: 11px;"
        )
        hdr_row.addWidget(self._hdr_thumbnail)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(8)
        btn_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._btn_hdr_upload = QPushButton("Subir imagen…")
        self._btn_hdr_upload.setStyleSheet(S.btn_ghost())
        self._btn_hdr_upload.clicked.connect(self._on_upload_header)
        btn_col.addWidget(self._btn_hdr_upload)

        self._btn_hdr_remove = QPushButton("Eliminar")
        self._btn_hdr_remove.setStyleSheet(S.btn_danger_small())
        self._btn_hdr_remove.clicked.connect(self._on_remove_header)
        self._btn_hdr_remove.setVisible(False)
        btn_col.addWidget(self._btn_hdr_remove)

        hdr_row.addLayout(btn_col)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        self.set_data(**DEFAULTS)

    # ── Public ────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        return {
            "primary":       self._primary_btn.property("color") or DEFAULTS["primary"],
            "accent":        self._accent_btn.property("color")  or DEFAULTS["accent"],
            "text":          self._text_btn.property("color")    or DEFAULTS["text"],
            "font_family":   self._font_combo.currentText(),
            "header_imagen": self._header_filename,
        }

    def set_data(
        self,
        primary:       str = DEFAULTS["primary"],
        accent:        str = DEFAULTS["accent"],
        text:          str = DEFAULTS["text"],
        font_family:   str = DEFAULTS["font_family"],
        header_imagen: str = "",
    ) -> None:
        self._apply_color(self._primary_btn, primary or DEFAULTS["primary"])
        self._apply_color(self._accent_btn,  accent  or DEFAULTS["accent"])
        self._apply_color(self._text_btn,    text    or DEFAULTS["text"])
        idx = self._font_combo.findText(font_family)
        self._font_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._set_header_thumbnail(header_imagen)

    # ── Handlers ──────────────────────────────────────────────────────

    def _on_pick_color(self, btn: QPushButton) -> None:
        current = QColor(btn.property("color") or "#000000")
        dlg = QColorDialog(current, self)
        dlg.setWindowTitle("Elegir color")
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dlg.setStyleSheet(_COLOR_DIALOG_STYLE)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        picked = dlg.selectedColor()
        if not picked.isValid():
            return
        self._apply_color(btn, picked.name())
        self.theme_changed.emit()

    def _on_upload_header(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen de encabezado",
            str(Path.home()),
            "Imágenes (*.png *.jpg *.jpeg *.bmp)",
        )
        if not path:
            return
        filename = asset_service.store(Path(path), _HEADER_FILENAME)
        self._set_header_thumbnail(filename)
        self.theme_changed.emit()

    def _on_remove_header(self) -> None:
        asset_service.remove(_HEADER_FILENAME)
        self._header_filename = ""
        self._hdr_thumbnail.setPixmap(QPixmap())
        self._hdr_thumbnail.setText("Sin imagen")
        self._btn_hdr_remove.setVisible(False)
        self.theme_changed.emit()

    # ── Internal ──────────────────────────────────────────────────────

    def _color_field(self, label_text: str, key: str) -> tuple[QPushButton, QVBoxLayout]:
        col = QVBoxLayout()
        col.setSpacing(5)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(S.field_label())
        col.addWidget(lbl)

        btn = QPushButton()
        btn.setFixedHeight(34)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._on_pick_color(btn))
        col.addWidget(btn)
        return btn, col

    def _apply_color(self, btn: QPushButton, hex_color: str) -> None:
        btn.setProperty("color", hex_color)
        btn.setText(hex_color.upper())
        text_color = _readable_text_color(hex_color)
        btn.setStyleSheet(
            f"background: {hex_color}; color: {text_color}; "
            f"border: 1px solid #D1D5DB; border-radius: 6px; "
            f"font-family: monospace; font-size: 13px; padding: 0 12px;"
        )

    def _set_header_thumbnail(self, filename: str) -> None:
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
            self._hdr_thumbnail.setText("")
            self._hdr_thumbnail.setPixmap(px)
            self._header_filename = filename
            self._btn_hdr_remove.setVisible(True)
        else:
            self._header_filename = ""
            self._hdr_thumbnail.setPixmap(QPixmap())
            self._hdr_thumbnail.setText("Sin imagen")
            self._btn_hdr_remove.setVisible(False)


def _readable_text_color(hex_color: str) -> str:
    """Return black or white text for contrast against the background."""
    c = QColor(hex_color)
    luminance = (0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()) / 255.0
    return "#FFFFFF" if luminance < 0.55 else "#111111"
