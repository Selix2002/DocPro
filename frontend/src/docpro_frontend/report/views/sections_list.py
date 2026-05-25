from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal

from docpro_frontend.report.styles import report_styles as S
from docpro_frontend.report.views.section_block import SectionBlock


class SectionsList(QWidget):
    """
    Container managing dynamic numbered sections with add/remove/reorder.
    Default sections: Antecedentes, Trabajos, Resultados, Conclusión.
    Includes the "Agregar nueva sección" dashed button at the bottom.
    """

    field_changed = Signal()

    _DEFAULT_TITLES = ["Antecedentes", "Trabajos", "Resultados", "Conclusión"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocks: list[SectionBlock] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self._blocks_container = QWidget()
        self._blocks_layout = QVBoxLayout(self._blocks_container)
        self._blocks_layout.setContentsMargins(0, 0, 0, 0)
        self._blocks_layout.setSpacing(8)
        root.addWidget(self._blocks_container)

        self._add_btn = QPushButton("+ Agregar nueva sección")
        self._add_btn.setStyleSheet(S.add_section_btn())
        self._add_btn.clicked.connect(lambda: self.add_section())
        root.addWidget(self._add_btn)

        self._reset_to_defaults()

    # ── Public ────────────────────────────────────────────────────────────────

    def add_section(self, title: str = "") -> SectionBlock:
        block = self._append_block(title)
        self.field_changed.emit()
        return block

    def get_data(self) -> list[dict]:
        return [b.get_data() for b in self._blocks]

    def set_data(self, sections: list[dict]) -> None:
        for b in self._blocks:
            b.deleteLater()
        self._blocks.clear()
        for sec in sections:
            b = self._append_block(sec.get("title", ""))
            if sec.get("content"):
                b.set_content(sec["content"])
            for sub in sec.get("subsections", []):
                b.add_subsection(sub.get("title", ""), sub.get("content", ""))

    def reset(self) -> None:
        for b in self._blocks:
            b.deleteLater()
        self._blocks.clear()
        self._reset_to_defaults()

    def set_readonly(self, readonly: bool) -> None:
        self._add_btn.setEnabled(not readonly)
        for b in self._blocks:
            b.set_readonly(readonly)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _reset_to_defaults(self) -> None:
        for title in self._DEFAULT_TITLES:
            self._append_block(title)

    def _append_block(self, title: str = "") -> SectionBlock:
        pos = len(self._blocks) + 1
        block = SectionBlock(pos, title)
        block.data_changed.connect(self.field_changed)
        block.move_up_requested.connect(lambda: self._move_block(block, -1))
        block.move_down_requested.connect(lambda: self._move_block(block, 1))
        block.delete_requested.connect(lambda: self._remove_block(block))
        self._blocks_layout.addWidget(block)
        self._blocks.append(block)
        self._update_move_buttons()
        return block

    def _move_block(self, block: SectionBlock, delta: int) -> None:
        idx = self._blocks.index(block)
        new_idx = idx + delta
        if not (0 <= new_idx < len(self._blocks)):
            return
        self._blocks[idx], self._blocks[new_idx] = self._blocks[new_idx], self._blocks[idx]
        for b in self._blocks:
            self._blocks_layout.removeWidget(b)
        for b in self._blocks:
            self._blocks_layout.addWidget(b)
        for i, b in enumerate(self._blocks, 1):
            b.set_position(i)
        self._update_move_buttons()
        self.field_changed.emit()

    def _remove_block(self, block: SectionBlock) -> None:
        self._blocks.remove(block)
        block.deleteLater()
        for i, b in enumerate(self._blocks, 1):
            b.set_position(i)
        self._update_move_buttons()
        self.field_changed.emit()

    def _update_move_buttons(self) -> None:
        count = len(self._blocks)
        for i, b in enumerate(self._blocks):
            b.set_move_up_enabled(i > 0)
            b.set_move_down_enabled(i < count - 1)
