from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PySide6.QtCore import Signal

from docpro_frontend.body.views.body_widget import BodyWidget
from docpro_frontend.clients.views.clients_widget import ClientsWidget
from docpro_frontend.header.views.header_widget import HeaderWidget
from docpro_frontend.history.views.history_widget import HistoryWidget
from docpro_frontend.services.clients_service import ClientsService
from docpro_frontend.services.dashboard_service import DashboardService
from docpro_frontend.services.history_service import HistorialService

_IDX_BODY    = 0
_IDX_HISTORY = 1
_IDX_CLIENTS = 2


class DashboardWidget(QWidget):
    tab_changed             = Signal(str)
    new_quote_requested     = Signal()
    new_report_requested    = Signal()
    import_pdf_requested    = Signal()
    settings_requested      = Signal()
    search_changed          = Signal(str)
    document_opened         = Signal(int, str)  # doc_id, doc_type
    create_quote_requested  = Signal()
    create_report_requested = Signal()
    draft_opened            = Signal(int, str)  # doc_id, doc_type
    new_client_requested    = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._header = HeaderWidget()

        self._body_stack = QStackedWidget()
        self._body        = BodyWidget()
        self._history_wgt = HistoryWidget()
        self._clients_wgt = ClientsWidget()
        self._body_stack.addWidget(self._body)        # _IDX_BODY
        self._body_stack.addWidget(self._history_wgt) # _IDX_HISTORY
        self._body_stack.addWidget(self._clients_wgt) # _IDX_CLIENTS

        layout.addWidget(self._header)
        layout.addWidget(self._body_stack, stretch=1)

        # Header signals
        self._header.tab_changed.connect(self._on_tab_changed)
        self._header.new_quote_requested.connect(self.new_quote_requested)
        self._header.new_report_requested.connect(self.new_report_requested)
        self._header.import_pdf_requested.connect(self.import_pdf_requested)
        self._header.settings_requested.connect(self.settings_requested)
        self._header.search_changed.connect(self.search_changed)

        # Body signals
        self._body.document_opened.connect(self.document_opened)
        self._body.create_quote_requested.connect(self.create_quote_requested)
        self._body.create_report_requested.connect(self.create_report_requested)
        self._body.draft_opened.connect(self.draft_opened)

        # History signals
        self._history_wgt.document_opened.connect(self.document_opened)
        self._history_wgt.filter_changed.connect(self._on_history_filter_changed)
        self._history_wgt.page_changed.connect(self._on_history_page_changed)

        # Clients signals
        self._clients_wgt.filter_changed.connect(self._on_clients_filter_changed)
        self._clients_wgt.page_changed.connect(self._on_clients_page_changed)
        self._clients_wgt.new_document_requested.connect(self.new_quote_requested)
        self._clients_wgt.new_client_requested.connect(self.new_client_requested)

        # Services
        self._service = DashboardService(self)
        self._service.loaded.connect(self._on_data_loaded)
        self._service.error.connect(self._on_error)
        self._service.load()

        self._history_service = HistorialService(self)
        self._history_service.loaded.connect(self._on_history_loaded)
        self._history_service.error.connect(self._on_history_error)

        self._history_params: dict = {
            "search":        "",
            "type_filter":   None,
            "status_filter": None,
            "sort":          "Más reciente",
            "page_size":     5,
        }
        self._history_page: int = 0

        self._clients_service = ClientsService(self)
        self._clients_service.loaded.connect(self._on_clients_loaded)
        self._clients_service.error.connect(self._on_clients_error)

        self._clients_params: dict = {
            "search":    "",
            "sort":      "Más reciente",
            "page_size": 12,
        }
        self._clients_page: int = 0

    # ── public ────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._service.load()

    # ── tab routing ───────────────────────────────────────────────────────

    def _on_tab_changed(self, name: str) -> None:
        if name == "Historial":
            self._body_stack.setCurrentIndex(_IDX_HISTORY)
            self._history_wgt.set_loading(True)
            self._history_page = 0
            self._history_service.load(page=0, **self._history_params)
        elif name == "Clientes":
            self._body_stack.setCurrentIndex(_IDX_CLIENTS)
            self._clients_wgt.set_loading(True)
            self._clients_page = 0
            self._clients_service.load(page=0, **self._clients_params)
        else:
            self._body_stack.setCurrentIndex(_IDX_BODY)
        self.tab_changed.emit(name)

    # ── history handlers ──────────────────────────────────────────────────

    def _on_history_filter_changed(self, params: dict) -> None:
        self._history_params = params
        self._history_page   = 0
        self._history_wgt.set_loading(True)
        self._history_service.load(page=0, **params)

    def _on_history_page_changed(self, page: int) -> None:
        self._history_page = page
        self._history_wgt.set_loading(True)
        self._history_service.load(page=page, **self._history_params)

    def _on_history_loaded(self, data: dict) -> None:
        self._history_wgt.set_data(data)

    def _on_history_error(self, message: str) -> None:
        print(f"[history] error cargando datos: {message}")
        self._history_wgt.set_loading(False)

    # ── clients handlers ──────────────────────────────────────────────────

    def _on_clients_filter_changed(self, params: dict) -> None:
        self._clients_params = params
        self._clients_page   = 0
        self._clients_wgt.set_loading(True)
        self._clients_service.load(page=0, **params)

    def _on_clients_page_changed(self, page: int) -> None:
        self._clients_page = page
        self._clients_wgt.set_loading(True)
        self._clients_service.load(page=page, **self._clients_params)

    def _on_clients_loaded(self, data: dict) -> None:
        self._clients_wgt.set_data(data)

    def _on_clients_error(self, message: str) -> None:
        print(f"[clients] error cargando datos: {message}")
        self._clients_wgt.set_loading(False)

    # ── dashboard handlers ────────────────────────────────────────────────

    def _on_data_loaded(self, data) -> None:
        t = data["totales"]
        self._body.set_totals(t["cotizaciones"], t["informes"], t["clientes"], t["docs_total"])
        self._body.set_month_summary(data["resumen_mes"])
        self._body.set_recent_documents(data["documentos_recientes"])
        self._body.set_drafts(data["borradores"])
        self._body.set_next_numbers(data["siguiente_cot"], data["siguiente_inf"])

    def _on_error(self, message: str) -> None:
        print(f"[dashboard] error cargando datos: {message}")
