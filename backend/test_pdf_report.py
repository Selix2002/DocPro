"""
Script de prueba visual del PDF de informe técnico.
Uso: uv run python test_pdf_report.py
Abre el PDF generado con el visor del sistema.
"""
import json
import subprocess
import sys
from pathlib import Path

from docpro_backend.dtos.config import CompanyProfileReadModel
from docpro_backend.dtos.reports import ReportReadModel, ReportSectionReadModel
from docpro_backend.services.pdf_service import render_report_pdf, report_pdf_filename

# ── Datos de prueba ──────────────────────────────────────────────────────────

COMPANY = CompanyProfileReadModel(
    id=1,
    name="Empresa Patagonia SpA",
    city="Punta Arenas",
    email="contacto@empresa.cl",
    phone="+56 61 222 3344",
)

REPORT = ReportReadModel(
    document_id=1,
    number="IT-0041",
    status="Borrador",
    client_id=1,
    client_name="Shell 21 de Mayo",
    client_rut=None,
    client_address=None,

    client_email=None,
    client_phone=None,
    created_at="2023-09-30T10:00:00Z",
    updated_at="2023-09-30T10:00:00Z",
    finalized_at=None,
    sent_at=None,
    sections=(
        # Sección de contexto: caja azul sin numeración
        ReportSectionReadModel(
            id=1,
            parent_id=None,
            title="Trabajo efectuado",
            content=None,
            content_json=json.dumps({
                "trabajo": "Mantención mantenedor de aderezos",
                "local": "Shell 21 de Mayo",
                "fecha": "30 de septiembre de 2023",
                "gas_refrigerante": "R-12",
            }, ensure_ascii=False),
            position=1,
        ),
        # Sección 1: lista numerada
        ReportSectionReadModel(
            id=2,
            parent_id=None,
            title="Inspección preliminar",
            content=(
                "Se evidencia gran acumulación de polvo, principalmente en el condensador y "
                "ventilador, lo que origina el recalentamiento del compresor.\n"
                "Evidencia de escarcha en paredes del evaporador."
            ),
            content_json=None,
            position=2,
        ),
        # Sección 2: lista numerada
        ReportSectionReadModel(
            id=3,
            parent_id=None,
            title="Descripción",
            content=(
                "Se desmontó ventilador del condensador, efectuando desarme para limpieza.\n"
                "Se realiza limpieza a condensador, compresor e inspección a termostato.\n"
                "Se inspecciona circuito de refrigeración, no encontrando evidencias de fugas.\n"
                "Inspección circuito eléctrico.\n"
                "Pruebas de funcionamiento."
            ),
            content_json=None,
            position=3,
        ),
        # Sección 3: lista numerada
        ReportSectionReadModel(
            id=4,
            parent_id=None,
            title="Conclusión",
            content=(
                "Se recomienda efectuar mantención a lo menos 2 veces al año, objeto evitar "
                "daños mayores que pudieran incluso dañar el compresor.\n"
                "De acuerdo a datos de placa del compresor, este usa refrigerante R-12, "
                "debiendo tener presente que este gas se encuentra sin disponibilidad en el "
                "comercio. De existir algún tipo de inconvenientes, se deberá reemplazar por R-134a.\n"
                "La formación de escarcha en la cámara destinada a la preservación del producto "
                "se debe a que esta expuesta a la humedad ambiental. Se sugiere tapar zona expuesta.\n"
                "Debido a desgaste ventilador condensador, se sugiere reemplazar en próxima mantención.\n"
                "Equipo opera correctamente, cumpliendo con los ciclos de trabajo ajustados."
            ),
            content_json=None,
            position=4,
        ),
    ),
)

FIRMA_NOMBRE = "Dagoberto Muñoz"
FIRMA_CARGO = "Técnico Refrigerante"

# ── Generación ───────────────────────────────────────────────────────────────

out_dir = Path(__file__).parent / "tmp"
out_dir.mkdir(exist_ok=True)
out = out_dir / report_pdf_filename(REPORT)

render_report_pdf(REPORT, COMPANY, FIRMA_NOMBRE, FIRMA_CARGO, out)
print(f"PDF generado: {out}  ({out.stat().st_size:,} bytes)")

opener = "xdg-open" if sys.platform == "linux" else "open"
subprocess.Popen([opener, str(out)])