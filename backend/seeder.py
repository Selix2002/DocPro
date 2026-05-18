"""
Seed the DocPro database with realistic sample data.
Run from the backend/ directory:
    uv run python seeder.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import select
from sqlalchemy.orm import Session

from docpro_backend.db.engine import engine
from docpro_backend.db.session import SessionLocal
from docpro_backend.schema import Base
from docpro_backend.schema import (
    Client,
    CompanyProfile,
    Document,
    DocumentVersion,
    Quote,
    QuoteItem,
    Report,
    ReportSection,
    SectionTemplate,
    SendLog,
    Setting,
)


# ---------------------------------------------------------------------------
# company_profile
# ---------------------------------------------------------------------------

def _seed_company_profile(session: Session) -> None:
    session.add(CompanyProfile(
        name="Refrigeración Austral SpA",
        city="Punta Arenas",
        email="contacto@refrigeracionaustral.cl",
        phone="+56 61 234 5678",
    ))


# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------

def _seed_settings(session: Session) -> None:
    for key, value in [
        ("firma.nombre",   "Dagoberto Muñoz"),
        ("firma.cargo",    "Técnico Refrigerante"),
        ("quote.prefix",   "COT-"),
        ("quote.counter",  "23"),
        ("report.prefix",  "IT-"),
        ("report.counter", "41"),
    ]:
        session.add(Setting(key=key, value=value))


# ---------------------------------------------------------------------------
# clients
# ---------------------------------------------------------------------------

def _seed_clients(session: Session) -> dict[str, Client]:
    rows = [
        dict(rut="76.234.567-8", name="Empresa Patagonia SpA",
             address="Av. Colón 1234",         city="Punta Arenas",
             email="admin@patagonia.cl",         phone="+56 61 221 1111"),
        dict(rut="77.123.456-K", name="Industrias del Sur Ltda",
             address="Ruta 9 Km 12",            city="Punta Arenas",
             email="contacto@industriasdelsur.cl", phone="+56 61 222 2222"),
        dict(rut="76.987.654-3", name="Constructora Austral",
             address="Calle Magallanes 456",    city="Punta Arenas",
             email="obras@constructoraaustral.cl", phone="+56 61 223 3333"),
        dict(rut="78.456.789-2", name="Terminal Austral",
             address="Puerto Natales s/n",      city="Puerto Natales",
             email="admin@terminalaustral.cl",  phone="+56 61 241 4141"),
        dict(rut="76.345.678-9", name="Frigorífico Magallanes",
             address="Zona Industrial Norte 789", city="Punta Arenas",
             email="planta@frigorificomagallanes.cl", phone="+56 61 224 4444"),
        dict(rut="76.111.222-3", name="Shell 21 de Mayo",
             address="21 de Mayo 501",          city="Punta Arenas",
             email="estacion@shell21mayo.cl",   phone="+56 61 225 5555"),
    ]
    clients: dict[str, Client] = {}
    for row in rows:
        client = Client(**row)
        session.add(client)
        clients[row["rut"]] = client
    session.flush()
    return clients


# ---------------------------------------------------------------------------
# quotes
# ---------------------------------------------------------------------------

def _seed_quotes(session: Session, clients: dict[str, Client]) -> list[Document]:
    specs = [
        {
            "number": "COT-0023", "client_rut": "76.234.567-8",
            "status": "Borrador",
            "created_at": "2026-05-18 09:00:00", "updated_at": "2026-05-18 11:30:00",
            "finalized_at": None, "sent_at": None,
            "issue_date": "2026-05-18",
            "observations": "Incluye mano de obra y materiales. Vigencia: 15 días.",
            "items": [
                (1, 1.0, "Mantención preventiva sistema HVAC",             180_000.0),
                (2, 4.0, "Cambio filtros HEPA",                             25_000.0),
                (3, 1.0, "Revisión y recarga gas refrigerante R-410A",      95_000.0),
            ],
        },
        {
            "number": "COT-0022", "client_rut": "76.987.654-3",
            "status": "Enviado",
            "created_at": "2026-05-07 08:00:00", "updated_at": "2026-05-10 14:32:00",
            "finalized_at": "2026-05-10 10:00:00", "sent_at": "2026-05-10 14:32:00",
            "issue_date": "2026-05-07",
            "observations": None,
            "items": [
                (1, 2.0, "Instalación sistema climatización split 12.000 BTU", 320_000.0),
                (2, 1.0, "Obra civil e instalación eléctrica",                 150_000.0),
            ],
        },
        {
            "number": "COT-0021", "client_rut": "76.345.678-9",
            "status": "Finalizado",
            "created_at": "2026-05-11 10:00:00", "updated_at": "2026-05-12 16:00:00",
            "finalized_at": "2026-05-12 16:00:00", "sent_at": None,
            "issue_date": "2026-05-11",
            "observations": "Compresor importado. Plazo de entrega 5 días hábiles.",
            "items": [
                (1, 1.0, "Reemplazo compresor Scroll 5HP",               680_000.0),
                (2, 1.0, "Instalación y configuración compresor",          120_000.0),
                (3, 1.0, "Prueba de estanqueidad y carga refrigerante",     80_000.0),
            ],
        },
        {
            "number": "COT-0020", "client_rut": "77.123.456-K",
            "status": "Borrador",
            "created_at": "2026-05-16 14:00:00", "updated_at": "2026-05-16 15:45:00",
            "finalized_at": None, "sent_at": None,
            "issue_date": "2026-05-16",
            "observations": None,
            "items": [
                (1, 1.0, "Diagnóstico sistema refrigeración cámara fría",  65_000.0),
                (2, 1.0, "Limpieza evaporador y condensador",               90_000.0),
            ],
        },
    ]

    docs: list[Document] = []
    for spec in specs:
        doc = Document(
            type="quote",
            number=spec["number"],
            status=spec["status"],
            client_id=clients[spec["client_rut"]].id,
            created_at=spec["created_at"],
            updated_at=spec["updated_at"],
            finalized_at=spec["finalized_at"],
            sent_at=spec["sent_at"],
        )
        session.add(doc)
        session.flush()

        neto = sum(qty * up for _, qty, _, up in spec["items"])
        iva   = round(neto * 0.19, 2)
        total = round(neto + iva, 2)

        session.add(Quote(
            document_id=doc.id,
            issue_date=spec["issue_date"],
            observations=spec["observations"],
            neto=neto, iva=iva, total=total,
        ))
        for pos, qty, desc, unit_price in spec["items"]:
            session.add(QuoteItem(
                document_id=doc.id,
                position=pos,
                quantity=qty,
                description=desc,
                unit_price=unit_price,
                subtotal=round(qty * unit_price, 2),
            ))

        session.flush()
        docs.append(doc)

    return docs


# ---------------------------------------------------------------------------
# reports
# ---------------------------------------------------------------------------

def _seed_reports(session: Session, clients: dict[str, Client]) -> list[Document]:
    docs: list[Document] = []

    # ---- IT-0041 — Industrias del Sur — Finalizado -------------------------
    doc41 = Document(
        type="report", number="IT-0041", status="Finalizado",
        client_id=clients["77.123.456-K"].id,
        created_at="2026-05-15 08:00:00", updated_at="2026-05-17 09:00:00",
        finalized_at="2026-05-17 09:00:00", sent_at=None,
    )
    session.add(doc41)
    session.flush()
    session.add(Report(document_id=doc41.id))
    session.flush()

    ctx41 = ReportSection(
        document_id=doc41.id, parent_id=None, position=0,
        title="Datos del trabajo",
        content=None,
        content_json=json.dumps({
            "trabajo":          "Mantención sistema refrigeración cámara fría",
            "local":            "Planta Industrial Norte",
            "fecha":            "15/05/2026",
            "gas_refrigerante": "R-410A",
        }),
    )
    s41_1 = ReportSection(
        document_id=doc41.id, parent_id=None, position=1,
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
        document_id=doc41.id, parent_id=None, position=2,
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
        document_id=doc41.id, parent_id=None, position=3,
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
        document_id=doc41.id, parent_id=s41_1.id, position=1,
        title="Estado del compresor",
        content=(
            "El compresor presenta desgaste moderado en válvulas de descarga. "
            "Se recomienda revisión en próximos 6 meses."
        ),
        content_json=None,
    ))
    session.flush()
    docs.append(doc41)

    # ---- IT-0040 — Terminal Austral — Finalizado ---------------------------
    doc40 = Document(
        type="report", number="IT-0040", status="Finalizado",
        client_id=clients["78.456.789-2"].id,
        created_at="2026-05-09 09:00:00", updated_at="2026-05-13 11:30:00",
        finalized_at="2026-05-13 11:30:00", sent_at=None,
    )
    session.add(doc40)
    session.flush()
    session.add(Report(document_id=doc40.id))
    session.flush()

    ctx40 = ReportSection(
        document_id=doc40.id, parent_id=None, position=0,
        title="Datos del trabajo",
        content=None,
        content_json=json.dumps({
            "trabajo": "Revisión equipos HVAC",
            "local":   "Terminal Rodoviario",
            "fecha":   "09/05/2026",
            "equipo":  "Sistema centralizado 48.000 BTU",
        }),
    )
    s40_1 = ReportSection(
        document_id=doc40.id, parent_id=None, position=1,
        title="Diagnóstico general",
        content=(
            "- Sistema operativo al 85% de capacidad\n"
            "- Filtros de aire saturados\n"
            "- Nivel de refrigerante bajo"
        ),
        content_json=None,
    )
    s40_2 = ReportSection(
        document_id=doc40.id, parent_id=None, position=2,
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
        document_id=doc40.id, parent_id=s40_1.id, position=1,
        title="Observaciones críticas",
        content=(
            "Se detectó fuga menor en unión de cañerías del circuito de retorno. "
            "Sellado realizado en terreno."
        ),
        content_json=None,
    ))
    session.flush()
    docs.append(doc40)

    return docs


# ---------------------------------------------------------------------------
# document_versions
# ---------------------------------------------------------------------------

def _seed_document_versions(
    session: Session,
    quote_docs: list[Document],
    report_docs: list[Document],
) -> None:
    for doc in quote_docs:
        if doc.status == "Borrador":
            continue
        quote = session.get(Quote, doc.id)
        items = session.scalars(
            select(QuoteItem)
            .where(QuoteItem.document_id == doc.id)
            .order_by(QuoteItem.position)
        ).all()
        snapshot = {
            "version": 1,
            "document": {
                "id": doc.id, "type": doc.type, "number": doc.number,
                "status": doc.status, "client_id": doc.client_id,
                "created_at": doc.created_at, "updated_at": doc.updated_at,
                "finalized_at": doc.finalized_at, "sent_at": doc.sent_at,
            },
            "quote": {
                "issue_date": quote.issue_date, "observations": quote.observations,
                "neto": quote.neto, "iva": quote.iva, "total": quote.total,
            },
            "items": [
                {
                    "position": i.position, "quantity": i.quantity,
                    "description": i.description,
                    "unit_price": i.unit_price, "subtotal": i.subtotal,
                }
                for i in items
            ],
        }
        session.add(DocumentVersion(
            document_id=doc.id,
            version_num=1,
            snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        ))

    for doc in report_docs:
        sections = session.scalars(
            select(ReportSection)
            .where(ReportSection.document_id == doc.id)
            .order_by(ReportSection.position)
        ).all()
        snapshot = {
            "version": 1,
            "document": {
                "id": doc.id, "type": doc.type, "number": doc.number,
                "status": doc.status, "client_id": doc.client_id,
                "created_at": doc.created_at, "updated_at": doc.updated_at,
                "finalized_at": doc.finalized_at, "sent_at": doc.sent_at,
            },
            "sections": [
                {
                    "id": s.id, "parent_id": s.parent_id,
                    "title": s.title, "content": s.content,
                    "content_json": s.content_json, "position": s.position,
                }
                for s in sections
            ],
        }
        session.add(DocumentVersion(
            document_id=doc.id,
            version_num=1,
            snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        ))


# ---------------------------------------------------------------------------
# send_log
# ---------------------------------------------------------------------------

def _seed_send_log(session: Session, quote_docs: list[Document]) -> None:
    for doc in quote_docs:
        if doc.status != "Enviado":
            continue
        client = session.get(Client, doc.client_id)
        session.add(SendLog(
            document_id=doc.id,
            recipient=client.email,
            subject=f"Cotización {doc.number} — Instalación climatización",
            sent_at=doc.sent_at,
        ))


# ---------------------------------------------------------------------------
# section_templates
# ---------------------------------------------------------------------------

def _seed_section_templates(session: Session) -> None:
    session.add_all([
        SectionTemplate(
            name="Inspección preliminar",
            title="Inspección preliminar",
            content=None,
            content_json=json.dumps({
                "estado_general":     "",
                "temperatura_retorno": "",
                "presion_succion":    "",
                "presion_descarga":   "",
            }),
        ),
        SectionTemplate(
            name="Trabajos realizados",
            title="Trabajos realizados",
            content="- \n- \n- ",
            content_json=None,
        ),
        SectionTemplate(
            name="Conclusión y recomendaciones",
            title="Conclusión y recomendaciones",
            content="",
            content_json=None,
        ),
    ])


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def seed() -> None:
    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        if session.query(CompanyProfile).count() > 0:
            print("La base de datos ya tiene datos. Omitiendo seeder.")
            return

        print("Sembrando base de datos...")

        _seed_company_profile(session)
        _seed_settings(session)
        session.flush()

        clients = _seed_clients(session)
        quote_docs = _seed_quotes(session, clients)
        report_docs = _seed_reports(session, clients)

        _seed_document_versions(session, quote_docs, report_docs)
        _seed_send_log(session, quote_docs)
        _seed_section_templates(session)

        session.commit()

        print(f"  {len(clients)} clientes")
        print(f"  {len(quote_docs)} cotizaciones (COT-0020 a COT-0023)")
        print(f"  {len(report_docs)} informes (IT-0040 a IT-0041)")
        print("Seeder completado.")

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
