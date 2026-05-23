from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QLineEdit,
)
from PySide6.QtCore import Qt, QObject, QEvent, Signal
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument

from docpro_frontend.report.styles import report_styles as S

_SLOT_PLACEHOLDER = 0
_SLOT_PDF         = 1
_SLOT_LOADING     = 2

_ZOOM_MIN        = 0.25
_ZOOM_MAX        = 4.0
_ZOOM_STEP_BTN   = 0.25
_ZOOM_STEP_WHEEL = 0.10


class _WheelZoomFilter(QObject):
    """
    Intercepts mouse-wheel events on the PDF viewport.
    Ctrl+Wheel → zoom (consumed, no scroll).
    Plain Wheel → passed through so QPdfView scrolls natively.
    """

    def __init__(self, on_delta, parent=None):
        super().__init__(parent)
        self._on_delta = on_delta

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                self._on_delta(event.angleDelta().y())
                return True  # consumed — prevent scroll while zooming
        return super().eventFilter(obj, event)


class PreviewPanel(QWidget):
    """
    Right-side PDF preview panel for reports.

    States
    ------
    placeholder  No document open or not yet rendered.
    loading      A render is in progress (Ctrl+S or auto on open).
    pdf          QPdfView with zoom controls.

    Zoom
    ----
    +/- buttons: ±25% per click.
    Mouse wheel over the PDF view: ±10% per notch.
    Input field: type a number (e.g. "75" or "75%") and press Enter.

    Signals
    -------
    collapse_toggled(bool)
    download_requested
    """

    collapse_toggled   = Signal(bool)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreviewPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.preview_panel())
        self.setMinimumWidth(0)

        self._collapsed = False
        self._has_pdf   = False

        self._pdf_doc = QPdfDocument(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_header())
        root.addWidget(self._build_body(), 1)
        root.addWidget(self._build_zoom_bar())

    # ── Public API ────────────────────────────────────────────────────────────

    def load_pdf(self, path) -> None:
        """Load a PDF from disk. Releases any previous file lock before opening."""
        self._pdf_doc.close()
        self._pdf_doc.load(str(path))
        self._has_pdf = True
        self._set_zoom(1.0)
        self._stack.setCurrentIndex(_SLOT_PDF)
        self._zoom_bar.setVisible(True)

    def set_loading(self, busy: bool) -> None:
        """Show the loading overlay (busy=True) or restore previous state (busy=False)."""
        if busy:
            self._stack.setCurrentIndex(_SLOT_LOADING)
            self._zoom_bar.setVisible(False)
        else:
            if self._has_pdf:
                self._stack.setCurrentIndex(_SLOT_PDF)
                self._zoom_bar.setVisible(True)
            else:
                self._stack.setCurrentIndex(_SLOT_PLACEHOLDER)

    def clear(self) -> None:
        """Release file lock and return to placeholder state."""
        self._pdf_doc.close()
        self._has_pdf = False
        self._stack.setCurrentIndex(_SLOT_PLACEHOLDER)
        self._zoom_bar.setVisible(False)

    # ── Zoom ──────────────────────────────────────────────────────────────────

    def _set_zoom(self, factor: float) -> None:
        factor = max(_ZOOM_MIN, min(_ZOOM_MAX, factor))
        self._pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self._pdf_view.setZoomFactor(factor)
        if not self._zoom_input.hasFocus():
            self._zoom_input.setText(f"{int(round(factor * 100))}%")
        self._zoom_out_btn.setEnabled(factor > _ZOOM_MIN)
        self._zoom_in_btn.setEnabled(factor < _ZOOM_MAX)

    def _on_zoom_in(self) -> None:
        self._set_zoom(self._pdf_view.zoomFactor() + _ZOOM_STEP_BTN)

    def _on_zoom_out(self) -> None:
        self._set_zoom(self._pdf_view.zoomFactor() - _ZOOM_STEP_BTN)

    def _on_wheel_delta(self, delta: int) -> None:
        step = (delta / 120.0) * _ZOOM_STEP_WHEEL
        self._set_zoom(self._pdf_view.zoomFactor() + step)

    def _on_zoom_input_edited(self) -> None:
        text = self._zoom_input.text().replace("%", "").strip()
        try:
            self._set_zoom(int(text) / 100.0)
        except ValueError:
            self._zoom_input.setText(
                f"{int(round(self._pdf_view.zoomFactor() * 100))}%"
            )
        self._pdf_view.setFocus()

    # ── Internal builders ─────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("PreviewHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setStyleSheet(S.preview_header())
        header.setFixedHeight(44)

        h = QHBoxLayout(header)
        h.setContentsMargins(16, 0, 12, 0)
        h.setSpacing(8)

        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 14px; background: transparent;")
        label = QLabel("Vista previa PDF")
        label.setStyleSheet(S.preview_header_label())

        h.addWidget(icon)
        h.addWidget(label)
        h.addStretch()

        self._collapse_btn = QPushButton("⟩")
        self._collapse_btn.setStyleSheet(S.btn_preview_icon())
        self._collapse_btn.setToolTip("Ocultar panel")
        self._collapse_btn.clicked.connect(self._on_collapse)
        h.addWidget(self._collapse_btn)

        return header

    def _build_body(self) -> QStackedWidget:
        self._stack = QStackedWidget()

        # Slot 0 — Placeholder
        placeholder = QWidget()
        ph = QVBoxLayout(placeholder)
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_icon = QLabel("📄")
        ph_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_icon.setStyleSheet("font-size: 36px; background: transparent;")
        ph_msg = QLabel("Presiona Ctrl+S\npara generar la vista previa")
        ph_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_msg.setWordWrap(True)
        ph_msg.setStyleSheet(S.preview_placeholder_label())
        ph.addWidget(ph_icon)
        ph.addSpacing(12)
        ph.addWidget(ph_msg)
        self._stack.addWidget(placeholder)  # index 0

        # Slot 1 — QPdfView
        self._pdf_view = QPdfView(self)
        self._pdf_view.setDocument(self._pdf_doc)
        self._pdf_view.setPageMode(QPdfView.PageMode.MultiPage)
        self._pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self._stack.addWidget(self._pdf_view)  # index 1

        # Install wheel-zoom filter on the scroll viewport
        self._wheel_filter = _WheelZoomFilter(self._on_wheel_delta, self)
        self._pdf_view.viewport().installEventFilter(self._wheel_filter)

        # Slot 2 — Loading overlay
        loading = QWidget()
        ld = QVBoxLayout(loading)
        ld.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ld_icon = QLabel("⏳")
        ld_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ld_icon.setStyleSheet("font-size: 32px; background: transparent;")
        ld_msg = QLabel("Generando vista previa…")
        ld_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ld_msg.setStyleSheet(S.preview_loading_label())
        ld.addWidget(ld_icon)
        ld.addSpacing(12)
        ld.addWidget(ld_msg)
        self._stack.addWidget(loading)  # index 2

        return self._stack

    def _build_zoom_bar(self) -> QWidget:
        self._zoom_bar = QWidget()
        self._zoom_bar.setObjectName("ZoomBar")
        self._zoom_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._zoom_bar.setStyleSheet(S.zoom_bar())
        self._zoom_bar.setFixedHeight(40)
        self._zoom_bar.setVisible(False)

        h = QHBoxLayout(self._zoom_bar)
        h.setContentsMargins(12, 0, 12, 0)
        h.setSpacing(6)
        h.addStretch()

        self._zoom_out_btn = QPushButton("−")
        self._zoom_out_btn.setStyleSheet(S.btn_zoom())
        self._zoom_out_btn.setToolTip("Alejar (−25%)")
        self._zoom_out_btn.clicked.connect(self._on_zoom_out)
        h.addWidget(self._zoom_out_btn)

        self._zoom_input = QLineEdit("100%")
        self._zoom_input.setStyleSheet(S.zoom_input())
        self._zoom_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._zoom_input.setToolTip("Zoom actual — escribe un valor y presiona Enter\nCtrl+Rueda del mouse para zoom rápido")
        self._zoom_input.returnPressed.connect(self._on_zoom_input_edited)
        h.addWidget(self._zoom_input)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setStyleSheet(S.btn_zoom())
        self._zoom_in_btn.setToolTip("Acercar (+25%)")
        self._zoom_in_btn.clicked.connect(self._on_zoom_in)
        h.addWidget(self._zoom_in_btn)

        h.addStretch()
        return self._zoom_bar

    def _on_collapse(self) -> None:
        self._collapsed = not self._collapsed
        self._collapse_btn.setText("⟨" if self._collapsed else "⟩")
        self._collapse_btn.setToolTip(
            "Mostrar panel" if self._collapsed else "Ocultar panel"
        )
        self.collapse_toggled.emit(self._collapsed)
