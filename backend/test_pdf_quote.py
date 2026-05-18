"""
Script de prueba visual del PDF de cotización.
Uso: uv run python test_pdf_quote.py
Abre el PDF generado con el visor del sistema.
"""
import subprocess
import sys
from pathlib import Path

from docpro_backend.dtos.config import CompanyProfileReadModel
from docpro_backend.dtos.quotes import QuoteItemReadModel, QuoteReadModel
from docpro_backend.services.pdf_service import quote_pdf_filename, render_quote_pdf

# ── Datos de prueba — edita libremente ──────────────────────────────────────

COMPANY = CompanyProfileReadModel(
    id=1,
    name="Empresa Patagonia SpA",
    city="Punta Arenas",
    email="contacto@empresa.cl",
    phone="+56 61 222 3344",
)

QUOTE = QuoteReadModel(
    document_id=1,
    number="COT-0001",
    status="Borrador",
    issue_date="2026-05-17",
    observations=(
        "Precios en pesos chilenos. Validez de la oferta: 15 días hábiles desde la fecha de emisión.\n"
        "Plazo de entrega: 5 días hábiles tras confirmación.\n"
        "Forma de pago: 50% anticipo, 50% contra entrega."
    ),
    neto=197900.0,
    iva=37601.0,
    total=235501.0,
    client_id=1,
    client_name="Industrias del Sur Ltda.",
    client_rut="76.543.210-9",
    client_address="Av. Colón 580, Of. 3",
    client_city="Punta Arenas",
    client_email="compras@industrias.cl",
    client_phone="+56 61 244 5566",
    created_at="2026-05-17T10:00:00Z",
    updated_at="2026-05-17T10:00:00Z",
    finalized_at=None,
    sent_at=None,
    items=(
        QuoteItemReadModel(id=1, position=1, quantity=2,
                           description="Cable conductor 10 mm² XLPE",
                           unit_price=18500, subtotal=37000),
        QuoteItemReadModel(id=2, position=2, quantity=1,
                           description="Interruptor termomagnético 3×40A",
                           unit_price=54900, subtotal=54900),
        QuoteItemReadModel(id=3, position=3, quantity=5,
                           description="Canaleta ranurada 60×40 mm blanca",
                           unit_price=6200, subtotal=31000),
        QuoteItemReadModel(id=4, position=4, quantity=3,
                           description="Servicio de instalación y mano de obra",
                           unit_price=25000, subtotal=75000),
    ),
)

# ── Generación ───────────────────────────────────────────────────────────────

out_dir = Path(__file__).parent / "tmp"
out_dir.mkdir(exist_ok=True)
out = out_dir / quote_pdf_filename(QUOTE)
render_quote_pdf(QUOTE, COMPANY, out)
print(f"PDF generado: {out}  ({out.stat().st_size:,} bytes)")

opener = "xdg-open" if sys.platform == "linux" else "open"
subprocess.Popen([opener, str(out)])
