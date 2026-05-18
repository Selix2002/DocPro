from __future__ import annotations
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True)
    rut: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    address: Mapped[str | None]
    city: Mapped[str | None]
    email: Mapped[str | None]
    phone: Mapped[str | None]
    created_at: Mapped[str] = mapped_column(server_default="CURRENT_TIMESTAMP")

    documents: Mapped[list[Document]] = relationship("Document", back_populates="client")
