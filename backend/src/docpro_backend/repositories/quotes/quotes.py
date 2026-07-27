from datetime import datetime

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from docpro_backend.schema import Client, Document, Quote, QuoteItem

from ..base import BaseRepository


class QuoteRepository(BaseRepository[Quote]):
    model = Quote

    def get_full(
        self, document_id: int
    ) -> tuple[Document, Quote, list[QuoteItem], Client]:
        result = (
            self._session.query(Document, Quote)
            .join(Quote, Quote.document_id == Document.id)
            .filter(Document.id == document_id)
            .one_or_none()
        )
        if result is None:
            raise NoResultFound(f"Quote document_id={document_id} not found")
        doc, quote = result
        items = (
            self._session.query(QuoteItem)
            .filter(QuoteItem.document_id == document_id)
            .order_by(QuoteItem.position)
            .all()
        )
        return doc, quote, items, doc.client

    def create(
        self,
        client_id: int,
        number: str,
        issue_date: str,
        observations: str | None = None,
        observations_json: str | None = None,
        show_iva: bool = True,
        items: list[dict] | None = None,
    ) -> tuple[Document, Quote]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        doc = Document(
            type="quote", number=number, client_id=client_id, status="Borrador",
            created_at=now, updated_at=now,
        )
        self._session.add(doc)
        self._session.flush()

        items = items or []
        neto, iva, total, quote_items = _calc_totals(doc.id, items)

        quote = Quote(
            document_id=doc.id,
            issue_date=issue_date,
            observations=observations,
            observations_json=observations_json,
            show_iva=show_iva,
            neto=neto,
            iva=iva,
            total=total,
        )
        self._session.add(quote)
        for qi in quote_items:
            self._session.add(qi)
        self._session.flush()
        return doc, quote

    def update(
        self,
        document_id: int,
        issue_date: str,
        observations: str | None = None,
        observations_json: str | None = None,
        show_iva: bool = True,
        items: list[dict] | None = None,
    ) -> tuple[Document, Quote]:
        doc, quote, _, _ = self.get_full(document_id)
        quote.issue_date = issue_date
        quote.observations = observations
        quote.observations_json = observations_json
        quote.show_iva = show_iva

        self._session.query(QuoteItem).filter(
            QuoteItem.document_id == document_id
        ).delete()

        items = items or []
        neto, iva, total, quote_items = _calc_totals(document_id, items)
        quote.neto = neto
        quote.iva = iva
        quote.total = total
        for qi in quote_items:
            self._session.add(qi)

        self._session.flush()
        return doc, quote

    def delete(self, document_id: int) -> None:  # type: ignore[override]
        doc = self._session.get(Document, document_id)
        if doc is None:
            raise NoResultFound(f"Quote document_id={document_id} not found")
        self._session.delete(doc)
        self._session.flush()


def _calc_totals(
    document_id: int, items: list[dict]
) -> tuple[float, float, float, list[QuoteItem]]:
    quote_items = []
    for i, item in enumerate(items):
        subtotal = round(item["quantity"] * item["unit_price"], 2)
        quote_items.append(QuoteItem(
            document_id=document_id,
            position=item.get("position", i + 1),
            quantity=item["quantity"],
            description=item["description"],
            unit_price=item["unit_price"],
            subtotal=subtotal,
        ))
    neto = round(sum(qi.subtotal for qi in quote_items), 2)
    iva = round(neto * 0.19, 2)
    total = round(neto + iva, 2)
    return neto, iva, total, quote_items
