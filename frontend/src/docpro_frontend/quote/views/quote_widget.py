from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Signal, Qt

from docpro_frontend.quote.views.quote_header import QuoteHeader
from docpro_frontend.quote.views.quote_form import QuoteForm
from docpro_frontend.quote.views.preview_panel import PreviewPanel


class QuoteWidget(QWidget):
    """
    Full-screen quote editor.
    Layout: QuoteHeader (60px) + QSplitter(QuoteForm | PreviewPanel).
    The splitter gives an Overleaf-style draggable resize between form and preview.
    back_requested is relayed from QuoteHeader for main.py wiring.
    """

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header  = QuoteHeader()
        self._form    = QuoteForm()
        self._preview = PreviewPanel()

        root.addWidget(self._header)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(12)
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background: #E5E7EB;
            }
            QSplitter::handle:hover {
                background: #B45309;
            }
        """)
        self._splitter.addWidget(self._form)
        self._splitter.addWidget(self._preview)
        self._splitter.setSizes([700, 360])
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, True)

        root.addWidget(self._splitter, 1)

        self._header.back_requested.connect(self.back_requested)
        self._preview.collapse_toggled.connect(self._on_preview_collapse)

    # ── Public ────────────────────────────────────────────────────────────────

    @property
    def header(self) -> QuoteHeader:
        return self._header

    @property
    def form(self) -> QuoteForm:
        return self._form

    @property
    def preview(self) -> PreviewPanel:
        return self._preview

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_preview_collapse(self, collapsed: bool) -> None:
        if collapsed:
            self._splitter.setSizes([10000, 0])
        else:
            self._splitter.setSizes([700, 360])
