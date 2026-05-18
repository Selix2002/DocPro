from PySide6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal, Qt

from docpro_frontend.body.views.greeting_widget import GreetingWidget
from docpro_frontend.body.views.create_section import CreateSection
from docpro_frontend.body.views.month_summary_section import MonthSummarySection
from docpro_frontend.body.views.recent_documents_section import RecentDocumentsSection
from docpro_frontend.body.views.totals_section import TotalsSection
from docpro_frontend.body.views.drafts_section import DraftsPendingSection


class BodyWidget(QWidget):
    create_quote_requested = Signal()
    create_report_requested = Signal()
    document_opened = Signal(int)
    draft_opened = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("BodyContent")
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content.setStyleSheet("QWidget#BodyContent { background: #FAFAFA; }")
        scroll.setWidget(content)

        inner = QVBoxLayout(content)
        inner.setContentsMargins(36, 36, 36, 36)
        inner.setSpacing(0)

        self._greeting = GreetingWidget()
        inner.addWidget(self._greeting)
        inner.addSpacing(36)

        grid = QHBoxLayout()
        grid.setSpacing(24)
        grid.setContentsMargins(0, 0, 0, 0)
        inner.addLayout(grid)

        # Column 1
        col1 = QVBoxLayout()
        col1.setSpacing(0)
        self._create_section = CreateSection()
        self._month_summary = MonthSummarySection()
        col1.addWidget(self._create_section)
        col1.addSpacing(24)
        col1.addWidget(self._month_summary)
        col1.addStretch()
        grid.addLayout(col1, stretch=1)

        # Column 2
        col2 = QVBoxLayout()
        col2.setSpacing(0)
        self._recent_docs = RecentDocumentsSection()
        col2.addWidget(self._recent_docs)
        col2.addStretch()
        grid.addLayout(col2, stretch=1)

        # Column 3 — fixed width (280 × 1.5 = 420)
        col3 = QWidget()
        col3.setFixedWidth(420)
        col3_layout = QVBoxLayout(col3)
        col3_layout.setContentsMargins(0, 0, 0, 0)
        col3_layout.setSpacing(0)
        self._totals = TotalsSection()
        self._drafts = DraftsPendingSection()
        col3_layout.addWidget(self._totals)
        col3_layout.addSpacing(24)
        col3_layout.addWidget(self._drafts)
        col3_layout.addStretch()
        grid.addWidget(col3)

        self._create_section.create_quote_requested.connect(self.create_quote_requested)
        self._create_section.create_report_requested.connect(self.create_report_requested)
        self._recent_docs.document_opened.connect(self.document_opened)
        self._drafts.draft_opened.connect(self.draft_opened)

    def set_draft_count(self, count: int) -> None:
        self._greeting.set_draft_count(count)

    def set_totals(
        self,
        cotizaciones: int,
        informes: int,
        clientes: int,
        docs_total: int,
    ) -> None:
        self._totals.set_data(cotizaciones, informes, clientes, docs_total)

    def set_month_summary(self, data: dict) -> None:
        self._month_summary.set_data(data)

    def set_recent_documents(self, docs: list[dict]) -> None:
        self._recent_docs.set_documents(docs)

    def set_drafts(self, drafts: list[dict]) -> None:
        self._drafts.set_drafts(drafts)
        self._greeting.set_draft_count(len(drafts))

    def set_next_numbers(self, next_quote: str, next_report: str) -> None:
        self._create_section.set_next_numbers(next_quote, next_report)
