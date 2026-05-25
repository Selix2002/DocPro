from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

_MAX_BYTES = 25 * 1024 * 1024  # 25 MB — Gmail hard limit


class EmailComposerDialog(QDialog):
    """
    Modal dialog for composing an email before sending via Gmail.
    All fields are pre-filled but editable. The document PDF is a fixed
    attachment; the user can add extra files of any type.
    Call get_data() after exec() == Accepted to retrieve
    (recipient, subject, body, extra_attachments).
    """

    def __init__(
        self,
        recipient: str,
        subject: str,
        body: str,
        pdf_path: Path,
        accent_color: str = "#B45309",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Enviar por Gmail")
        self.setMinimumWidth(560)
        self.setStyleSheet(_dialog_style(accent_color))

        self._pdf_path     = pdf_path
        self._extra_paths: list[Path] = []
        self._accent       = accent_color

        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(24, 24, 24, 24)

        # Form fields
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._recipient = QLineEdit(recipient)
        self._subject   = QLineEdit(subject)
        form.addRow("Para:", self._recipient)
        form.addRow("Asunto:", self._subject)
        root.addLayout(form)

        body_lbl = QLabel("Cuerpo:")
        body_lbl.setStyleSheet("font-size: 15px; color: #374151;")
        root.addWidget(body_lbl)

        self._body = QTextEdit()
        self._body.setPlainText(body)
        self._body.setMinimumHeight(130)
        root.addWidget(self._body)

        # Fixed attachment (the document PDF — cannot be removed)
        fixed_row = QHBoxLayout()
        fixed_row.setSpacing(6)
        clip_lbl = QLabel("📎")
        clip_lbl.setStyleSheet("font-size: 16px;")
        fixed_row.addWidget(clip_lbl)
        name_lbl = QLabel(pdf_path.name)
        name_lbl.setStyleSheet("color: #374151; font-size: 14px;")
        fixed_row.addWidget(name_lbl)
        fixed_row.addStretch()
        root.addLayout(fixed_row)

        # Extra attachments area — scrollable so the dialog never grows off-screen
        _ROW_H    = 32          # px per row
        _ROW_GAP  = 4           # spacing between rows
        _ROWS_VIS = 4           # rows visible before scroll activates
        _scroll_max_h = _ROWS_VIS * _ROW_H + (_ROWS_VIS - 1) * _ROW_GAP

        self._row_h = _ROW_H

        self._extras_container = QWidget()
        self._extras_container.setStyleSheet("background: #FFFFFF;")
        self._extras_layout    = QVBoxLayout(self._extras_container)
        self._extras_layout.setContentsMargins(0, 0, 0, 0)
        self._extras_layout.setSpacing(_ROW_GAP)

        self._extras_scroll = QScrollArea()
        self._extras_scroll.setWidget(self._extras_container)
        self._extras_scroll.setWidgetResizable(True)
        self._extras_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._extras_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._extras_scroll.setMaximumHeight(_scroll_max_h)
        self._extras_scroll.setStyleSheet("QScrollArea { background: #FFFFFF; border: none; }")
        self._extras_scroll.hide()
        root.addWidget(self._extras_scroll)

        add_btn = QPushButton("＋  Adjuntar archivo")
        add_btn.setStyleSheet(_BTN_GHOST)
        add_btn.clicked.connect(self._on_add_file)
        root.addWidget(add_btn)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(_BTN_GHOST)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(8)
        send_btn = QPushButton("Enviar")
        send_btn.setDefault(True)
        send_btn.setStyleSheet(_btn_primary(accent_color))
        send_btn.clicked.connect(self.accept)
        btn_row.addWidget(send_btn)
        root.addLayout(btn_row)

    # ── Public ────────────────────────────────────────────────────────

    def get_data(self) -> tuple[str, str, str, list[Path]]:
        return (
            self._recipient.text().strip(),
            self._subject.text().strip(),
            self._body.toPlainText().strip(),
            list(self._extra_paths),
        )

    # ── Overrides ─────────────────────────────────────────────────────

    def accept(self) -> None:
        total = self._pdf_path.stat().st_size
        for p in self._extra_paths:
            try:
                total += p.stat().st_size
            except OSError:
                pass
        if total > _MAX_BYTES:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Adjuntos demasiado grandes")
            dlg.setText("El total de adjuntos supera el límite de 25 MB de Gmail.")
            dlg.setInformativeText(
                f"Tamaño actual: {total / 1024 / 1024:.1f} MB. "
                "Elimina algunos archivos antes de enviar."
            )
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.setStyleSheet(_dialog_style(self._accent))
            dlg.addButton("Entendido", QMessageBox.ButtonRole.RejectRole)
            dlg.exec()
            return
        super().accept()

    # ── Internal ──────────────────────────────────────────────────────

    def _on_add_file(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos a adjuntar",
            "",
            "Todos los archivos (*)",
        )
        for p in paths:
            path = Path(p)
            if path not in self._extra_paths:
                self._extra_paths.append(path)
                self._add_extra_row(path)

    def _add_extra_row(self, path: Path) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(6)

        clip = QLabel("📎")
        clip.setStyleSheet("font-size: 14px; background: transparent;")
        row.addWidget(clip)

        name = QLabel(path.name)
        name.setStyleSheet("color: #374151; font-size: 14px; background: transparent;")
        name.setToolTip(str(path))
        row.addWidget(name)
        row.addStretch()

        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setStyleSheet(_BTN_REMOVE)
        remove_btn.clicked.connect(lambda: self._remove_extra(path, container))
        row.addWidget(remove_btn)

        container = QWidget()
        container.setFixedHeight(self._row_h)
        container.setStyleSheet("background: #FFFFFF;")
        container.setLayout(row)
        self._extras_layout.addWidget(container)
        self._extras_scroll.show()
        self.adjustSize()

    def _remove_extra(self, path: Path, container: QWidget) -> None:
        if path in self._extra_paths:
            self._extra_paths.remove(path)
        container.setParent(None)
        container.deleteLater()
        if not self._extra_paths:
            self._extras_scroll.hide()
        self.adjustSize()


# ── Styles ────────────────────────────────────────────────────────────────────

_BTN_GHOST = """
QPushButton {
    background: #F3F4F6; color: #111827;
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 6px 20px; font-size: 15px;
}
QPushButton:hover { background: #E5E7EB; }
"""

_BTN_REMOVE = """
QPushButton {
    background: transparent; color: #9CA3AF;
    border: none; border-radius: 4px;
    font-size: 16px; font-weight: 700;
    padding: 0;
}
QPushButton:hover { color: #EF4444; background: #FEE2E2; }
"""


def _btn_primary(color: str) -> str:
    return f"""
QPushButton {{
    background: {color}; color: #FFFFFF;
    border: 1px solid {color}; border-radius: 6px;
    padding: 6px 20px; font-size: 15px;
}}
QPushButton:hover {{ opacity: 0.9; }}
QPushButton:disabled {{ background: #D1D5DB; border-color: #D1D5DB; }}
"""


def _dialog_style(accent: str) -> str:
    return f"""
QDialog {{ background: #FFFFFF; }}
QLabel {{ color: #111827; background: transparent; font-size: 15px; }}
QLineEdit {{
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 6px 10px; font-size: 15px; color: #111827;
    background: #FFFFFF;
}}
QLineEdit:focus {{ border-color: {accent}; }}
QTextEdit {{
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 8px; font-size: 15px; color: #111827;
    background: #FFFFFF;
}}
QTextEdit:focus {{ border-color: {accent}; }}
QMessageBox {{ background: #FFFFFF; }}
QMessageBox QLabel {{ color: #111827; background: transparent; }}
QPushButton {{
    background: #F3F4F6; color: #111827;
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 6px 20px; font-size: 15px;
}}
QPushButton:hover {{ background: #E5E7EB; }}
"""
