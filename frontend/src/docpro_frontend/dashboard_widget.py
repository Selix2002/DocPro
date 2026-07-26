from PySide6.QtCore import QThreadPool, Signal, Qt
from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QStackedWidget, QWidget

from docpro_frontend.body.views.body_widget import BodyWidget
from docpro_frontend.clients.views.clients_widget import ClientsWidget
from docpro_frontend.header.views.header_widget import HeaderWidget
from docpro_frontend.history.views.history_widget import HistoryWidget
from docpro_frontend.services.clients_service import (
    ClientsService, _create_client, _delete_client, _update_client,
)
from docpro_frontend.services.dashboard_service import DashboardService
from docpro_frontend.services.history_service import HistorialService
from docpro_frontend.services.worker import Worker

_IDX_BODY    = 0
_IDX_HISTORY = 1
_IDX_CLIENTS = 2

_DLG_STYLE = """
QMessageBox          { background: #FFFFFF; }
QMessageBox QLabel   { color: #111827; background: transparent; }
QPushButton {
    background: #F3F4F6; color: #111827;
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 6px 20px; font-size: 15px;
}
QPushButton:hover    { background: #E5E7EB; }
QPushButton:default  { background: #EF4444; color: #FFFFFF; border-color: #EF4444; }
QPushButton:default:hover { background: #DC2626; }
"""


