from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QLineEdit, QPushButton, QTextEdit,
)
from PySide6.QtCore import Signal, Qt

from docpro_frontend.report.styles import report_styles as S
from docpro_frontend.report.views.subsection_card import SubsectionCard


class SectionBlock(QFrame):
    """
    One dynamic section: header (number + editable title + move/delete buttons)
    + body (optional section-level text + subsections + add-subsection button).
    Signals:
        data_changed        — any field changed
        move_up_requested   — user clicked ▲
        move_down_requested — user clicked ▼
        delete_requested    — user clicked ✕
    """

    data_changed        = Signal()
    move_up_requested   = Signal()
    move_down_requested = Signal()
    delete_requested    = Signal()

    def __init__(self, position: int, title: str = "", parent=None):
        super().__init__(parent)
        self._position = position
        self._subsections: list[SubsectionCard] = []

        self.setObjectName("SectionBlock")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.section_block())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_head(title))

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 20)
        body_layout.setSpacing(12)

        # Section-level content
        self._content_edit = QTextEdit()
        self._content_edit.setPlaceholderText("Contenido de la sección (opcional)…")
        self._content_edit.setStyleSheet(S.section_textarea())
        self._content_edit.setMinimumHeight(80)
        body_layout.addWidget(self._content_edit)

        # Subsections container
        self._subs_container = QWidget()
        self._subs_layout = QVBoxLayout(self._subs_container)
        self._subs_layout.setContentsMargins(0, 0, 0, 0)
        self._subs_layout.setSpacing(8)
        body_layout.addWidget(self._subs_container)

        # Add subsection button
        self._add_sub_btn = QPushButton("+ Agregar subsección")
        self._add_sub_btn.setStyleSheet(S.add_sub_btn())
        self._add_sub_btn.clicked.connect(lambda: self._add_subsection())
        body_layout.addWidget(self._add_sub_btn)

        root.addWidget(body)

        self._content_edit.textChanged.connect(self.data_changed)
        self._title_edit.textEdited.connect(lambda _: self.data_changed.emit())

    # ── Public ────────────────────────────────────────────────────────────────

    @property
    def position(self) -> int:
        return self._position

    def set_position(self, pos: int) -> None:
        self._position = pos
        self._num_label.setText(str(pos))

    def set_move_up_enabled(self, enabled: bool) -> None:
        self._up_btn.setEnabled(enabled)

    def set_move_down_enabled(self, enabled: bool) -> None:
        self._down_btn.setEnabled(enabled)

    def add_subsection(self, title: str = "", content: str = "") -> None:
        self._add_subsection(title, content)

    def set_content(self, content: str) -> None:
        self._content_edit.setPlainText(content)

    def get_data(self) -> dict:
        return {
            "position":    self._position,
            "title":       self._title_edit.text().strip(),
            "content":     self._content_edit.toPlainText().strip() or None,
            "subsections": [sub.get_data() for sub in self._subsections],
        }

    def set_readonly(self, readonly: bool) -> None:
        self._title_edit.setReadOnly(readonly)
        self._content_edit.setReadOnly(readonly)
        self._add_sub_btn.setEnabled(not readonly)
        for sub in self._subsections:
            sub.set_readonly(readonly)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _build_head(self, title: str) -> QWidget:
        head = QWidget()
        head.setObjectName("SectionHead")
        head.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        head.setStyleSheet(S.section_head())
        head.setFixedHeight(46)

        h = QHBoxLayout(head)
        h.setContentsMargins(16, 0, 12, 0)
        h.setSpacing(6)

        # Section icon
        icon = QLabel("§")
        icon.setStyleSheet(S.section_head_icon())

        # Position badge
        self._num_label = QLabel(str(self._position))
        self._num_label.setStyleSheet(S.section_number_label())

        # Editable title
        self._title_edit = QLineEdit(title)
        self._title_edit.setPlaceholderText("Título de sección")
        self._title_edit.setStyleSheet(S.section_title_input())

        # Drag handle (visual only)
        drag = QLabel("⋮⋮")
        drag.setStyleSheet("color: #D1D5DB; font-size: 14px; background: transparent;")

        # Move buttons
        self._up_btn = QPushButton("▲")
        self._up_btn.setStyleSheet(S.btn_section_icon())
        self._up_btn.setFixedSize(26, 26)
        self._up_btn.setToolTip("Mover arriba")
        self._up_btn.clicked.connect(self.move_up_requested)

        self._down_btn = QPushButton("▼")
        self._down_btn.setStyleSheet(S.btn_section_icon())
        self._down_btn.setFixedSize(26, 26)
        self._down_btn.setToolTip("Mover abajo")
        self._down_btn.clicked.connect(self.move_down_requested)

        # Delete
        del_btn = QPushButton("✕")
        del_btn.setStyleSheet(S.btn_section_delete())
        del_btn.setFixedSize(26, 26)
        del_btn.setToolTip("Eliminar sección")
        del_btn.clicked.connect(self.delete_requested)

        h.addWidget(icon)
        h.addSpacing(2)
        h.addWidget(self._num_label)
        h.addSpacing(4)
        h.addWidget(self._title_edit, 1)
        h.addSpacing(4)
        h.addWidget(drag)
        h.addWidget(self._up_btn)
        h.addWidget(self._down_btn)
        h.addWidget(del_btn)

        return head

    def _add_subsection(self, title: str = "", content: str = "") -> SubsectionCard:
        pos = len(self._subsections) + 1
        card = SubsectionCard(pos, title, content)
        card.data_changed.connect(self.data_changed)
        card.delete_requested.connect(lambda: self._remove_subsection(card))
        self._subs_layout.addWidget(card)
        self._subsections.append(card)
        self.data_changed.emit()
        return card

    def _remove_subsection(self, card: SubsectionCard) -> None:
        self._subsections.remove(card)
        card.deleteLater()
        for i, sub in enumerate(self._subsections, 1):
            sub.set_position(i)
        self.data_changed.emit()
