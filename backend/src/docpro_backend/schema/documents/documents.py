from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("type IN ('quote', 'report')", name="ck_documents_type"),
        CheckConstraint(
            "status IN ('Borrador', 'Finalizado', 'Enviado', 'Aprobado', 'Rechazado')",
            name="ck_documents_status",
        ),
        Index("idx_documents_client_status", "client_id", "status", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    number: Mapped[str] = mapped_column(unique=True)
    status: Mapped[str] = mapped_column(server_default="'Borrador'")
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    created_at: Mapped[str] = mapped_column(server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[str] = mapped_column(server_default="CURRENT_TIMESTAMP")
    finalized_at: Mapped[str | None]
    sent_at: Mapped[str | None]

    client: Mapped[Client] = relationship("Client", back_populates="documents")
    quote: Mapped[Quote | None] = relationship(
        "Quote", back_populates="document", uselist=False, cascade="all, delete-orphan"
    )
    report: Mapped[Report | None] = relationship(
        "Report", back_populates="document", uselist=False, cascade="all, delete-orphan"
    )
    versions: Mapped[list[DocumentVersion]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )
    send_log: Mapped[list[SendLog]] = relationship(
        "SendLog", back_populates="document", cascade="all, delete-orphan"
    )
