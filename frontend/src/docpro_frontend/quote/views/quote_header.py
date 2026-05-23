from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.quote.styles import quote_styles as S


class QuoteHeader(QWidget):
    """
    Top bar for the quote editor.
    Signals:
        back_requested
        finalize_requested
        delete_requested
        generate_pdf_requested
        approve_requested
        reject_requested
    """

    back_requested         = Signal()
    finalize_requested     = Signal()
    delete_requested       = Signal()
    generate_pdf_requested = Signal()
    approve_requested      = Signal()
    reject_requested       = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DocHeader")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.doc_header())
        self.setFixedHeight(60)

        h = QHBoxLayout(self)
        h.setContentsMargins(24, 0, 24, 0)
        h.setSpacing(0)

        # Back button
        back_btn = QPushButton("← Inicio")
        back_btn.setStyleSheet(S.back_btn())
        back_btn.clicked.connect(self.back_requested)
        h.addWidget(back_btn)
        h.addSpacing(20)

        # Type pill + number
        type_pill = QLabel("Cotización")
        type_pill.setStyleSheet(S.doc_type_pill())

        self._number_lbl = QLabel("—")
        self._number_lbl.setStyleSheet(S.doc_number_label())

        self._status_pill = QLabel("Borrador")
        self._status_pill.setStyleSheet(S.status_pill("Borrador"))

        h.addWidget(type_pill)
        h.addSpacing(10)
        h.addWidget(self._number_lbl)
        h.addSpacing(10)
        h.addWidget(self._status_pill)
        h.addSpacing(20)

        # Autosave indicator
        self._dot = QLabel()
        self._dot.setFixedSize(7, 7)
        self._dot.setStyleSheet(S.autosave_dot("saved"))

        self._autosave_lbl = QLabel("Guardado")
        self._autosave_lbl.setStyleSheet(S.autosave_label())

        h.addWidget(self._dot)
        h.addSpacing(5)
        h.addWidget(self._autosave_lbl)

        h.addStretch()

        # Action buttons
        self._history_btn = QPushButton("🕓")
        self._history_btn.setStyleSheet(S.btn_header_icon())
        self._history_btn.setToolTip("Historial de versiones (Fase 5)")
        self._history_btn.setEnabled(False)
        h.addWidget(self._history_btn)
        h.addSpacing(8)

        self._delete_btn = QPushButton("Eliminar")
        self._delete_btn.setStyleSheet(S.btn_header_danger())
        self._delete_btn.clicked.connect(self.delete_requested)
        h.addWidget(self._delete_btn)
        h.addSpacing(8)

        self._sep1 = self._make_sep()
        h.addWidget(self._sep1)
        h.addSpacing(8)

        self._pdf_btn = QPushButton("Exportar PDF")
        self._pdf_btn.setStyleSheet(S.btn_header_ghost())
        self._pdf_btn.clicked.connect(self.generate_pdf_requested)
        h.addWidget(self._pdf_btn)
        h.addSpacing(8)

        self._sep2 = self._make_sep()
        h.addWidget(self._sep2)
        h.addSpacing(8)

        self._finalize_btn = QPushButton("Finalizar")
        self._finalize_btn.setStyleSheet(S.btn_header_primary())
        self._finalize_btn.clicked.connect(self.finalize_requested)
        h.addWidget(self._finalize_btn)

        self._sep3 = self._make_sep()
        self._sep3.setVisible(False)
        h.addSpacing(8)
        h.addWidget(self._sep3)
        h.addSpacing(8)

        self._approve_btn = QPushButton("✓ Aprobar")
        self._approve_btn.setStyleSheet(S.btn_approve())
        self._approve_btn.clicked.connect(self.approve_requested)
        self._approve_btn.setVisible(False)
        h.addWidget(self._approve_btn)
        h.addSpacing(8)

        self._reject_btn = QPushButton("✗ Rechazar")
        self._reject_btn.setStyleSheet(S.btn_reject())
        self._reject_btn.clicked.connect(self.reject_requested)
        self._reject_btn.setVisible(False)
        h.addWidget(self._reject_btn)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_document_number(self, number: str) -> None:
        self._number_lbl.setText(number)

    def set_status(self, status: str) -> None:
        self._status_pill.setText(status)
        self._status_pill.setStyleSheet(S.status_pill(status))
        is_borrador = status == "Borrador"
        is_enviado  = status == "Enviado"
        self._finalize_btn.setVisible(is_borrador)
        self._delete_btn.setVisible(is_borrador)
        self._sep3.setVisible(is_enviado)
        self._approve_btn.setVisible(is_enviado)
        self._reject_btn.setVisible(is_enviado)

    def set_autosave_state(self, state: str) -> None:
        """state: 'saving' | 'saved' | 'error' | 'idle'"""
        self._dot.setStyleSheet(S.autosave_dot(state))
        labels = {
            "saving": "Guardando…",
            "saved":  "Guardado",
            "error":  "Error al guardar",
            "idle":   "",
        }
        self._autosave_lbl.setText(labels.get(state, ""))

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_sep() -> QLabel:
        sep = QLabel()
        sep.setFixedSize(1, 28)
        sep.setStyleSheet("background: #E5E7EB;")
        return sep
