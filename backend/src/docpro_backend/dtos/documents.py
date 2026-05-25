from __future__ import annotations

from dataclasses import dataclass

from docpro_backend.schema import Client, Document, DocumentVersion


@dataclass(frozen=True)
class DocumentSummary:
    id: int
    type: str
    number: str
    status: str
    client_id: int
    client_name: str
    client_rut: str
    created_at: str
    updated_at: str
    finalized_at: str | None
    sent_at: str | None

    @classmethod
    def from_orm(cls, doc: Document, client: Client) -> DocumentSummary:
        return cls(
            id=doc.id,
            type=doc.type,
            number=doc.number,
            status=doc.status,
            client_id=client.id,
            client_name=client.name,
            client_rut=client.rut,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            finalized_at=doc.finalized_at,
            sent_at=doc.sent_at,
        )


@dataclass(frozen=True)
class DocumentVersionSummary:
    id: int
    document_id: int
    version_num: int
    created_at: str

    @classmethod
    def from_orm(cls, obj: DocumentVersion) -> DocumentVersionSummary:
        return cls(
            id=obj.id,
            document_id=obj.document_id,
            version_num=obj.version_num,
            created_at=obj.created_at,
        )
