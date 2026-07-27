from __future__ import annotations

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class Quote(Base):
    __tablename__ = "quotes"

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    issue_date: Mapped[str]
    observations: Mapped[str | None]
    observations_json: Mapped[str | None]
    show_iva: Mapped[bool] = mapped_column(server_default="1")
    neto: Mapped[float] = mapped_column(server_default="0")
    iva: Mapped[float] = mapped_column(server_default="0")
    total: Mapped[float] = mapped_column(server_default="0")

    document: Mapped[Document] = relationship("Document", back_populates="quote")
    items: Mapped[list[QuoteItem]] = relationship(
        "QuoteItem",
        back_populates="quote",
        cascade="all, delete-orphan",
        order_by="QuoteItem.position",
    )


class QuoteItem(Base):
    __tablename__ = "quote_items"
    __table_args__ = (
        Index("idx_quote_items_position", "document_id", "position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("quotes.document_id", ondelete="CASCADE")
    )
    position: Mapped[int]
    quantity: Mapped[float]
    description: Mapped[str]
    unit_price: Mapped[float]
    subtotal: Mapped[float]

    quote: Mapped[Quote] = relationship("Quote", back_populates="items")
