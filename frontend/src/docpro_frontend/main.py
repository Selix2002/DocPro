import logging
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from docpro_backend.db.profile_context import ProfileContext
from docpro_frontend.dashboard_widget import DashboardWidget
from docpro_frontend.header.dialogs.profile_dialogs import (
    prompt_new_profile,
    prompt_rename_profile,
    show_error as show_profile_error,
)
from docpro_frontend.services import profile_service
from docpro_frontend.services.gmail_service import GmailService
from docpro_frontend.services.profile_bootstrap import bootstrap_profiles, run_migrations
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
        run_migrations()
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

    bootstrap_profiles()
    _run_migrations()

    app = QApplication(sys.argv)
    app.setStyleSheet(_GLOBAL_STYLE)

    window = QMainWindow()
    ctx = ProfileContext.get()

    def _refresh_title() -> None:
        window.setWindowTitle(f"DocPro — {ctx.active_name()}")

    _refresh_title()
    ctx.add_listener(_refresh_title)
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
    settings_svc = SettingsService(settings)
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

    # ── Profile management ────────────────────────────────────────────
    def _refresh_profile_chip() -> None:
        dashboard.profile_chip.set_profiles(
            profile_service.list_profiles(),
            profile_service.active_slug(),
        )

    def _reload_after_switch() -> None:
        settings_svc.load_all()
        dashboard.refresh()
        stack.setCurrentWidget(dashboard)

    def _on_switch_profile(slug: str) -> None:
        if slug == profile_service.active_slug():
            return
        try:
            profile_service.switch_to(slug)
        except Exception as exc:
            logging.getLogger(__name__).exception("Switch profile failed")
            show_profile_error(window, f"No se pudo cambiar de perfil: {exc}")
            return
        _reload_after_switch()

    def _on_new_profile() -> None:
        name = prompt_new_profile(window)
        if not name:
            return
        try:
            profile_service.create_and_activate(name)
        except Exception as exc:
            logging.getLogger(__name__).exception("Create profile failed")
            show_profile_error(window, f"No se pudo crear el perfil: {exc}")
            return
        _reload_after_switch()

    def _on_rename_profile() -> None:
        current_slug = profile_service.active_slug()
        current_name = profile_service.active_name()
        new_name = prompt_rename_profile(window, current_name)
        if not new_name:
            return
        try:
            profile_service.rename(current_slug, new_name)
        except Exception as exc:
            logging.getLogger(__name__).exception("Rename profile failed")
            show_profile_error(window, f"No se pudo renombrar: {exc}")

    dashboard.switch_profile_requested.connect(_on_switch_profile)
    dashboard.new_profile_requested.connect(_on_new_profile)
    dashboard.rename_profile_requested.connect(_on_rename_profile)
    ctx.add_listener(_refresh_profile_chip)
    _refresh_profile_chip()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
