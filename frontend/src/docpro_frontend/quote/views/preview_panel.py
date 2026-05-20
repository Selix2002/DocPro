from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

from docpro_frontend.quote.styles import quote_styles as S


class PreviewPanel(QWidget):
    """
    Right-side PDF preview panel.
    Phase 4 will replace the placeholder with a live QPdfView.
    collapse_toggled(collapsed) emitted when the panel is collapsed/expanded.
    """

    collapse_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PreviewPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(S.preview_panel())
        self.setMinimumWidth(0)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body.setObjectName("PreviewBody")
        body_layout = QVBoxLayout(body)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("📄")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 36px; background: transparent;")

        msg = QLabel("Vista previa disponible\nen Fase 4")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        msg.setStyleSheet(S.preview_placeholder_label())

        body_layout.addWidget(icon)
        body_layout.addSpacing(12)
        body_layout.addWidget(msg)

        root.addWidget(body, 1)

        self._collapsed = False

    # ── Internal ──────────────────────────────────────────────────────────────

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

        badge = QLabel("Fase 4")
        badge.setStyleSheet(S.preview_phase_badge())

        h.addWidget(icon)
        h.addWidget(label)
        h.addWidget(badge)
        h.addStretch()

        self._collapse_btn = QPushButton("⟩")
        self._collapse_btn.setStyleSheet(S.btn_preview_icon())
        self._collapse_btn.setToolTip("Ocultar panel")
        self._collapse_btn.clicked.connect(self._on_collapse)
        h.addWidget(self._collapse_btn)

        return header

    def _on_collapse(self) -> None:
        self._collapsed = not self._collapsed
        self._collapse_btn.setText("⟨" if self._collapsed else "⟩")
        self._collapse_btn.setToolTip("Mostrar panel" if self._collapsed else "Ocultar panel")
        self.collapse_toggled.emit(self._collapsed)
