from __future__ import annotations

from dataclasses import dataclass, field

from docpro_backend.schema import Client, Document, Report, ReportSection


@dataclass
class SectionInput:
    title: str
    position: int
    content: str | None = None
    content_json: str | None = None
    temp_id: str | None = None
    parent_temp_id: str | None = None


@dataclass
class ReportInput:
    client_id: int
    number: str


@dataclass(frozen=True)
class ReportSectionReadModel:
    id: int
    parent_id: int | None
    title: str
    content: str | None
    content_json: str | None
    position: int

    @classmethod
    def from_orm(cls, obj: ReportSection) -> ReportSectionReadModel:
        return cls(
            id=obj.id,
            parent_id=obj.parent_id,
            title=obj.title,
            content=obj.content,
            content_json=obj.content_json,
            position=obj.position,
        )


@dataclass(frozen=True)
class ReportReadModel:
    document_id: int
    number: str
    status: str
    client_id: int
    client_name: str
    client_rut: str
    client_address: str | None
    client_email: str | None
    client_phone: str | None
    created_at: str
    updated_at: str
    finalized_at: str | None
    sent_at: str | None
    sections: tuple[ReportSectionReadModel, ...]

    @classmethod
    def from_query(
        cls,
        doc: Document,
        report: Report,
        sections: list[ReportSection],
        client: Client,
    ) -> ReportReadModel:
        return cls(
            document_id=doc.id,
            number=doc.number,
            status=doc.status,
            client_id=client.id,
            client_name=client.name,
            client_rut=client.rut,
            client_address=client.address,
            client_email=client.email,
            client_phone=client.phone,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            finalized_at=doc.finalized_at,
            sent_at=doc.sent_at,
            sections=tuple(ReportSectionReadModel.from_orm(s) for s in sections),
        )
