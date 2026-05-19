from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.views.sidebar_widget import SidebarWidget
from docpro_frontend.settings.views.content_area import ContentArea


class SettingsWidget(QWidget):
    """
    Full-screen settings view (Propuesta A).
    Layout: compact header (← Inicio + title + Guardar) + horizontal body
    (SidebarWidget 230 px fixed + ContentArea flex).
    """

    back_requested = Signal()
    save_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = SidebarWidget()
        self._content = ContentArea()

        body.addWidget(self._sidebar)
        body.addWidget(self._content, 1)

        root.addLayout(body, 1)

        self._sidebar.tile_selected.connect(self._content.show_section)
        self._sidebar.tile_selected.connect(self._sidebar.set_active_tile)

    # ── Public ────────────────────────────────────────────────────────

    @property
    def content(self) -> ContentArea:
        return self._content

    @property
    def sidebar(self) -> SidebarWidget:
        return self._sidebar

    # ── Internal ──────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("SettingsHeader")
        header.setFixedHeight(60)
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setStyleSheet(S.settings_header())

        h = QHBoxLayout(header)
        h.setContentsMargins(24, 0, 24, 0)
        h.setSpacing(0)

        back_btn = QPushButton("← Inicio")
        back_btn.setStyleSheet(S.back_btn())
        back_btn.clicked.connect(self.back_requested)

        h.addWidget(back_btn)
        h.addSpacing(20)

        icon_lbl = QLabel("⚙")
        icon_lbl.setStyleSheet(S.header_title_icon())

        title_lbl = QLabel("Configuración")
        title_lbl.setStyleSheet(S.header_title_text())

        h.addWidget(icon_lbl)
        h.addSpacing(10)
        h.addWidget(title_lbl)
        h.addStretch()

        save_btn = QPushButton("Guardar cambios")
        save_btn.setStyleSheet(S.btn_primary())
        save_btn.clicked.connect(self.save_requested)
        h.addWidget(save_btn)

        return header
