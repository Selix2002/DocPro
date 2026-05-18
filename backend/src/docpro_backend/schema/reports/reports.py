from __future__ import annotations

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Report(Base):
    __tablename__ = "reports"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )

    document: Mapped[Document] = relationship("Document", back_populates="report")
    sections: Mapped[list[ReportSection]] = relationship(
        "ReportSection",
        back_populates="report",
        cascade="all, delete-orphan",
        foreign_keys="[ReportSection.document_id]",
    )


class ReportSection(Base):
    __tablename__ = "report_sections"
    __table_args__ = (
        Index("idx_report_sections_parent", "document_id", "parent_id", "position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("reports.document_id", ondelete="CASCADE")
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("report_sections.id", ondelete="CASCADE")
    )
    title: Mapped[str]
    content: Mapped[str | None]
    content_json: Mapped[str | None]
    position: Mapped[int]

    report: Mapped[Report] = relationship(
        "Report",
        back_populates="sections",
        foreign_keys=[document_id],
    )
    children: Mapped[list[ReportSection]] = relationship(
        "ReportSection",
        back_populates="parent",
        foreign_keys="[ReportSection.parent_id]",
    )
    parent: Mapped[ReportSection | None] = relationship(
        "ReportSection",
        back_populates="children",
        remote_side=[id],
        foreign_keys="[ReportSection.parent_id]",
    )
