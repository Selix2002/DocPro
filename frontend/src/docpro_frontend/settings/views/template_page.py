"""Combines ThemeForm + ThemePreview side-by-side."""
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from docpro_frontend.settings.views.theme_form import ThemeForm
from docpro_frontend.settings.views.theme_preview import ThemePreview


class TemplatePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(0)
        self._form = ThemeForm()
        left.addWidget(self._form)
        left.addStretch()

        left_wrap = QWidget()
        left_wrap.setLayout(left)
        left_wrap.setMinimumWidth(360)
        root.addWidget(left_wrap, 3)

        self._preview = ThemePreview()
        self._preview.setMinimumWidth(300)
        root.addWidget(self._preview, 4)

        self._form.theme_changed.connect(self._on_theme_changed)

    @property
    def form(self) -> ThemeForm:
        return self._form

    def refresh_preview(self) -> None:
        self._preview.schedule_refresh(self._form.get_data())

    def _on_theme_changed(self) -> None:
        self.refresh_preview()
