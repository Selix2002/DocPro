from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from docpro_backend.schema import Client, Document

from ..base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    model = Document

    def list_history(
        self,
        type: str | None = None,
        status: str | None = None,
        client_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[tuple[Document, Client]]:
        q = (
            self._session.query(Document, Client)
            .join(Client, Client.id == Document.client_id)
        )
        if type is not None:
            q = q.filter(Document.type == type)
        if status is not None:
            q = q.filter(Document.status == status)
        if client_id is not None:
            q = q.filter(Document.client_id == client_id)
        if date_from is not None:
            q = q.filter(Document.created_at >= date_from)
        if date_to is not None:
            q = q.filter(Document.created_at <= date_to)
        return q.order_by(Document.updated_at.desc()).all()

    def search_fts(self, query: str) -> list[tuple[Document, Client]]:
        rows = self._session.execute(
            text("""
                SELECT d.id
                FROM fts_documents fts
                JOIN documents d ON fts.rowid = d.id
                WHERE fts_documents MATCH :query
                ORDER BY rank
            """),
            {"query": query},
        ).fetchall()
        doc_ids = [row[0] for row in rows]
        if not doc_ids:
            return []
        return (
            self._session.query(Document, Client)
            .join(Client, Client.id == Document.client_id)
            .filter(Document.id.in_(doc_ids))
            .all()
        )

    def update_status(self, document_id: int, status: str) -> Document:
        doc = self.get_by_id(document_id)
        doc.status = status
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if status == "Finalizado":
            doc.finalized_at = now
        elif status == "Enviado":
            doc.sent_at = now
        self._session.flush()
        return doc
