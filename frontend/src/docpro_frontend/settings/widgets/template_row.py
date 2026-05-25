from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCursor

from docpro_frontend.settings.styles import settings_styles as S


class TemplateRow(QWidget):
    """Single row in the section-templates list: icon, name + meta, edit button, delete button."""

    delete_clicked = Signal(int)  # emits template id
    edit_clicked = Signal(int)    # emits template id

    def __init__(self, template_id: int, name: str, usage_count: int, parent=None):
        super().__init__(parent)
        self._template_id = template_id
        self._hovered = False

        self.setObjectName("TemplateRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(10)

        self._icon = QLabel("☰")

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self._name_lbl = QLabel(name)
        self._meta_lbl = QLabel(f"Sección completa · Usada {usage_count} veces")
        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._meta_lbl)

        self._edit_btn = QPushButton("✎")
        self._edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self._template_id))

        self._del_btn = QPushButton("✕")
        self._del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._del_btn.clicked.connect(lambda: self.delete_clicked.emit(self._template_id))

        layout.addWidget(self._icon)
        layout.addLayout(text_col, 1)
        layout.addWidget(self._edit_btn)
        layout.addWidget(self._del_btn)

        self._apply_styles()

    # ── Internal ──────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        self.setStyleSheet(S.template_row(self._hovered))
        self._icon.setStyleSheet(S.template_row_icon())
        self._name_lbl.setStyleSheet(S.template_row_name())
        self._meta_lbl.setStyleSheet(S.template_row_meta())
        self._edit_btn.setStyleSheet(S.template_action_btn())
        self._del_btn.setStyleSheet(S.template_del_btn())

    def enterEvent(self, event):
        self._hovered = True
        self.setStyleSheet(S.template_row(True))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.setStyleSheet(S.template_row(False))
        super().leaveEvent(event)
