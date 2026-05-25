from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt

from docpro_frontend.settings.styles import settings_styles as S
from docpro_frontend.settings.widgets.card_section import CardSection
from docpro_frontend.settings.views.company_profile_form import CompanyProfileForm
from docpro_frontend.settings.views.numbering_form import NumberingForm
from docpro_frontend.settings.views.appearance_form import AppearanceForm
from docpro_frontend.settings.views.gmail_form import GmailForm
from docpro_frontend.settings.views.groq_form import GroqForm
from docpro_frontend.settings.views.backup_form import BackupForm


# Single source of truth for section metadata, shared with SidebarWidget
SECTION_META: dict[str, dict] = {
    "perfil": {
        "icon": "🏢", "color": "amber",
        "name": "Perfil de empresa",
        "subtitle": "Se usan para autocompletar encabezados de cotizaciones e informes",
        "page_sub": "Estos datos aparecen en el encabezado de todos los documentos generados.",
        "status_text": "", "status_state": "",
    },
    "numeracion": {
        "icon": "#", "color": "blue",
        "name": "Numeración",
        "subtitle": "Prefijos y contadores de inicio para cada tipo de documento",
        "page_sub": "Configura los prefijos y el número inicial para cotizaciones e informes.",
        "status_text": "", "status_state": "",
    },
    "apariencia": {
        "icon": "☀", "color": "gray",
        "name": "Apariencia",
        "subtitle": "Tema de la interfaz — se aplica en tiempo real",
        "page_sub": "Elige entre modo claro, oscuro o seguir la configuración de Windows.",
        "status_text": "", "status_state": "",
    },
    "gmail": {
        "icon": "@", "color": "green",
        "name": "Gmail",
        "subtitle": "Integración OAuth 2.0 para envío de correos con documentos adjuntos",
        "page_sub": "Vincula una cuenta de Gmail para enviar cotizaciones e informes directamente.",
        "status_text": "Desconectado", "status_state": "off",
    },
    "groq": {
        "icon": "✦", "color": "purple",
        "name": "Inteligencia artificial · Groq",
        "subtitle": "API key para mejora de redacción en documentos",
        "page_sub": "Activa el asistente de redacción con Groq para todos los campos de texto libre.",
        "status_text": "Sin validar", "status_state": "warn",
    },
    "backup": {
        "icon": "💾", "color": "gray",
        "name": "Backup y restauración",
        "subtitle": "Exportar o restaurar la base de datos SQLite local",
        "page_sub": "Haz una copia de seguridad de todos tus datos o restaura desde un archivo previo.",
        "status_text": "", "status_state": "",
    },
}

_ORDER = ["perfil", "numeracion", "apariencia", "gmail", "groq", "backup"]


class ContentArea(QWidget):
    """
    Main scrollable content area (Propuesta A).
    Page-head (title + subtitle) + stacked CardSection instances,
    one per settings section, each wrapping a form view.
    Clicking a sidebar item calls show_section(key) to scroll and update
    the page-head.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ContentArea")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.content_area())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}")

        content = QWidget()
        content.setObjectName("ContentScroll")
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content.setStyleSheet(S.content_scroll())
        self._scroll.setWidget(content)

        inner = QVBoxLayout(content)
        inner.setContentsMargins(32, 28, 32, 28)
        inner.setSpacing(0)

        # Page head
        self._page_title = QLabel()
        self._page_title.setStyleSheet(S.page_head_title())
        self._page_sub = QLabel()
        self._page_sub.setStyleSheet(S.page_head_sub())
        self._page_sub.setWordWrap(True)

        inner.addWidget(self._page_title)
        inner.addSpacing(4)
        inner.addWidget(self._page_sub)
        inner.addSpacing(24)

        # Build form views
        self._company    = CompanyProfileForm()
        self._numbering  = NumberingForm()
        self._appearance = AppearanceForm()
        self._gmail      = GmailForm()
        self._groq       = GroqForm()
        self._backup     = BackupForm()

        _forms: dict[str, QWidget] = {
            "perfil":     self._company,
            "numeracion": self._numbering,
            "apariencia": self._appearance,
            "gmail":      self._gmail,
            "groq":       self._groq,
            "backup":     self._backup,
        }

        self._cards: dict[str, CardSection] = {}
        for key in _ORDER:
            meta = SECTION_META[key]
            card = CardSection(
                icon=meta["icon"],
                color=meta["color"],
                title=meta["name"],
                subtitle=meta["subtitle"],
                status_text=meta["status_text"],
                status_state=meta["status_state"],
            )
            card.set_form(_forms[key])
            inner.addWidget(card)
            inner.addSpacing(16)
            self._cards[key] = card

        inner.addStretch()
        outer.addWidget(self._scroll)

        self.show_section("perfil")

    # ── Public ────────────────────────────────────────────────────────

    def show_section(self, key: str) -> None:
        meta = SECTION_META.get(key)
        if not meta:
            return
        self._page_title.setText(meta["name"])
        self._page_sub.setText(meta["page_sub"])
        card = self._cards.get(key)
        if card:
            self._scroll.ensureWidgetVisible(card)

    def update_card_status(self, key: str, text: str, state: str) -> None:
        if key in self._cards:
            self._cards[key].update_status(text, state)

    # ── Form property accessors (for future service wiring) ───────────

    @property
    def company_form(self) -> CompanyProfileForm:
        return self._company

    @property
    def numbering_form(self) -> NumberingForm:
        return self._numbering

    @property
    def appearance_form(self) -> AppearanceForm:
        return self._appearance

    @property
    def gmail_form(self) -> GmailForm:
        return self._gmail

    @property
    def groq_form(self) -> GroqForm:
        return self._groq

    @property
    def backup_form(self) -> BackupForm:
        return self._backup
