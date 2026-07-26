import base64
import json
from pathlib import Path

from sqlalchemy.orm import Session

from docpro_backend.dtos.reports import ReportInput, ReportReadModel, SectionInput
from docpro_backend.repositories.config.company_profile import CompanyProfileRepository
from docpro_backend.repositories.config.settings import SettingRepository
from docpro_backend.repositories.documents.document_versions import DocumentVersionRepository
from docpro_backend.repositories.reports.reports import ReportRepository
from docpro_backend.services.number_service import next_number


def create_report(session: Session, data: ReportInput) -> ReportReadModel:
    number = next_number(session, "report")
    repo = ReportRepository(session)
    doc, _report = repo.create(client_id=data.client_id, number=number)
    doc, report, sections, client = repo.get_full(doc.id)
    return ReportReadModel.from_query(doc, report, sections, client)


def update_sections(
    session: Session, document_id: int, sections: list[SectionInput]
) -> ReportReadModel:
    repo = ReportRepository(session)
    repo.replace_sections(
        document_id=document_id,
        sections=[
            {
                "temp_id": s.temp_id,
                "parent_temp_id": s.parent_temp_id,
                "title": s.title,
                "content": s.content,
                "content_json": s.content_json,
                "position": s.position,
            }
            for s in sections
        ],
    )
    doc, report, sections_orm, client = repo.get_full(document_id)
    result = ReportReadModel.from_query(doc, report, sections_orm, client)
    _save_snapshot(session, result)
    return result


def finalize_report(session: Session, document_id: int) -> ReportReadModel:
    from docpro_backend.repositories.documents.documents import DocumentRepository
    DocumentRepository(session).update_status(document_id, "Finalizado")
    repo = ReportRepository(session)
    doc, report, sections, client = repo.get_full(document_id)
    result = ReportReadModel.from_query(doc, report, sections, client)
    _save_snapshot(session, result)
    return result


def duplicate_report(session: Session, source_doc_id: int) -> ReportReadModel:
    source = get_report(session, source_doc_id)
    new_inp = ReportInput(client_id=source.client_id, number="")
    new_doc = create_report(session, new_inp)
    section_inputs = [
        SectionInput(
            temp_id=f"s{s.id}",
            parent_temp_id=f"s{s.parent_id}" if s.parent_id is not None else None,
            title=s.title,
            content=s.content,
            content_json=s.content_json,
            position=s.position,
        )
        for s in source.sections
    ]
    return update_sections(session, new_doc.document_id, section_inputs)


def get_report(session: Session, document_id: int) -> ReportReadModel:
    repo = ReportRepository(session)
    doc, report, sections, client = repo.get_full(document_id)
    return ReportReadModel.from_query(doc, report, sections, client)


def get_company(session: Session):
    from docpro_backend.dtos.config import CompanyProfileReadModel
    profile = CompanyProfileRepository(session).get()
    return CompanyProfileReadModel.from_orm(profile) if profile else None


def get_firma(session: Session) -> tuple[str | None, str | None, str | None]:
    from docpro_backend.repositories.config.company_profile import CompanyProfileRepository
    repo = SettingRepository(session)
    nombre = repo.get_or_none("firma.nombre") or None
    cargo  = repo.get_or_none("firma.cargo")  or None
    if nombre is None:
        profile = CompanyProfileRepository(session).get()
        if profile and profile.name:
            nombre = profile.name
    imagen_b64: str | None = None
    stored = repo.get_or_none("firma.imagen") or ""
    if stored:
        img_path = _resolve_firma_path(stored)
        if img_path is not None and img_path.exists():
            data = img_path.read_bytes()
            suffix = img_path.suffix.lower().lstrip(".")
            mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix or "png"
            imagen_b64 = f"data:image/{mime};base64,{base64.b64encode(data).decode()}"
    return nombre, cargo, imagen_b64


def _resolve_firma_path(stored: str) -> Path | None:
    """Resolve a stored firma value (filename in active profile, or legacy abs path)."""
    from docpro_backend.db.profile_context import ProfileContext

    p = Path(stored)
    if p.is_absolute():
        return p
    ctx = ProfileContext.get()
    if ctx.is_initialized():
        return ctx.assets_dir() / stored
    return None


def _save_snapshot(session: Session, report: ReportReadModel) -> None:
    snapshot = {
        "version": 1,
        "document": {
            "id": report.document_id,
            "number": report.number,
            "status": report.status,
            "client_id": report.client_id,
        },
        "sections": [
            {
                "id": s.id,
                "parent_id": s.parent_id,
                "title": s.title,
                "content": s.content,
                "content_json": s.content_json,
                "position": s.position,
            }
            for s in report.sections
        ],
    }
    DocumentVersionRepository(session).save_snapshot(
        document_id=report.document_id,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
    )
