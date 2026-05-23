from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTextEdit,
)
from PySide6.QtCore import Signal, Qt

from docpro_frontend.report.styles import report_styles as S


class SubsectionCard(QFrame):
    """
    One subsection inside a section: title input + QTextEdit body + AI button stub.
    Signals:
        data_changed      — any field edited
        delete_requested  — user clicked the delete button
    """

    data_changed     = Signal()
    delete_requested = Signal()

    def __init__(self, position: int, title: str = "", content: str = "", parent=None):
        super().__init__(parent)
        self._position = position

        self.setObjectName("SubsectionCard")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.subsection_card())

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self._title_edit = QLineEdit(title)
        self._title_edit.setPlaceholderText("Título de subsección")
        self._title_edit.setStyleSheet(S.section_title_input())

        self._ai_btn = QPushButton("✦  Mejorar redacción")
        self._ai_btn.setStyleSheet(S.ai_btn_stub())
        self._ai_btn.setEnabled(False)
        self._ai_btn.setToolTip("Disponible en Fase 9")

        del_btn = QPushButton("✕")
        del_btn.setStyleSheet(S.btn_section_delete())
        del_btn.clicked.connect(self.delete_requested)

        title_row.addWidget(self._title_edit, 1)
        title_row.addWidget(self._ai_btn)
        title_row.addWidget(del_btn)

        # Body textarea
        self._body = QTextEdit()
        self._body.setPlaceholderText("Contenido de la subsección…")
        self._body.setStyleSheet(S.sub_textarea())
        self._body.setMinimumHeight(80)
        if content:
            self._body.setPlainText(content)

        root.addLayout(title_row)
        root.addWidget(self._body)

        self._title_edit.textEdited.connect(lambda _: self.data_changed.emit())
        self._body.textChanged.connect(self.data_changed)

    # ── Public ────────────────────────────────────────────────────────────────

    @property
    def position(self) -> int:
        return self._position

    def set_position(self, pos: int) -> None:
        self._position = pos

    def get_data(self) -> dict:
        return {
            "position": self._position,
            "title":    self._title_edit.text().strip(),
            "content":  self._body.toPlainText().strip(),
        }

    def set_content(self, content: str) -> None:
        self._body.setPlainText(content)

    def set_readonly(self, readonly: bool) -> None:
        self._title_edit.setReadOnly(readonly)
        self._body.setReadOnly(readonly)
        self._ai_btn.setEnabled(False)
