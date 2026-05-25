from sqlalchemy.orm import Session

from docpro_backend.schema import SendLog

from ..base import BaseRepository


class SendLogRepository(BaseRepository[SendLog]):
    model = SendLog

    def log_send(
        self, document_id: int, recipient: str, subject: str | None = None
    ) -> SendLog:
        entry = SendLog(document_id=document_id, recipient=recipient, subject=subject)
        self._session.add(entry)
        self._session.flush()
        return entry

    def list_by_document(self, document_id: int) -> list[SendLog]:
        return (
            self._session.query(SendLog)
            .filter(SendLog.document_id == document_id)
            .order_by(SendLog.sent_at.desc())
            .all()
        )
