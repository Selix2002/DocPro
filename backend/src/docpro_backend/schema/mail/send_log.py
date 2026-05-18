from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class SendLog(Base):
    __tablename__ = "send_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE")
    )
    recipient: Mapped[str]
    subject: Mapped[str | None]
    sent_at: Mapped[str] = mapped_column(server_default="CURRENT_TIMESTAMP")

    document: Mapped[Document] = relationship("Document", back_populates="send_log")
