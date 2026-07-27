from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget,
)

from docpro_frontend.quote.styles import quote_styles as S
from docpro_frontend.widgets.ai_improve_button import AiImproveButton


class ObsSubsectionCard(QFrame):
    """
    Recursive card: [num label] + [title input] + [body] + [nested children].

    Levels:  depth 0 → "1."   depth 1 → "1.1."   depth 2 → "1.1.1."
    MAX_DEPTH = 2 caps nesting at three levels.

    Signals:
        data_changed     — any field edited (bubbles up from children)
        delete_requested — user clicked ✕  (handled by parent)
    """

    MAX_DEPTH = 2

    data_changed     = Signal()
    delete_requested = Signal()

    def __init__(
        self,
        number: str,
        depth: int = 0,
        title: str = "",
        content: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._number = number
        self._depth  = depth
        self._child_cards: list[ObsSubsectionCard] = []

        # Outer frame is a transparent layout container (no border of its own)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # ── Visible card box ──────────────────────────────────────────────────
        inner = QFrame()
        inner.setObjectName("ObsSubsectionCard")
        inner.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        inner.setStyleSheet(S.obs_subsection_card())

        card_vbox = QVBoxLayout(inner)
        card_vbox.setContentsMargins(12, 10, 12, 12)
        card_vbox.setSpacing(8)

        # Body textarea first so AiImproveButton can reference it
        self._body = QTextEdit()
        self._body.setPlaceholderText("Contenido de la subsección…")
        self._body.setStyleSheet(S.obs_textarea())
        self._body.setMinimumHeight(70)
        if content:
            self._body.setPlainText(content)

        # Header row: [num] [title input] [ai btn] [del btn]
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        self._num_label = QLabel(f"{number}.")
        self._num_label.setStyleSheet(S.obs_num_label())
        self._num_label.setFixedWidth(52)

        self._title_edit = QLineEdit(title)
        self._title_edit.setPlaceholderText("Título (opcional)")
        self._title_edit.setStyleSheet(S.obs_subsection_title_input())

        self._ai_btn = AiImproveButton(self._body)

        del_btn = QPushButton("✕")
        del_btn.setStyleSheet(S.obs_subsection_del_btn())
        del_btn.clicked.connect(self.delete_requested)

        hdr.addWidget(self._num_label)
        hdr.addWidget(self._title_edit, 1)
        hdr.addWidget(self._ai_btn)
        hdr.addWidget(del_btn)

        card_vbox.addLayout(hdr)
        card_vbox.addWidget(self._body)
        root.addWidget(inner)

        # ── Children area (only when not at max depth) ────────────────────────
        if depth < self.MAX_DEPTH:
            children_wrap = QWidget()
            children_vbox = QVBoxLayout(children_wrap)
            children_vbox.setContentsMargins(24, 2, 0, 0)
            children_vbox.setSpacing(6)
            self._children_layout: QVBoxLayout | None = children_vbox

            self._add_child_btn: QPushButton | None = QPushButton("＋  Añadir sub-ítem")
            self._add_child_btn.setStyleSheet(S.obs_add_child_btn())
            self._add_child_btn.clicked.connect(lambda: self._on_add_child())
            children_vbox.addWidget(self._add_child_btn)

            root.addWidget(children_wrap)
        else:
            self._children_layout = None
            self._add_child_btn   = None

        # Signals
        self._title_edit.textEdited.connect(lambda _: self.data_changed.emit())
        self._body.textChanged.connect(self.data_changed)

    # ── Children management ───────────────────────────────────────────────────

    def _on_add_child(self) -> None:
        self._add_child()
        self.data_changed.emit()

    def _add_child(
        self,
        title: str = "",
        content: str = "",
        children: list[dict] | None = None,
    ) -> None:
        if self._children_layout is None:
            return
        pos          = len(self._child_cards) + 1
        child_number = f"{self._number}.{pos}"
        card         = ObsSubsectionCard(child_number, self._depth + 1, title, content)
        card.data_changed.connect(self.data_changed)
        card.delete_requested.connect(lambda: self._remove_child(card))

        btn_idx = self._children_layout.indexOf(self._add_child_btn)
        self._children_layout.insertWidget(btn_idx, card)
        self._child_cards.append(card)

        if children:
            card.load_children(children)

    def _remove_child(self, card: ObsSubsectionCard) -> None:
        if self._children_layout is None:
            return
        self._children_layout.removeWidget(card)
        self._child_cards.remove(card)
        card.deleteLater()
        self._renumber_children()
        self.data_changed.emit()

    def _renumber_children(self) -> None:
        for i, child in enumerate(self._child_cards):
            child.set_number(f"{self._number}.{i + 1}")

    def load_children(self, children: list[dict]) -> None:
        for child_data in (children or []):
            self._add_child(
                title    = child_data.get("title", ""),
                content  = child_data.get("content", ""),
                children = child_data.get("children"),
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def set_number(self, number: str) -> None:
        self._number = number
        self._num_label.setText(f"{number}.")
        self._renumber_children()

    def get_data(self) -> dict:
        return {
            "title":    self._title_edit.text().strip(),
            "content":  self._body.toPlainText().strip(),
            "children": [c.get_data() for c in self._child_cards],
        }

    def set_readonly(self, readonly: bool) -> None:
        self._title_edit.setReadOnly(readonly)
        self._body.setReadOnly(readonly)
        self._ai_btn.setEnabled(not readonly)
        if self._add_child_btn is not None:
            self._add_child_btn.setVisible(not readonly)
        for child in self._child_cards:
            child.set_readonly(readonly)