class DashboardWidget(QWidget):
    tab_changed             = Signal(str)
    new_quote_requested          = Signal()
    create_quote_for_client      = Signal(int)   # client_id
    new_report_requested    = Signal()
    import_pdf_requested    = Signal()
    settings_requested      = Signal()
    search_changed          = Signal(str)
    document_opened         = Signal(int, str)  # doc_id, doc_type
    create_quote_requested  = Signal()
    create_report_requested = Signal()
    draft_opened            = Signal(int, str)  # doc_id, doc_type
    new_client_requested    = Signal()
    switch_profile_requested = Signal(str)
    new_profile_requested   = Signal()
    rename_profile_requested = Signal()

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

        # ── Header signals ────────────────────────────────────────────────
        self._header.tab_changed.connect(self._on_tab_changed)
        self._header.new_quote_requested.connect(self.new_quote_requested)
        self._header.new_report_requested.connect(self.new_report_requested)
        self._header.import_pdf_requested.connect(self.import_pdf_requested)
        self._header.settings_requested.connect(self.settings_requested)
        self._header.search_changed.connect(self.search_changed)
        self._header.switch_profile_requested.connect(self.switch_profile_requested)
        self._header.new_profile_requested.connect(self.new_profile_requested)
        self._header.rename_profile_requested.connect(self.rename_profile_requested)

        # ── Body signals ──────────────────────────────────────────────────
        self._body.document_opened.connect(self.document_opened)
        self._body.create_quote_requested.connect(self.create_quote_requested)
        self._body.create_report_requested.connect(self.create_report_requested)
        self._body.draft_opened.connect(self.draft_opened)

        # ── History signals ───────────────────────────────────────────────
        self._history_wgt.document_opened.connect(self.document_opened)
        self._history_wgt.filter_changed.connect(self._on_history_filter_changed)
        self._history_wgt.page_changed.connect(self._on_history_page_changed)

        # ── Clients signals ───────────────────────────────────────────────
        self._clients_wgt.filter_changed.connect(self._on_clients_filter_changed)
        self._clients_wgt.page_changed.connect(self._on_clients_page_changed)
        self._clients_wgt.new_document_requested.connect(self.create_quote_for_client)
        self._clients_wgt.new_client_requested.connect(self._on_new_client)
        self._clients_wgt.delete_requested.connect(self._on_client_delete)
        self._clients_wgt.edit_requested.connect(self._on_client_edit)

        self._search_initialized = False

        # ── Services ──────────────────────────────────────────────────────
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

    # ── Public ────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        self._service.load()

    @property
    def profile_chip(self):
        return self._header.profile_chip

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._search_initialized:
            self._search_initialized = True
            self._init_search()

    def _init_search(self) -> None:
        from docpro_frontend.header.widgets.search_dropdown import SearchDropdown
        from docpro_frontend.services.search_service import SearchService

        self._search_svc  = SearchService(self)
        self._search_drop = SearchDropdown(self.window(), self._header.search_field)

        self._header.search_changed.connect(self._search_svc.search)
        self._header.filter_changed.connect(self._search_svc.set_filters)
        self._search_svc.results_ready.connect(self._search_drop.show_results)
        self._search_drop.result_selected.connect(self.document_opened)

    # ── Tab routing ───────────────────────────────────────────────────────

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

    # ── History handlers ──────────────────────────────────────────────────

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

    # ── Clients list handlers ─────────────────────────────────────────────

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

    # ── Client CRUD ───────────────────────────────────────────────────────

    def _on_new_client(self) -> None:
        from docpro_frontend.clients.views.client_form_dialog import ClientFormDialog
        dlg = ClientFormDialog(parent=self)
        dlg.saved.connect(self._do_create_client)
        dlg.exec()

    def _do_create_client(self, data: dict) -> None:
        worker = Worker(lambda: _create_client(data))
        worker.signals.result.connect(self._on_client_mutated)
        worker.signals.error.connect(self._on_client_mutation_error)
        QThreadPool.globalInstance().start(worker)

    def _on_client_edit(self, client_id: int, data: dict) -> None:
        from docpro_frontend.clients.views.client_form_dialog import ClientFormDialog
        dlg = ClientFormDialog(client_id=client_id, data=data, parent=self)
        dlg.saved.connect(self._do_update_client)
        dlg.exec()

    def _do_update_client(self, data: dict) -> None:
        client_id = data.pop("client_id")
        worker = Worker(lambda: _update_client(client_id, data))
        worker.signals.result.connect(self._on_client_mutated)
        worker.signals.error.connect(self._on_client_mutation_error)
        QThreadPool.globalInstance().start(worker)

    def _on_client_delete(self, client_id: int, name: str) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Eliminar cliente")
        dlg.setText(f'¿Eliminar a "{name}"?')
        dlg.setInformativeText(
            "Esta acción es permanente y no se puede deshacer.\n"
            "Solo se puede eliminar un cliente sin documentos asociados."
        )
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setStyleSheet(_DLG_STYLE)
        confirm = dlg.addButton("Eliminar", QMessageBox.ButtonRole.DestructiveRole)
        dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dlg.setDefaultButton(confirm)
        dlg.exec()
        if dlg.clickedButton() is not confirm:
            return

        worker = Worker(lambda: _delete_client(client_id))
        worker.signals.result.connect(self._on_client_mutated)
        worker.signals.error.connect(self._on_client_mutation_error)
        QThreadPool.globalInstance().start(worker)

    def _on_client_mutated(self, _) -> None:
        self._clients_wgt.set_loading(True)
        self._clients_service.load(page=self._clients_page, **self._clients_params)

    def _on_client_mutation_error(self, message: str) -> None:
        dlg = QMessageBox(self)
        dlg.setWindowTitle("No se pudo completar la operación")
        dlg.setText(message[:300])
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setStyleSheet(_DLG_STYLE.replace(
            "background: #EF4444; color: #FFFFFF; border-color: #EF4444;",
            "background: #B45309; color: #FFFFFF; border-color: #B45309;",
        ))
        dlg.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        dlg.exec()

    # ── Dashboard handlers ────────────────────────────────────────────────

    def _on_data_loaded(self, data) -> None:
        t = data["totales"]
        self._body.set_totals(t["cotizaciones"], t["informes"], t["clientes"], t["docs_total"])
        self._body.set_month_summary(data["resumen_mes"])
        self._body.set_recent_documents(data["documentos_recientes"])
        self._body.set_drafts(data["borradores"])
        self._body.set_next_numbers(data["siguiente_cot"], data["siguiente_inf"])

    def _on_error(self, message: str) -> None:
        print(f"[dashboard] error cargando datos: {message}")
