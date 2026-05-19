import sys

import hupper
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from docpro_backend.db.engine import get_db_path
from docpro_frontend.dashboard_widget import DashboardWidget
from docpro_frontend.services.settings_service import SettingsService
from docpro_frontend.settings.views.settings_widget import SettingsWidget

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


def main() -> None:
    hupper.start_reloader("docpro_frontend.main.main")

    DB_PATH = get_db_path()

    app = QApplication(sys.argv)
    app.setStyleSheet(_GLOBAL_STYLE)

    window = QMainWindow()
    window.setWindowTitle("DocPro")
    window.resize(1280, 800)
    window.setMinimumSize(960, 600)

    stack = QStackedWidget()
    dashboard = DashboardWidget()
    settings = SettingsWidget()

    stack.addWidget(dashboard)
    stack.addWidget(settings)
    stack.setCurrentWidget(dashboard)
    window.setCentralWidget(stack)

    dashboard.tab_changed.connect(lambda name: print(f"[nav] tab → {name}"))
    dashboard.new_quote_requested.connect(lambda: print("[nav] nueva cotización"))
    dashboard.new_report_requested.connect(lambda: print("[nav] nuevo informe"))
    dashboard.import_pdf_requested.connect(lambda: print("[nav] importar PDF"))
    dashboard.document_opened.connect(lambda doc_id: print(f"[nav] abrir documento {doc_id}"))
    dashboard.draft_opened.connect(lambda doc_id: print(f"[nav] abrir borrador {doc_id}"))

    settings_svc = SettingsService(settings, DB_PATH)
    settings_svc.load_all()

    def go_to_settings():
        settings_svc.load_all()
        stack.setCurrentWidget(settings)

    def go_to_dashboard():
        dashboard.refresh()
        stack.setCurrentWidget(dashboard)

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

    dashboard.settings_requested.connect(go_to_settings)
    settings.back_requested.connect(back_to_dashboard)
    settings.save_requested.connect(go_to_dashboard)

    window.show()
    sys.exit(app.exec())
