from PySide6.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PySide6.QtCore import Signal, Qt

from docpro_frontend.report.views.report_header import ReportHeader
from docpro_frontend.report.views.report_form import ReportForm
from docpro_frontend.report.views.preview_panel import PreviewPanel


class ReportWidget(QWidget):
    """
    Full-screen report editor.
    Layout: ReportHeader (60px) + QSplitter(ReportForm | PreviewPanel).
    """

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._header  = ReportHeader()
        self._form    = ReportForm()
        self._preview = PreviewPanel()

        root.addWidget(self._header)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(12)
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background: #E5E7EB;
            }
            QSplitter::handle:hover {
                background: #1D4ED8;
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
    def header(self) -> ReportHeader:
        return self._header

    @property
    def form(self) -> ReportForm:
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
