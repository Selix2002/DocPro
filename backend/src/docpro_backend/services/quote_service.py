import json

from sqlalchemy.orm import Session

from docpro_backend.dtos import QuoteInput, QuoteItemInput, QuoteReadModel
from docpro_backend.repositories.config.company_profile import CompanyProfileRepository
from docpro_backend.repositories.documents.document_versions import DocumentVersionRepository
from docpro_backend.repositories.quotes.quotes import QuoteRepository
from docpro_backend.services.number_service import next_number, sync_counter


def create_quote(session: Session, data: QuoteInput) -> QuoteReadModel:
    if data.number and data.number.strip():
        number = data.number.strip()
        sync_counter(session, "quote", number)
    else:
        number = next_number(session, "quote")
    repo = QuoteRepository(session)
    doc, quote = repo.create(
        client_id=data.client_id,
        number=number,
        issue_date=data.issue_date,
        observations=data.observations,
        show_iva=data.show_iva,
        items=[
            {
                "quantity": i.quantity,
                "description": i.description,
                "unit_price": i.unit_price,
                "position": idx + 1,
            }
            for idx, i in enumerate(data.items)
        ],
    )
    doc, quote, items, client = repo.get_full(doc.id)
    result = QuoteReadModel.from_query(doc, quote, items, client)
    _save_snapshot(session, result)
    return result


def update_quote(session: Session, document_id: int, data: QuoteInput) -> QuoteReadModel:
    repo = QuoteRepository(session)
    repo.update(
        document_id=document_id,
        issue_date=data.issue_date,
        observations=data.observations,
        show_iva=data.show_iva,
        items=[
            {
                "quantity": i.quantity,
                "description": i.description,
                "unit_price": i.unit_price,
                "position": idx + 1,
            }
            for idx, i in enumerate(data.items)
        ],
    )
    doc, quote, items, client = repo.get_full(document_id)
    return QuoteReadModel.from_query(doc, quote, items, client)


def finalize_quote(session: Session, document_id: int) -> QuoteReadModel:
    from docpro_backend.repositories.documents.documents import DocumentRepository
    DocumentRepository(session).update_status(document_id, "Finalizado")
    repo = QuoteRepository(session)
    doc, quote, items, client = repo.get_full(document_id)
    result = QuoteReadModel.from_query(doc, quote, items, client)
    _save_snapshot(session, result)
    return result


def approve_quote(session: Session, document_id: int) -> QuoteReadModel:
    from docpro_backend.repositories.documents.documents import DocumentRepository
    DocumentRepository(session).update_status(document_id, "Aprobado")
    repo = QuoteRepository(session)
    doc, quote, items, client = repo.get_full(document_id)
    return QuoteReadModel.from_query(doc, quote, items, client)


def reject_quote(session: Session, document_id: int) -> QuoteReadModel:
    from docpro_backend.repositories.documents.documents import DocumentRepository
    DocumentRepository(session).update_status(document_id, "Rechazado")
    repo = QuoteRepository(session)
    doc, quote, items, client = repo.get_full(document_id)
    return QuoteReadModel.from_query(doc, quote, items, client)


def duplicate_quote(session: Session, source_doc_id: int) -> QuoteReadModel:
    from datetime import date
    source = get_quote(session, source_doc_id)
    data = QuoteInput(
        client_id=source.client_id,
        number="",
        issue_date=date.today().strftime("%Y-%m-%d"),
        observations=source.observations,
        show_iva=source.show_iva,
        items=[
            QuoteItemInput(
                quantity=i.quantity,
                description=i.description,
                unit_price=i.unit_price,
                position=i.position,
            )
            for i in source.items
        ],
    )
    return create_quote(session, data)


def get_quote(session: Session, document_id: int) -> QuoteReadModel:
    repo = QuoteRepository(session)
    doc, quote, items, client = repo.get_full(document_id)
    return QuoteReadModel.from_query(doc, quote, items, client)


def get_company(session: Session):
    from docpro_backend.dtos.config import CompanyProfileReadModel
    profile = CompanyProfileRepository(session).get()
    return CompanyProfileReadModel.from_orm(profile) if profile else None


def _save_snapshot(session: Session, quote: QuoteReadModel) -> None:
    snapshot = {
        "version": 1,
        "document": {
            "id": quote.document_id,
            "number": quote.number,
            "status": quote.status,
            "client_id": quote.client_id,
        },
        "quote": {
            "issue_date": quote.issue_date,
            "observations": quote.observations,
            "neto": quote.neto,
            "iva": quote.iva,
            "total": quote.total,
        },
        "items": [
            {
                "position": i.position,
                "quantity": i.quantity,
                "description": i.description,
                "unit_price": i.unit_price,
                "subtotal": i.subtotal,
            }
            for i in quote.items
        ],
    }
    DocumentVersionRepository(session).save_snapshot(
        document_id=quote.document_id,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
    )
