import json
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from docpro_backend.schema import (
    Document,
    DocumentVersion,
    Quote,
    QuoteItem,
    ReportSection,
)

from ..base import BaseRepository


class DocumentVersionRepository(BaseRepository[DocumentVersion]):
    model = DocumentVersion

    def save_snapshot(self, document_id: int, snapshot_json: str) -> DocumentVersion:
        max_ver = (
            self._session.query(func.max(DocumentVersion.version_num))
            .filter(DocumentVersion.document_id == document_id)
            .scalar()
        ) or 0
        version = DocumentVersion(
            document_id=document_id,
            version_num=max_ver + 1,
            snapshot_json=snapshot_json,
        )
        self._session.add(version)
        self._session.flush()
        return version

    def list_versions(self, document_id: int) -> list[DocumentVersion]:
        return (
            self._session.query(DocumentVersion)
            .filter(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_num.desc())
            .all()
        )

    def get_snapshot(self, document_id: int, version_num: int) -> DocumentVersion:
        obj = (
            self._session.query(DocumentVersion)
            .filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_num == version_num,
            )
            .one_or_none()
        )
        if obj is None:
            raise NoResultFound(
                f"DocumentVersion document_id={document_id} version_num={version_num} not found"
            )
        return obj

    def restore(self, document_id: int, version_num: int) -> Document:
        dv = self.get_snapshot(document_id, version_num)
        snap = json.loads(dv.snapshot_json)

        doc = self._session.get(Document, document_id)
        if doc is None:
            raise NoResultFound(f"Document id={document_id} not found")

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        doc.status = "Borrador"
        doc.updated_at = now
        doc.finalized_at = None
        doc.sent_at = None

        if "quote" in snap:
            q_data = snap["quote"]
            quote = self._session.get(Quote, document_id)
            if quote:
                quote.issue_date = q_data["issue_date"]
                quote.observations = q_data.get("observations")
                quote.neto = q_data["neto"]
                quote.iva = q_data["iva"]
                quote.total = q_data["total"]
            self._session.query(QuoteItem).filter(
                QuoteItem.document_id == document_id
            ).delete()
            for item in snap.get("items", []):
                self._session.add(QuoteItem(
                    document_id=document_id,
                    position=item["position"],
                    quantity=item["quantity"],
                    description=item["description"],
                    unit_price=item["unit_price"],
                    subtotal=item["subtotal"],
                ))
        else:
            self._session.query(ReportSection).filter(
                ReportSection.document_id == document_id
            ).delete()
            _insert_sections(self._session, snap.get("sections", []), document_id)

        self._session.flush()
        return doc


def _insert_sections(
    session: Session,
    sections: list[dict],
    document_id: int,
    parent_id: int | None = None,
) -> None:
    for s in sorted(sections, key=lambda x: x["position"]):
        section = ReportSection(
            document_id=document_id,
            parent_id=parent_id,
            title=s["title"],
            content=s.get("content"),
            content_json=s.get("content_json"),
            position=s["position"],
        )
        session.add(section)
        session.flush()
        if s.get("children"):
            _insert_sections(session, s["children"], document_id, section.id)
