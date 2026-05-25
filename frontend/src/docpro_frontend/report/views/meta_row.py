from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QDateEdit
from PySide6.QtCore import Signal, Qt, QDate, QThreadPool

from docpro_frontend.report.styles import report_styles as S
from docpro_frontend.services.worker import Worker


class MetaRow(QWidget):
    """
    Blue gradient meta row: N° Informe (read-only after save) + Fecha emisión + company block.
    """

    field_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MetaRow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.meta_row())
        self.setFixedHeight(58)

        h = QHBoxLayout(self)
        h.setContentsMargins(20, 0, 20, 0)
        h.setSpacing(0)

        # N° Informe
        num_lbl = QLabel("N° INFORME")
        num_lbl.setStyleSheet(S.meta_label())

        self._number_input = QLineEdit()
        self._number_input.setPlaceholderText("IT-0001")
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
        sep.setStyleSheet("background: #93C5FD;")
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

        self._issue_date.dateChanged.connect(lambda _: self.field_changed.emit())

        # Load company profile asynchronously
        worker = Worker(_load_company)
        worker.signals.result.connect(self._on_company_loaded)
        QThreadPool.globalInstance().start(worker)

    def _on_company_loaded(self, data: dict) -> None:
        if not data:
            return
        self._company_name_lbl.setText(data.get("name", ""))
        parts = [p for p in (data.get("phone"), data.get("email")) if p]
        self._company_detail_lbl.setText("  ·  ".join(parts))

    # ── Public ────────────────────────────────────────────────────────────────

    def get_number(self) -> str:
        return self._number_input.text().strip()

    def set_number(self, number: str) -> None:
        self._number_input.setText(number)

    def lock_number(self) -> None:
        self._number_input.setReadOnly(True)

    def get_issue_date(self) -> str:
        return self._issue_date.date().toString("yyyy-MM-dd")

    def set_issue_date(self, date_str: str) -> None:
        try:
            y, m, d = date_str.split("-")
            self._issue_date.setDate(QDate(int(y), int(m), int(d)))
        except (ValueError, AttributeError):
            self._issue_date.setDate(QDate.currentDate())

    def set_readonly(self, readonly: bool) -> None:
        self._issue_date.setEnabled(not readonly)

    def reset(self) -> None:
        self._number_input.clear()
        self._number_input.setReadOnly(False)
        self._issue_date.setDate(QDate.currentDate())


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
