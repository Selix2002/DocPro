from datetime import date

from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel,
    QDateEdit, QFrame, QSizePolicy, QLineEdit, QCheckBox, QPushButton,
)
from PySide6.QtCore import Signal, Qt, QDate, QThreadPool

from docpro_frontend.quote.styles import quote_styles as S
from docpro_frontend.quote.views.client_section import ClientSection
from docpro_frontend.quote.views.items_table import ItemsTable
from docpro_frontend.quote.views.obs_subsection_card import ObsSubsectionCard
from docpro_frontend.services.worker import Worker


class QuoteForm(QWidget):
    """
    Left scrollable panel: meta-row + client section + items table + observations.
    Signals:
        field_changed       — any tracked field changed (drives autosave timer)
        rut_entered(rut)    — relayed from ClientSection
    Methods:
        get_data() -> dict
        set_data(quote_rm)
        set_readonly(bool)
        reset()
    """

    field_changed = Signal()
    rut_entered   = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FormPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.form_panel())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        content.setObjectName("FormScrollContent")
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content.setStyleSheet("QWidget#FormScrollContent { background: #FFFFFF; }")
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        scroll.setWidget(content)

        inner = QVBoxLayout(content)
        inner.setContentsMargins(28, 24, 28, 32)
        inner.setSpacing(12)

        # Meta row
        inner.addWidget(self._build_meta_row())

        # Client section
        self._client = ClientSection()
        inner.addWidget(self._client)

        # Items table (inside a section block)
        inner.addWidget(self._build_items_section())

        # Observations
        inner.addWidget(self._build_obs_section())

        inner.addStretch()

        # Signal relay
        self._client.rut_entered.connect(self.rut_entered)

        # field_changed wiring
        self._issue_date.dateChanged.connect(lambda _: self.field_changed.emit())

        # Load company profile asynchronously
        worker = Worker(_load_company)
        worker.signals.result.connect(self._on_company_loaded)
        QThreadPool.globalInstance().start(worker)
        self._items_table.data_changed.connect(self.field_changed)
        self._client.client_data_changed.connect(self.field_changed)
        self._iva_toggle.toggled.connect(self._on_iva_toggled)

    def _on_company_loaded(self, data: dict) -> None:
        if not data:
            return
        self._company_name_lbl.setText(data.get("name", ""))
        parts = [p for p in (data.get("phone"), data.get("email")) if p]
        self._company_detail_lbl.setText("  ·  ".join(parts))

    # ── Public API ────────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        subs = [c.get_data() for c in self._obs_cards]
        non_empty = [s for s in subs if _sub_has_content(s)] or None
        return {
            "number":            self._number_input.text().strip(),
            "issue_date":        self._issue_date.date().toString("yyyy-MM-dd"),
            "observations_json": non_empty,
            "show_iva":          self._iva_toggle.isChecked(),
            "items":             self._items_table.get_data(),
        }

    def set_data(self, rm) -> None:
        """Populate form from a QuoteReadModel."""
        # Issue date
        try:
            y, m, d = rm.issue_date.split("-")
            self._issue_date.setDate(QDate(int(y), int(m), int(d)))
        except (ValueError, AttributeError):
            self._issue_date.setDate(QDate.currentDate())

        # Client fields
        self._client.set_rut(rm.client_rut)
        self._client.fill_client(
            name=rm.client_name,
            address=rm.client_address,
            email=rm.client_email,
            phone=rm.client_phone,
        )

        # Items
        self._items_table.set_data([
            {
                "position":    i.position,
                "quantity":    i.quantity,
                "description": i.description,
                "unit_price":  i.unit_price,
                "subtotal":    i.subtotal,
            }
            for i in rm.items
        ])

        # IVA toggle
        self._iva_toggle.setChecked(getattr(rm, "show_iva", True))

        # Observations
        self._clear_obs_cards()
        if rm.observations_json:
            for sub in rm.observations_json:
                self._add_obs_card(
                    title    = sub.get("title", ""),
                    content  = sub.get("content", ""),
                    children = sub.get("children"),
                )
        elif rm.observations:
            self._add_obs_card(content=rm.observations)

    def set_number(self, number: str) -> None:
        self._number_input.setText(number)

    def lock_number(self) -> None:
        """Called after the document is created in DB — number can no longer change."""
        self._number_input.setReadOnly(True)

    def set_readonly(self, readonly: bool) -> None:
        # _number_input editability is managed only by lock_number() and reset()
        self._issue_date.setEnabled(not readonly)
        self._client.set_readonly(readonly)
        self._items_table.set_readonly(readonly)
        self._iva_toggle.setEnabled(not readonly)
        for card in self._obs_cards:
            card.set_readonly(readonly)
        self._obs_add_btn.setVisible(not readonly)

    def reset(self) -> None:
        self._number_input.clear()
        self._number_input.setReadOnly(False)
        self._issue_date.setDate(QDate.currentDate())
        self._client.reset()
        self._items_table.clear()
        self._clear_obs_cards()
        self._iva_toggle.setChecked(True)

    def get_client_data(self) -> dict:
        return self._client.get_client_data()

    def _on_iva_toggled(self, checked: bool) -> None:
        self._items_table.set_show_iva(checked)
        self.field_changed.emit()

    @property
    def client_section(self) -> ClientSection:
        return self._client

    # ── Internal builders ─────────────────────────────────────────────────────

    def _build_meta_row(self) -> QWidget:
        row = QWidget()
        row.setObjectName("MetaRow")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setStyleSheet(S.meta_row())
        row.setFixedHeight(58)

        h = QHBoxLayout(row)
        h.setContentsMargins(20, 0, 20, 0)
        h.setSpacing(0)

        # N° Cotización (editable before creation, read-only after)
        num_lbl = QLabel("N° COTIZACIÓN")
        num_lbl.setStyleSheet(S.meta_label())

        self._number_input = QLineEdit()
        self._number_input.setPlaceholderText("COT-0001")
        self._number_input.setFixedWidth(110)
        self._number_input.setStyleSheet(S.meta_number_input())

        num_wrap = QHBoxLayout()
        num_wrap.setSpacing(8)
        num_wrap.addWidget(num_lbl)
        num_wrap.addWidget(self._number_input)
        h.addLayout(num_wrap)

        # Separator with explicit spacing
        h.addSpacing(20)
        sep = QLabel()
        sep.setFixedSize(1, 24)
        sep.setStyleSheet("background: #E5E7EB;")
        h.addWidget(sep)
        h.addSpacing(20)

        # Fecha emisión
        date_lbl = QLabel("FECHA DE EMISIÓN")
        date_lbl.setStyleSheet(S.meta_label())

        self._issue_date = QDateEdit()
        self._issue_date.setDate(QDate.currentDate())
        self._issue_date.setCalendarPopup(True)
        self._issue_date.setDisplayFormat("dd/MM/yyyy")
        self._issue_date.setStyleSheet(S.date_edit())
        self._issue_date.setFixedWidth(140)

        date_wrap = QHBoxLayout()
        date_wrap.setSpacing(8)
        date_wrap.addWidget(date_lbl)
        date_wrap.addWidget(self._issue_date)
        h.addLayout(date_wrap)

        h.addStretch()

        # Company info block (populated async)
        self._company_name_lbl = QLabel("")
        self._company_name_lbl.setStyleSheet(S.meta_company_name())
        self._company_detail_lbl = QLabel("")
        self._company_detail_lbl.setStyleSheet(S.meta_company_detail())

        company_block = QVBoxLayout()
        company_block.setSpacing(2)
        company_block.setContentsMargins(0, 0, 0, 0)
        company_block.addWidget(self._company_name_lbl)
        company_block.addWidget(self._company_detail_lbl)
        h.addLayout(company_block)

        return row

    def _build_items_section(self) -> QFrame:
        block = QFrame()
        block.setObjectName("SectionBlock")
        block.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        block.setStyleSheet(S.section_block())

        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Section head
        head = QWidget()
        head.setObjectName("SectionHead")
        head.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        head.setStyleSheet(S.section_head())
        head.setFixedHeight(46)

        h = QHBoxLayout(head)
        h.setContentsMargins(20, 0, 20, 0)
        icon = QLabel("☰")
        icon.setStyleSheet(S.section_head_icon())
        label = QLabel("Ítems")
        label.setStyleSheet(S.section_head_label())
        h.addWidget(icon)
        h.addSpacing(8)
        h.addWidget(label)
        h.addStretch()

        self._iva_toggle = QCheckBox("Incluir IVA (19%)")
        self._iva_toggle.setChecked(True)
        self._iva_toggle.setStyleSheet("""
            QCheckBox { font-size: 13px; color: #374151; spacing: 6px; }
            QCheckBox::indicator {
                width: 15px; height: 15px;
                border-radius: 3px; border: 1.5px solid #D1D5DB; background: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background: #B45309; border-color: #B45309;
            }
            QCheckBox:disabled { color: #9CA3AF; }
        """)
        h.addWidget(self._iva_toggle)
        h.addSpacing(4)
        layout.addWidget(head)

        # Items table (owns totals bar internally)
        self._items_table = ItemsTable()
        layout.addWidget(self._items_table)

        return block

    def _build_obs_section(self) -> QFrame:
        block = QFrame()
        block.setObjectName("SectionBlock")
        block.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        block.setStyleSheet(S.section_block())

        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Section head
        head = QWidget()
        head.setObjectName("SectionHead")
        head.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        head.setStyleSheet(S.section_head())
        head.setFixedHeight(46)

        h = QHBoxLayout(head)
        h.setContentsMargins(20, 0, 20, 0)
        icon = QLabel("📝")
        icon.setStyleSheet(S.section_head_icon())
        sec_label = QLabel("Observaciones")
        sec_label.setStyleSheet(S.section_head_label())
        h.addWidget(icon)
        h.addSpacing(8)
        h.addWidget(sec_label)
        h.addStretch()
        layout.addWidget(head)

        # Cards container
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(16, 12, 16, 0)
        body_layout.setSpacing(8)

        self._obs_cards: list[ObsSubsectionCard] = []
        self._obs_body_layout = body_layout
        layout.addWidget(body)

        # "Add subsection" button
        self._obs_add_btn = QPushButton("＋  Añadir subsección")
        self._obs_add_btn.setStyleSheet(S.obs_add_sub_btn())
        self._obs_add_btn.clicked.connect(lambda: self._add_obs_card())
        layout.addWidget(self._obs_add_btn)

        return block

    # ── Observations helpers ──────────────────────────────────────────────────

    def _add_obs_card(
        self,
        title: str = "",
        content: str = "",
        children: list | None = None,
    ) -> None:
        number = str(len(self._obs_cards) + 1)
        card   = ObsSubsectionCard(number, depth=0, title=title, content=content)
        card.data_changed.connect(self.field_changed)
        card.delete_requested.connect(lambda: self._remove_obs_card(card))
        if children:
            card.load_children(children)
        self._obs_body_layout.addWidget(card)
        self._obs_cards.append(card)

    def _remove_obs_card(self, card: ObsSubsectionCard) -> None:
        self._obs_body_layout.removeWidget(card)
        self._obs_cards.remove(card)
        card.deleteLater()
        for i, c in enumerate(self._obs_cards):
            c.set_number(str(i + 1))
        self.field_changed.emit()

    def _clear_obs_cards(self) -> None:
        for card in list(self._obs_cards):
            self._obs_body_layout.removeWidget(card)
            card.deleteLater()
        self._obs_cards.clear()


def _sub_has_content(sub: dict) -> bool:
    if sub.get("title") or sub.get("content"):
        return True
    return any(_sub_has_content(c) for c in sub.get("children", []))


def _load_company() -> dict:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.schema import CompanyProfile
    session = SessionLocal()
    try:
        profile = session.query(CompanyProfile).first()
        if profile:
            return {
                "name":  profile.name,
                "city":  profile.city,
                "email": profile.email,
                "phone": profile.phone,
            }
        return {}
    finally:
        session.close()
