from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt

from docpro_frontend.report.styles import report_styles as S


class ReportHeader(QWidget):
    """
    Top bar for the report editor.
    Signals:
        back_requested
        title_changed(str)
        finalize_requested
        delete_requested
        generate_pdf_requested
    Methods:
        set_document_number(str)
        set_status(str)
        set_autosave_state(str)
        get_title() -> str
        set_title(str)
    """

    back_requested          = Signal()
    finalize_requested      = Signal()
    delete_requested        = Signal()
    generate_pdf_requested  = Signal()
    send_requested          = Signal()
    number_change_requested = Signal(str)
    duplicate_requested     = Signal()

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
        type_pill = QLabel("Informe técnico")
        type_pill.setStyleSheet(S.doc_type_pill())

        self._number_lbl = QLabel("—")
        self._number_lbl.setStyleSheet(S.doc_number_label())
        self._current_number = "—"

        self._edit_num_btn = QPushButton("✎")
        self._edit_num_btn.setStyleSheet(S.doc_number_edit_btn())
        self._edit_num_btn.setFixedSize(22, 22)
        self._edit_num_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._edit_num_btn.setToolTip("Editar número")
        self._edit_num_btn.setVisible(False)
        self._edit_num_btn.clicked.connect(self._on_edit_number)

        h.addWidget(type_pill)
        h.addSpacing(10)
        h.addWidget(self._number_lbl)
        h.addSpacing(4)
        h.addWidget(self._edit_num_btn)
        h.addSpacing(8)

        # Status pill
        self._status_pill = QLabel("Borrador")
        self._status_pill.setStyleSheet(S.status_pill("Borrador"))
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

        # History button (disabled stub)
        self._history_btn = QPushButton("🕓")
        self._history_btn.setStyleSheet(S.btn_header_icon())
        self._history_btn.setToolTip("Historial de versiones (Fase 5)")
        self._history_btn.setEnabled(False)
        h.addWidget(self._history_btn)
        h.addSpacing(8)

        # Eliminar
        self._delete_btn = QPushButton("Eliminar")
        self._delete_btn.setStyleSheet(S.btn_header_danger())
        self._delete_btn.clicked.connect(self.delete_requested)
        h.addWidget(self._delete_btn)
        h.addSpacing(6)

        self._dup_btn = QPushButton("Duplicar")
        self._dup_btn.setStyleSheet(S.btn_header_ghost())
        self._dup_btn.setEnabled(False)
        self._dup_btn.clicked.connect(self.duplicate_requested)
        h.addWidget(self._dup_btn)
        h.addSpacing(8)

        h.addWidget(self._make_sep())
        h.addSpacing(8)

        # Exportar PDF
        self._pdf_btn = QPushButton("Exportar PDF")
        self._pdf_btn.setStyleSheet(S.btn_header_ghost())
        self._pdf_btn.clicked.connect(self.generate_pdf_requested)
        h.addWidget(self._pdf_btn)
        h.addSpacing(6)

        # Enviar
        self._send_btn = QPushButton("Enviar")
        self._send_btn.setStyleSheet(S.btn_header_ghost())
        self._send_btn.setVisible(False)
        self._send_btn.clicked.connect(self.send_requested)
        h.addWidget(self._send_btn)
        h.addSpacing(8)

        h.addWidget(self._make_sep())
        h.addSpacing(8)

        # Finalizar
        self._finalize_btn = QPushButton("Finalizar")
        self._finalize_btn.setStyleSheet(S.btn_header_primary())
        self._finalize_btn.clicked.connect(self.finalize_requested)
        h.addWidget(self._finalize_btn)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_document_number(self, number: str) -> None:
        self._number_lbl.setText(number)
        self._current_number = number

    def set_number_editable(self, enabled: bool) -> None:
        self._edit_num_btn.setVisible(enabled)

    def set_duplicate_enabled(self, enabled: bool) -> None:
        self._dup_btn.setEnabled(enabled)

    def set_status(self, status: str) -> None:
        self._status_pill.setText(status)
        self._status_pill.setStyleSheet(S.status_pill(status))
        is_borrador   = status == "Borrador"
        is_finalizado = status == "Finalizado"
        self._finalize_btn.setVisible(is_borrador)
        self._delete_btn.setVisible(is_borrador)
        self._send_btn.setVisible(is_finalizado)

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

    def _on_edit_number(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            self,
            "Editar número de informe",
            "Número:",
            text=self._current_number,
        )
        text = text.strip()
        if ok and text and text != self._current_number:
            self.number_change_requested.emit(text)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_sep() -> QLabel:
        sep = QLabel()
        sep.setFixedSize(1, 28)
        sep.setStyleSheet("background: #E5E7EB;")
        return sep
