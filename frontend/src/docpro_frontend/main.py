import logging
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from docpro_backend.db.engine import get_db_path
from docpro_frontend.dashboard_widget import DashboardWidget
from docpro_frontend.services.gmail_service import GmailService
from docpro_frontend.services.settings_service import SettingsService
from docpro_frontend.services.quote_service import QuoteService
from docpro_frontend.services.report_service import ReportService
from docpro_frontend.settings.views.settings_widget import SettingsWidget
from docpro_frontend.quote.views.quote_widget import QuoteWidget
from docpro_frontend.report.views.report_widget import ReportWidget

_GLOBAL_STYLE = """
* {
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 20px;
    color: #111827;
}
QMainWindow {
    background: #FAFAFA;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: #F3F4F6;
    width: 9px;
    border-radius: 5px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #D1D5DB;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0; border: none; }
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical { background: none; }
"""


def _is_debug_mode() -> bool:
    if "--debug" in sys.argv:
        return True
    if getattr(sys, "frozen", False):
        return Path(sys.executable).stem.lower().endswith("-debug")
    return False


def _setup_logging() -> None:
    log_dir = Path(os.environ.get("APPDATA", Path.home())) / "DocPro"
    log_dir.mkdir(parents=True, exist_ok=True)

    debug = _is_debug_mode()
    level = logging.DEBUG if debug else logging.WARNING
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"

    handlers: list[logging.Handler] = [
        logging.FileHandler(log_dir / "docpro.log", encoding="utf-8"),
    ]
    if debug:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(level=level, format=fmt, handlers=handlers)
    if debug:
        logging.getLogger(__name__).info("Debug mode activo — logs visibles en consola")


def _run_migrations() -> None:
    """Apply pending Alembic migrations at startup — safe to call on every launch."""
    try:
        from alembic import command as alembic_command
        from alembic.config import Config
        from docpro_backend.db.engine import get_db_path

        if getattr(sys, "frozen", False):
            # In the frozen bundle: alembic.ini and alembic/ land at sys._MEIPASS
            meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
            ini_path = meipass / "alembic.ini"
            script_loc = str(meipass / "alembic")
        else:
            # Dev layout: backend/alembic.ini, backend/alembic/
            repo_root = Path(__file__).resolve().parents[3]
            ini_path = repo_root / "backend" / "alembic.ini"
            script_loc = str(ini_path.parent / "alembic")

        cfg = Config(str(ini_path))
        cfg.set_main_option("script_location", script_loc)
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{get_db_path()}")
        alembic_command.upgrade(cfg, "head")
    except Exception:
        logging.getLogger(__name__).exception("Alembic migration failed")
        raise


def main() -> None:
    _setup_logging()

    if not getattr(sys, "frozen", False):
        import hupper
        hupper.start_reloader("docpro_frontend.main.main")
        # parent process blocks here monitoring for file changes;
        # worker process returns immediately and falls through below

    _run_migrations()

    DB_PATH = get_db_path()

    app = QApplication(sys.argv)
    app.setStyleSheet(_GLOBAL_STYLE)

    window = QMainWindow()
    window.setWindowTitle("DocPro")
    window.resize(1280, 800)
    window.setMinimumSize(960, 600)

    stack = QStackedWidget()
    dashboard  = DashboardWidget()
    settings   = SettingsWidget()
    quote_wgt  = QuoteWidget()
    report_wgt = ReportWidget()

    stack.addWidget(dashboard)
    stack.addWidget(settings)
    stack.addWidget(quote_wgt)
    stack.addWidget(report_wgt)
    stack.setCurrentWidget(dashboard)
    window.setCentralWidget(stack)

    gmail_svc    = GmailService()
    settings_svc = SettingsService(settings, DB_PATH)
    settings_svc.load_all()

    quote_svc  = QuoteService(quote_wgt, gmail_svc)
    report_svc = ReportService(report_wgt, gmail_svc)

    def go_to_settings():
        settings_svc.load_all()
        stack.setCurrentWidget(settings)

    def go_to_dashboard():
        dashboard.refresh()
        stack.setCurrentWidget(dashboard)

    def open_new_quote():
        quote_svc.open_new()
        stack.setCurrentWidget(quote_wgt)

    def open_new_quote_for_client(client_id: int):
        quote_svc.open_new_for_client(client_id)
        stack.setCurrentWidget(quote_wgt)

    def open_existing_quote(doc_id: int):
        quote_svc.open_existing(doc_id)
        stack.setCurrentWidget(quote_wgt)

    def open_new_report():
        report_svc.open_new()
        stack.setCurrentWidget(report_wgt)

    def open_existing_report(doc_id: int):
        report_svc.open_existing(doc_id)
        stack.setCurrentWidget(report_wgt)

    def back_to_dashboard():
        if settings_svc.has_unsaved_changes():
            from PySide6.QtWidgets import QMessageBox
            dlg = QMessageBox(settings)
            dlg.setWindowTitle("Cambios sin guardar")
            dlg.setText("Hay cambios sin guardar.")
            dlg.setInformativeText("¿Quieres volver al inicio sin guardarlos?")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.setStyleSheet("""
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
            """)
            discard = dlg.addButton("Volver sin guardar", QMessageBox.ButtonRole.DestructiveRole)
            dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            dlg.setDefaultButton(discard)
            dlg.exec()
            if dlg.clickedButton() is not discard:
                return
        go_to_dashboard()

    def open_existing_document(doc_id: int, doc_type: str):
        if doc_type == "inf":
            open_existing_report(doc_id)
        else:
            open_existing_quote(doc_id)

    dashboard.new_quote_requested.connect(open_new_quote)
    dashboard.create_quote_requested.connect(open_new_quote)
    dashboard.create_quote_for_client.connect(open_new_quote_for_client)
    dashboard.draft_opened.connect(open_existing_document)
    dashboard.document_opened.connect(open_existing_document)

    dashboard.settings_requested.connect(go_to_settings)
    settings.back_requested.connect(back_to_dashboard)
    settings.save_requested.connect(go_to_dashboard)

    dashboard.new_report_requested.connect(open_new_report)
    dashboard.create_report_requested.connect(open_new_report)

    quote_svc.navigation_back.connect(go_to_dashboard)
    report_svc.navigation_back.connect(go_to_dashboard)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
