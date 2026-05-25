from __future__ import annotations

from dataclasses import dataclass, field

from docpro_backend.schema import Client, Document, Quote, QuoteItem


@dataclass
class QuoteItemInput:
    quantity: float
    description: str
    unit_price: float
    position: int = 0


@dataclass
class QuoteInput:
    client_id: int
    number: str
    issue_date: str
    observations: str | None = None
    items: list[QuoteItemInput] = field(default_factory=list)


@dataclass(frozen=True)
class QuoteItemReadModel:
    id: int
    position: int
    quantity: float
    description: str
    unit_price: float
    subtotal: float

    @classmethod
    def from_orm(cls, obj: QuoteItem) -> QuoteItemReadModel:
        return cls(
            id=obj.id,
            position=obj.position,
            quantity=obj.quantity,
            description=obj.description,
            unit_price=obj.unit_price,
            subtotal=obj.subtotal,
        )


@dataclass(frozen=True)
class QuoteReadModel:
    document_id: int
    number: str
    status: str
    issue_date: str
    observations: str | None
    neto: float
    iva: float
    total: float
    client_id: int
    client_name: str
    client_rut: str
    client_address: str | None
    client_email: str | None
    client_phone: str | None
    created_at: str
    updated_at: str
    finalized_at: str | None
    sent_at: str | None
    items: tuple[QuoteItemReadModel, ...]

    @classmethod
    def from_query(
        cls,
        doc: Document,
        quote: Quote,
        items: list[QuoteItem],
        client: Client,
    ) -> QuoteReadModel:
        return cls(
            document_id=doc.id,
            number=doc.number,
            status=doc.status,
            issue_date=quote.issue_date,
            observations=quote.observations,
            neto=quote.neto,
            iva=quote.iva,
            total=quote.total,
            client_id=client.id,
            client_name=client.name,
            client_rut=client.rut,
            client_address=client.address,
            client_email=client.email,
            client_phone=client.phone,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            finalized_at=doc.finalized_at,
            sent_at=doc.sent_at,
            items=tuple(QuoteItemReadModel.from_orm(i) for i in items),
        )
