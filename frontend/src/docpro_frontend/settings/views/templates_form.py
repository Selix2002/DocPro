from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.widgets.template_row import TemplateRow


class TemplatesForm(QWidget):
    """Form block: Plantillas de sección — list of saved templates."""

    delete_template_requested = Signal(int)
    edit_template_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        title = QLabel("PLANTILLAS DE SECCIÓN")
        title.setStyleSheet(S.d_section_title())
        layout.addWidget(title)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        layout.addWidget(self._list_container)

    # ── Public ────────────────────────────────────────────────────────

    def set_templates(self, templates: list[dict]) -> None:
        """templates: list of {"id": int, "name": str, "usage_count": int}"""
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for tmpl in templates:
            row = TemplateRow(tmpl["id"], tmpl["name"], tmpl["usage_count"])
            row.delete_clicked.connect(self.delete_template_requested)
            row.edit_clicked.connect(self.edit_template_requested)
            self._list_layout.addWidget(row)
