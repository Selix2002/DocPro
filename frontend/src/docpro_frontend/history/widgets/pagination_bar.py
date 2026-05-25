from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.history.styles.history_styles import PAGE_BTN_ACTIVE, PAGE_BTN_NORMAL


class PaginationBar(QWidget):
    page_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current = 0
        self._total   = 1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addStretch()   # leading stretch kept at index 0

        self._layout = layout
        self._render()

    def set_state(self, current_page: int, total_pages: int) -> None:
        self._current = current_page
        self._total   = max(1, total_pages)
        self._render()

    def _render(self) -> None:
        # Remove everything after the leading stretch (index 0)
        while self._layout.count() > 1:
            item = self._layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        prev_btn = QPushButton("← Anterior")
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet(PAGE_BTN_NORMAL)
        prev_btn.setEnabled(self._current > 0)
        prev_btn.clicked.connect(lambda: self.page_requested.emit(self._current - 1))
        self._layout.addWidget(prev_btn)

        # Up to 5 page numbers centered on the current page
        start = max(0, self._current - 2)
        end   = min(self._total, start + 5)
        start = max(0, end - 5)
        for p in range(start, end):
            btn = QPushButton(str(p + 1))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(PAGE_BTN_ACTIVE if p == self._current else PAGE_BTN_NORMAL)
            btn.clicked.connect(lambda _, pg=p: self.page_requested.emit(pg))
            self._layout.addWidget(btn)

        next_btn = QPushButton("Siguiente →")
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet(PAGE_BTN_NORMAL)
        next_btn.setEnabled(self._current < self._total - 1)
        next_btn.clicked.connect(lambda: self.page_requested.emit(self._current + 1))
        self._layout.addWidget(next_btn)

        self._layout.addStretch()   # trailing stretch
