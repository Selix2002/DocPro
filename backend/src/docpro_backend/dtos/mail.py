from __future__ import annotations

from dataclasses import dataclass

from docpro_backend.schema import SendLog


@dataclass(frozen=True)
class SendLogReadModel:
    id: int
    document_id: int
    recipient: str
    subject: str | None
    sent_at: str

    @classmethod
    def from_orm(cls, obj: SendLog) -> SendLogReadModel:
        return cls(
            id=obj.id,
            document_id=obj.document_id,
            recipient=obj.recipient,
            subject=obj.subject,
            sent_at=obj.sent_at,
        )
