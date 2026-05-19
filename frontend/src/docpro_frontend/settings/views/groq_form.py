from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Signal

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.widgets.pass_field import PassField


_MODELS = [
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]


class GroqForm(QWidget):
    """Form block: IA · Groq — API key, model selector, and validate button."""

    validate_requested = Signal(str, str)  # (api_key, model)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("IA · GROQ")
        title.setStyleSheet(S.d_section_title())
        layout.addWidget(title)

        # API key field
        key_col = QVBoxLayout()
        key_col.setSpacing(5)
        key_lbl = QLabel("API KEY")
        key_lbl.setStyleSheet(S.field_label())
        self._key_field = PassField("gsk_…")
        hint = QLabel("Almacenada localmente cifrada con Fernet.")
        hint.setStyleSheet(S.field_hint())
        key_col.addWidget(key_lbl)
        key_col.addWidget(self._key_field)
        key_col.addWidget(hint)
        layout.addLayout(key_col)

        # Model + validate row
        model_row = QHBoxLayout()
        model_row.setSpacing(10)
        model_lbl = QLabel("MODELO")
        model_lbl.setStyleSheet(S.field_label())

        self._model_combo = QComboBox()
        for m in _MODELS:
            self._model_combo.addItem(m)
        self._model_combo.setStyleSheet(S.field_combobox())

        self._validate_btn = QPushButton("Validar")
        self._validate_btn.setStyleSheet(S.btn_validate())
        self._validate_btn.clicked.connect(self._on_validate)

        model_row.addWidget(model_lbl, 0)
        model_row.addWidget(self._model_combo, 1)
        model_row.addWidget(self._validate_btn)
        layout.addLayout(model_row)

    # ── Public ────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        return {
            "api_key": self._key_field.text(),
            "model":   self._model_combo.currentText(),
        }

    def set_data(self, api_key: str, model: str) -> None:
        self._key_field.set_text(api_key)
        index = self._model_combo.findText(model)
        if index >= 0:
            self._model_combo.setCurrentIndex(index)

    # ── Internal ──────────────────────────────────────────────────────

    def _on_validate(self) -> None:
        self.validate_requested.emit(
            self._key_field.text(),
            self._model_combo.currentText(),
        )
