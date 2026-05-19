from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from docpro_frontend.header.views.header_widget import HeaderWidget
from docpro_frontend.body.views.body_widget import BodyWidget
from docpro_frontend.services.dashboard_service import DashboardService


class DashboardWidget(QWidget):
    tab_changed = Signal(str)
    new_quote_requested = Signal()
    new_report_requested = Signal()
    import_pdf_requested = Signal()
    settings_requested = Signal()
    search_changed = Signal(str)
    document_opened = Signal(int)
    create_quote_requested = Signal()
    create_report_requested = Signal()
    draft_opened = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = HeaderWidget()
        self._body = BodyWidget()

        layout.addWidget(self._header)
        layout.addWidget(self._body, stretch=1)

        self._header.tab_changed.connect(self.tab_changed)
        self._header.new_quote_requested.connect(self.new_quote_requested)
        self._header.new_report_requested.connect(self.new_report_requested)
        self._header.import_pdf_requested.connect(self.import_pdf_requested)
        self._header.settings_requested.connect(self.settings_requested)
        self._header.search_changed.connect(self.search_changed)

        self._body.document_opened.connect(self.document_opened)
        self._body.create_quote_requested.connect(self.create_quote_requested)
        self._body.create_report_requested.connect(self.create_report_requested)
        self._body.draft_opened.connect(self.draft_opened)

        self._service = DashboardService(self)
        self._service.loaded.connect(self._on_data_loaded)
        self._service.error.connect(self._on_error)
        self._service.load()

    def refresh(self) -> None:
        self._service.load()

    def _on_data_loaded(self, data) -> None:
        t = data["totales"]
        self._body.set_totals(t["cotizaciones"], t["informes"], t["clientes"], t["docs_total"])
        self._body.set_month_summary(data["resumen_mes"])
        self._body.set_recent_documents(data["documentos_recientes"])
        self._body.set_drafts(data["borradores"])
        self._body.set_next_numbers(data["siguiente_cot"], data["siguiente_inf"])

    def _on_error(self, message: str) -> None:
        print(f"[dashboard] error cargando datos: {message}")
