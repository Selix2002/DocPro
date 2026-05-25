"""
Restores child-table data (quotes, quote_items, reports, report_sections,
document_versions, send_log) that was wiped by the CASCADE bug in migration
d3e4f5a6b7c8.

Run from backend/:
    uv run python repair_data.py

Safe to run multiple times — skips tables that already have rows.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from docpro_backend.db.session import SessionLocal
from docpro_backend.schema import (
    DocumentVersion, Quote, QuoteItem, Report, ReportSection, SendLog,
)


def _already_repaired(session) -> bool:
    return session.query(Quote).count() > 0 or session.query(Report).count() > 0


def _repair_quotes(session) -> None:
    # ── COT-0023 (doc_id=1, Borrador) ───────────────────────────────────────
    q1 = Quote(document_id=1, issue_date="2026-05-18",
               observations="Incluye mano de obra y materiales. Vigencia: 15 días.",
               neto=375000.0, iva=71250.0, total=446250.0)
    session.add(q1)
    session.add_all([
        QuoteItem(document_id=1, position=1, quantity=1.0,
                  description="Mantención preventiva sistema HVAC",
                  unit_price=180000.0, subtotal=180000.0),
        QuoteItem(document_id=1, position=2, quantity=4.0,
                  description="Cambio filtros HEPA",
                  unit_price=25000.0, subtotal=100000.0),
        QuoteItem(document_id=1, position=3, quantity=1.0,
                  description="Revisión y recarga gas refrigerante R-410A",
                  unit_price=95000.0, subtotal=95000.0),
    ])

    # ── COT-0022 (doc_id=2, Enviado) ────────────────────────────────────────
    q2 = Quote(document_id=2, issue_date="2026-05-07", observations=None,
               neto=790000.0, iva=150100.0, total=940100.0)
    session.add(q2)
    session.add_all([
        QuoteItem(document_id=2, position=1, quantity=2.0,
                  description="Instalación sistema climatización split 12.000 BTU",
                  unit_price=320000.0, subtotal=640000.0),
        QuoteItem(document_id=2, position=2, quantity=1.0,
                  description="Obra civil e instalación eléctrica",
                  unit_price=150000.0, subtotal=150000.0),
    ])

    # ── COT-0021 (doc_id=3, Finalizado) ─────────────────────────────────────
    q3 = Quote(document_id=3, issue_date="2026-05-11",
               observations="Compresor importado. Plazo de entrega 5 días hábiles.",
               neto=880000.0, iva=167200.0, total=1047200.0)
    session.add(q3)
    session.add_all([
        QuoteItem(document_id=3, position=1, quantity=1.0,
                  description="Reemplazo compresor Scroll 5HP",
                  unit_price=680000.0, subtotal=680000.0),
        QuoteItem(document_id=3, position=2, quantity=1.0,
                  description="Instalación y configuración compresor",
                  unit_price=120000.0, subtotal=120000.0),
        QuoteItem(document_id=3, position=3, quantity=1.0,
                  description="Prueba de estanqueidad y carga refrigerante",
                  unit_price=80000.0, subtotal=80000.0),
    ])

    # ── COT-0020 (doc_id=4, Borrador) ───────────────────────────────────────
    q4 = Quote(document_id=4, issue_date="2026-05-16", observations=None,
               neto=155000.0, iva=29450.0, total=184450.0)
    session.add(q4)
    session.add_all([
        QuoteItem(document_id=4, position=1, quantity=1.0,
                  description="Diagnóstico sistema refrigeración cámara fría",
                  unit_price=65000.0, subtotal=65000.0),
        QuoteItem(document_id=4, position=2, quantity=1.0,
                  description="Limpieza evaporador y condensador",
                  unit_price=90000.0, subtotal=90000.0),
    ])

    # ── COT-0024 (doc_id=7, Finalizado — user-created, placeholder) ─────────
    session.add(Quote(document_id=7, issue_date="2026-05-21", observations=None,
                      neto=0.0, iva=0.0, total=0.0))

    session.flush()


def _repair_reports(session) -> None:
    # ── IT-0041 (doc_id=5, Finalizado) ──────────────────────────────────────
    session.add(Report(document_id=5))
    session.flush()

    ctx41 = ReportSection(
        document_id=5, parent_id=None, position=0,
        title="Datos del trabajo", content=None,
        content_json=json.dumps({
            "trabajo": "Mantención sistema refrigeración cámara fría",
            "local": "Planta Industrial Norte",
            "fecha": "15/05/2026",
            "gas_refrigerante": "R-410A",
        }),
    )
    s41_1 = ReportSection(
        document_id=5, parent_id=None, position=1,
        title="Inspección preliminar",
        content=(
            "- Se verificó el estado general del sistema\n"
            "- Temperatura de retorno: -2°C\n"
            "- Presión de succión: 3.2 bar\n"
            "- Presión de descarga: 14.8 bar"
        ),
        content_json=None,
    )
    s41_2 = ReportSection(
        document_id=5, parent_id=None, position=2,
        title="Trabajos realizados",
        content=(
            "- Limpieza filtros evaporador\n"
            "- Recarga gas refrigerante R-410A (800 gr)\n"
            "- Ajuste válvulas de expansión\n"
            "- Verificación sistema eléctrico"
        ),
        content_json=None,
    )
    s41_3 = ReportSection(
        document_id=5, parent_id=None, position=3,
        title="Conclusión",
        content=(
            "El sistema quedó operativo con parámetros dentro de rangos normales. "
            "Se recomienda mantención preventiva semestral."
        ),
        content_json=None,
    )
    session.add_all([ctx41, s41_1, s41_2, s41_3])
    session.flush()

    session.add(ReportSection(
        document_id=5, parent_id=s41_1.id, position=1,
        title="Estado del compresor",
        content=(
            "El compresor presenta desgaste moderado en válvulas de descarga. "
            "Se recomienda revisión en próximos 6 meses."
        ),
        content_json=None,
    ))
    session.flush()

    # ── IT-0040 (doc_id=6, Finalizado) ──────────────────────────────────────
    session.add(Report(document_id=6))
    session.flush()

    ctx40 = ReportSection(
        document_id=6, parent_id=None, position=0,
        title="Datos del trabajo", content=None,
        content_json=json.dumps({
            "trabajo": "Revisión equipos HVAC",
            "local": "Terminal Rodoviario",
            "fecha": "09/05/2026",
            "equipo": "Sistema centralizado 48.000 BTU",
        }),
    )
    s40_1 = ReportSection(
        document_id=6, parent_id=None, position=1,
        title="Diagnóstico general",
        content=(
            "- Sistema operativo al 85% de capacidad\n"
            "- Filtros de aire saturados\n"
            "- Nivel de refrigerante bajo"
        ),
        content_json=None,
    )
    s40_2 = ReportSection(
        document_id=6, parent_id=None, position=2,
        title="Trabajos ejecutados",
        content=(
            "- Reemplazo filtros de aire (x8)\n"
            "- Recarga refrigerante R-22 (600 gr)\n"
            "- Sellado fuga circuito retorno\n"
            "- Limpieza bandejas condensado"
        ),
        content_json=None,
    )
    session.add_all([ctx40, s40_1, s40_2])
    session.flush()

    session.add(ReportSection(
        document_id=6, parent_id=s40_1.id, position=1,
        title="Observaciones críticas",
        content=(
            "Se detectó fuga menor en unión de cañerías del circuito de retorno. "
            "Sellado realizado en terreno."
        ),
        content_json=None,
    ))
    session.flush()

    # ── IT-0043 (doc_id=8, Borrador — user-created, placeholder) ────────────
    session.add(Report(document_id=8))
    session.flush()


def _repair_versions(session) -> None:
    from sqlalchemy import select
    from docpro_backend.schema import Document

    non_borrador = [2, 3, 5, 6]
    for doc_id in non_borrador:
        doc = session.get(Document, doc_id)
        if doc is None:
            continue
        if doc.type == "quote":
            quote = session.get(Quote, doc_id)
            items = session.scalars(
                select(QuoteItem)
                .where(QuoteItem.document_id == doc_id)
                .order_by(QuoteItem.position)
            ).all()
            snapshot = {
                "version": 1,
                "document": {
                    "id": doc.id, "number": doc.number,
                    "status": doc.status, "client_id": doc.client_id,
                },
                "quote": {
                    "issue_date": quote.issue_date,
                    "observations": quote.observations,
                    "neto": quote.neto, "iva": quote.iva, "total": quote.total,
                },
                "items": [
                    {"position": i.position, "quantity": i.quantity,
                     "description": i.description,
                     "unit_price": i.unit_price, "subtotal": i.subtotal}
                    for i in items
                ],
            }
        else:
            sections = session.scalars(
                select(ReportSection)
                .where(ReportSection.document_id == doc_id)
                .order_by(ReportSection.position)
            ).all()
            snapshot = {
                "version": 1,
                "document": {
                    "id": doc.id, "number": doc.number,
                    "status": doc.status, "client_id": doc.client_id,
                },
                "sections": [
                    {"id": s.id, "parent_id": s.parent_id,
                     "title": s.title, "content": s.content,
                     "content_json": s.content_json, "position": s.position}
                    for s in sections
                ],
            }
        session.add(DocumentVersion(
            document_id=doc_id,
            version_num=1,
            snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        ))
    session.flush()


def _repair_send_log(session) -> None:
    from docpro_backend.schema import Client, Document
    doc = session.get(Document, 2)
    client = session.get(Client, doc.client_id)
    session.add(SendLog(
        document_id=2,
        recipient=client.email,
        subject=f"Cotización {doc.number} — Instalación climatización",
        sent_at=doc.sent_at,
    ))
    session.flush()


def repair() -> None:
    session = SessionLocal()
    try:
        if _already_repaired(session):
            print("Los datos ya están presentes. No se requiere reparación.")
            return

        print("Restaurando datos perdidos por el bug de CASCADE...")
        _repair_quotes(session)
        _repair_reports(session)
        _repair_versions(session)
        _repair_send_log(session)
        session.commit()
        print("  Cotizaciones restauradas: 5 (4 seeder + 1 placeholder COT-0024)")
        print("  Informes restaurados: 3 (2 seeder + 1 placeholder IT-0043)")
        print("  NOTA: Los ítems de COT-0024 no se pueden recuperar.")
        print("Reparación completada.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    repair()
