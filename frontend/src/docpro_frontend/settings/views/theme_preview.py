"""Live-preview panel: renders a sample cotización PDF with the current theme."""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import Qt, QTimer
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from docpro_frontend.services import asset_service


def _sample_quote() -> SimpleNamespace:
    items = (
        SimpleNamespace(position=1, quantity=1.0, description="Servicio de instalación", unit_price=180_000.0, subtotal=180_000.0),
        SimpleNamespace(position=2, quantity=4.0, description="Cambio de filtros HEPA",  unit_price=25_000.0,  subtotal=100_000.0),
        SimpleNamespace(position=3, quantity=1.0, description="Mantención preventiva",   unit_price=95_000.0,  subtotal=95_000.0),
    )
    neto  = sum(i.subtotal for i in items)
    iva   = round(neto * 0.19)
    total = neto + iva
    return SimpleNamespace(
        number="COT-0001",
        client_name="Cliente de muestra SpA",
        client_rut="76.234.567-8",
        client_address="Av. Ejemplo 1234, Punta Arenas",
        client_city="Punta Arenas",
        client_phone="+56 61 221 1111",
        client_email="cliente@muestra.cl",
        issue_date="2026-01-15",
        items=items,
        neto=neto, iva=iva, total=total,
        show_iva=True,
        observations="Vigencia 15 días. Precios en CLP.",
    )


def _sample_company() -> SimpleNamespace:
    return SimpleNamespace(
        name="Empresa Emisora SpA",
        city="Punta Arenas",
        email="contacto@empresa.cl",
        phone="+56 61 234 5678",
    )


def _header_data_url(filename: str) -> str | None:
    if not filename:
        return None
    p = asset_service.resolve(filename)
    if p is None:
        return None
    suffix = p.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix or "png"
    return f"data:image/{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


class ThemePreview(QWidget):
    """Renders a sample cotización PDF with the current theme, debounced."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel("Vista previa")
        title.setStyleSheet("font-size: 12px; color: #6B7280; font-weight: 600;")
        layout.addWidget(title)

        self._pdf_doc = QPdfDocument(self)
        self._pdf_view = QPdfView(self)
        self._pdf_view.setDocument(self._pdf_doc)
        self._pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
        self._pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self._pdf_view.setMinimumHeight(420)
        layout.addWidget(self._pdf_view, 1)

        self._tmp_pdf = Path(tempfile.gettempdir()) / "docpro" / "theme_preview.pdf"
        self._tmp_pdf.parent.mkdir(parents=True, exist_ok=True)

        self._pending_theme: dict | None = None
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(400)
        self._debounce.timeout.connect(self._render_now)

    # ── Public API ────────────────────────────────────────────────────

    def schedule_refresh(self, theme_data: dict) -> None:
        """Debounce a re-render; call after any theme_form change."""
        self._pending_theme = theme_data
        self._debounce.start()

    # ── Internal ──────────────────────────────────────────────────────

    def _render_now(self) -> None:
        theme = self._pending_theme or {}
        try:
            from docpro_backend.services.pdf_service import render_quote_pdf
            from docpro_backend.services.theme_service import resolve_font_stack

            pdf_theme = {
                "primary":     theme.get("primary")     or "#111111",
                "accent":      theme.get("accent")      or "#EBEBEB",
                "text":        theme.get("text")        or "#1A1A1A",
                "font_family": resolve_font_stack(theme.get("font_family") or "Arial"),
            }
            header_data = _header_data_url(theme.get("header_imagen") or "")

            self._pdf_doc.close()
            render_quote_pdf(
                _sample_quote(), _sample_company(), self._tmp_pdf,
                theme=pdf_theme, header_imagen=header_data,
            )
            self._pdf_doc.load(str(self._tmp_pdf))
        except Exception as exc:  # noqa: BLE001 — surface preview errors quietly
            import logging
            logging.getLogger(__name__).exception("ThemePreview render failed: %s", exc)
