from __future__ import annotations

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_num", name="uq_document_versions"),
        Index("idx_document_versions_doc", "document_id", "version_num"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )
    version_num: Mapped[int]
    snapshot_json: Mapped[str]
    created_at: Mapped[str] = mapped_column(server_default="CURRENT_TIMESTAMP")

    document: Mapped[Document] = relationship("Document", back_populates="versions")
