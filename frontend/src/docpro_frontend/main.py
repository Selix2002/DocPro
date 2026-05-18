import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from docpro_frontend.dashboard_widget import DashboardWidget

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
    app = QApplication(sys.argv)
    app.setStyleSheet(_GLOBAL_STYLE)

    window = QMainWindow()
    window.setWindowTitle("DocPro")
    window.resize(1280, 800)
    window.setMinimumSize(960, 600)

    dashboard = DashboardWidget()
    window.setCentralWidget(dashboard)

    dashboard.tab_changed.connect(lambda name: print(f"[nav] tab → {name}"))
    dashboard.new_quote_requested.connect(lambda: print("[nav] nueva cotización"))
    dashboard.new_report_requested.connect(lambda: print("[nav] nuevo informe"))
    dashboard.import_pdf_requested.connect(lambda: print("[nav] importar PDF"))
    dashboard.settings_requested.connect(lambda: print("[nav] ajustes"))
    dashboard.document_opened.connect(lambda doc_id: print(f"[nav] abrir documento {doc_id}"))
    dashboard.draft_opened.connect(lambda doc_id: print(f"[nav] abrir borrador {doc_id}"))

    window.show()
    sys.exit(app.exec())
