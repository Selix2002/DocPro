from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QTextEdit,
)
from PySide6.QtCore import Signal, Qt

from docpro_frontend.report.styles import report_styles as S
from docpro_frontend.report.views.meta_row import MetaRow
from docpro_frontend.report.views.trabajo_section import TrabajoSection
from docpro_frontend.report.views.sections_list import SectionsList
from docpro_frontend.quote.views.client_section import ClientSection


class ReportForm(QWidget):
    """
    Left scrollable panel:
      MetaRow → ClientSection → TrabajoSection → SectionsList → Observaciones.
    Signals:
        field_changed  — any tracked field changed (drives 800ms autosave timer)
        rut_entered(str) — relayed from ClientSection
    Methods:
        get_data() -> dict
        set_data(report_rm)
        set_readonly(bool)
        reset()
        set_number(str)
        lock_number()
        get_client_data() -> dict
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

        # 1. Meta row
        self._meta_row = MetaRow()
        inner.addWidget(self._meta_row)

        # 2. Client section (reused from quote module)
        self._client = ClientSection()
        inner.addWidget(self._client)

        # 3. Trabajo efectuado
        self._trabajo = TrabajoSection()
        inner.addWidget(self._trabajo)

        # 4. Dynamic sections list (includes "Agregar nueva sección" button internally)
        self._sections_list = SectionsList()
        inner.addWidget(self._sections_list)

        # 5. Observaciones (toggle)
        self._obs_is_active = False
        self._obs_inactive_widget = self._build_obs_inactive()
        self._obs_active_frame = self._build_obs_active()
        self._obs_active_frame.setVisible(False)
        inner.addWidget(self._obs_inactive_widget)
        inner.addWidget(self._obs_active_frame)

        inner.addStretch()

        # Signal wiring
        self._meta_row.field_changed.connect(self.field_changed)
        self._client.rut_entered.connect(self.rut_entered)
        self._client.client_data_changed.connect(self.field_changed)
        self._trabajo.field_changed.connect(self.field_changed)
        self._sections_list.field_changed.connect(self.field_changed)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_data(self) -> dict:
        return {
            "number":       self._meta_row.get_number(),
            "issue_date":   self._meta_row.get_issue_date(),
            "title":        None,  # collected by service from ReportHeader
            "trabajo":      self._trabajo.get_data(),
            "sections":     self._sections_list.get_data(),
            "observations": self._obs.toPlainText().strip() if self._obs_is_active else None,
        }

    def set_data(self, rm) -> None:
        """Populate form from a ReportReadModel."""
        self._meta_row.set_number(rm.number)
        self._meta_row.lock_number()

        self._client.set_rut(rm.client_rut)
        self._client.fill_client(
            name=rm.client_name,
            address=rm.client_address,
            email=rm.client_email,
            phone=rm.client_phone,
        )

        sections_data, trabajo_from_db = _sections_from_read_model(rm.sections)
        if trabajo_from_db:
            self._trabajo.set_data(trabajo_from_db)
        self._sections_list.set_data(sections_data)

    def set_number(self, number: str) -> None:
        self._meta_row.set_number(number)

    def lock_number(self) -> None:
        self._meta_row.lock_number()

    def set_readonly(self, readonly: bool) -> None:
        self._meta_row.set_readonly(readonly)
        self._client.set_readonly(readonly)
        self._trabajo.set_readonly(readonly)
        self._sections_list.set_readonly(readonly)
        if self._obs_is_active:
            self._obs.setReadOnly(readonly)

    def reset(self) -> None:
        self._meta_row.reset()
        self._client.reset()
        self._trabajo.reset()
        self._sections_list.reset()
        self._obs_inactive_widget.setVisible(True)
        self._obs_active_frame.setVisible(False)
        self._obs_is_active = False
        self._obs.clear()

    def get_client_data(self) -> dict:
        return self._client.get_client_data()

    @property
    def client_section(self) -> ClientSection:
        return self._client

    # ── Internal builders ─────────────────────────────────────────────────────

    def _build_obs_inactive(self) -> QWidget:
        widget = QWidget()
        widget.setObjectName("ObsInactive")
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        widget.setStyleSheet(S.obs_inactive())

        h = QHBoxLayout(widget)
        h.setContentsMargins(20, 16, 20, 16)

        label = QLabel("Observaciones")
        label.setStyleSheet(S.obs_inactive_label())

        activate_btn = QPushButton("Activar sección")
        activate_btn.setStyleSheet(S.btn_activate_section())
        activate_btn.clicked.connect(self._activate_obs)

        h.addWidget(label)
        h.addStretch()
        h.addWidget(activate_btn)
        return widget

    def _build_obs_active(self) -> QFrame:
        block = QFrame()
        block.setObjectName("SectionBlock")
        block.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        block.setStyleSheet(S.section_block())

        layout = QVBoxLayout(block)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Head
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

        self._obs_ai_btn = QPushButton("✦  Mejorar redacción")
        self._obs_ai_btn.setStyleSheet(S.ai_btn_stub())
        self._obs_ai_btn.setEnabled(False)
        self._obs_ai_btn.setToolTip("Disponible en Fase 9")

        h.addWidget(icon)
        h.addSpacing(8)
        h.addWidget(sec_label)
        h.addStretch()
        h.addWidget(self._obs_ai_btn)
        layout.addWidget(head)

        # Body
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 20)

        self._obs = QTextEdit()
        self._obs.setPlaceholderText(
            "Ingrese observaciones, condiciones u otras notas relevantes…"
        )
        self._obs.setStyleSheet(S.section_textarea())
        self._obs.setMinimumHeight(100)
        self._obs.textChanged.connect(self.field_changed)
        body_layout.addWidget(self._obs)
        layout.addWidget(body)

        return block

    def _activate_obs(self) -> None:
        self._obs_inactive_widget.setVisible(False)
        self._obs_active_frame.setVisible(True)
        self._obs_is_active = True
        self.field_changed.emit()


# ── Module-level helper ────────────────────────────────────────────────────────

_TRABAJO_FIXED_KEYS = {"local", "fecha", "tipo_equipo"}


def _sections_from_read_model(sections) -> tuple[list[dict], dict | None]:
    """Reconstruct hierarchical section dicts, separating the 'Trabajo efectuado' context section.

    Returns (regular_sections, trabajo_data_or_None).
    """
    import json as _json

    trabajo_data: dict | None = None
    context_ids: set[int] = set()

    for s in sections:
        if s.parent_id is None and s.content_json and not s.content:
            context_ids.add(s.id)
            try:
                ctx = _json.loads(s.content_json)
                trabajo_data = {
                    "local":          ctx.get("local", ""),
                    "fecha":          ctx.get("fecha", ""),
                    "equipment_type": ctx.get("tipo_equipo", ""),
                    "extra_fields": [
                        {"label": k.replace("_", " ").capitalize(), "value": v}
                        for k, v in ctx.items()
                        if k not in _TRABAJO_FIXED_KEYS
                    ],
                }
            except (ValueError, KeyError):
                pass

    root = sorted(
        [s for s in sections if s.parent_id is None and s.id not in context_ids],
        key=lambda x: x.position,
    )
    children_by_parent: dict[int, list] = {}
    for s in sections:
        if s.parent_id is not None:
            children_by_parent.setdefault(s.parent_id, []).append(s)

    result = []
    for sec in root:
        children = sorted(children_by_parent.get(sec.id, []), key=lambda x: x.position)
        result.append({
            "position": sec.position,
            "title":    sec.title,
            "content":  sec.content or "",
            "subsections": [
                {"position": s.position, "title": s.title, "content": s.content or ""}
                for s in children
            ],
        })
    return result, trabajo_data
