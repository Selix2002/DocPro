from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from docpro_backend.schema import Client, Document, Report, ReportSection

from ..base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    model = Report

    def get_full(
        self, document_id: int
    ) -> tuple[Document, Report, list[ReportSection], Client]:
        result = (
            self._session.query(Document, Report)
            .join(Report, Report.document_id == Document.id)
            .filter(Document.id == document_id)
            .one_or_none()
        )
        if result is None:
            raise NoResultFound(f"Report document_id={document_id} not found")
        doc, report = result
        sections = (
            self._session.query(ReportSection)
            .filter(ReportSection.document_id == document_id)
            .order_by(ReportSection.parent_id.nulls_first(), ReportSection.position)
            .all()
        )
        return doc, report, sections, doc.client

    def create(self, client_id: int, number: str) -> tuple[Document, Report]:
        doc = Document(type="report", number=number, client_id=client_id, status="Borrador")
        self._session.add(doc)
        self._session.flush()

        report = Report(document_id=doc.id)
        self._session.add(report)
        self._session.flush()
        return doc, report

    def replace_sections(
        self, document_id: int, sections: list[dict]
    ) -> list[ReportSection]:
        """
        sections: flat list ordered parent-before-child.
        Each dict: {temp_id?, parent_temp_id?, title, content, content_json, position}
        """
        self._session.query(ReportSection).filter(
            ReportSection.document_id == document_id
        ).delete()
        self._session.flush()

        id_map: dict[str, int] = {}
        result: list[ReportSection] = []
        for s in sections:
            parent_id = id_map.get(s["parent_temp_id"]) if s.get("parent_temp_id") else None
            section = ReportSection(
                document_id=document_id,
                parent_id=parent_id,
                title=s["title"],
                content=s.get("content"),
                content_json=s.get("content_json"),
                position=s["position"],
            )
            self._session.add(section)
            self._session.flush()
            if s.get("temp_id"):
                id_map[s["temp_id"]] = section.id
            result.append(section)
        return result

    def delete(self, document_id: int) -> None:  # type: ignore[override]
        doc = self._session.get(Document, document_id)
        if doc is None:
            raise NoResultFound(f"Report document_id={document_id} not found")
        self._session.delete(doc)
        self._session.flush()
