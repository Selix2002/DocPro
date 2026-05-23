from PySide6.QtCore import QObject, QThreadPool, Signal

from docpro_frontend.services.worker import Worker


class ClientsService(QObject):
    loaded = Signal(object)
    error  = Signal(str)

    def load(
        self,
        page:      int = 0,
        page_size: int = 12,
        search:    str = "",
        sort:      str = "Más reciente",
    ) -> None:
        params = {
            "page":      page,
            "page_size": page_size,
            "search":    search,
            "sort":      sort,
        }
        worker = Worker(lambda: _fetch_clients(params))
        worker.signals.result.connect(self.loaded)
        worker.signals.error.connect(self.error)
        QThreadPool.globalInstance().start(worker)


# ---------------------------------------------------------------------------
# Internal fetch — runs in a worker thread, no Qt objects allowed here
# ---------------------------------------------------------------------------

def _fetch_clients(params: dict) -> dict:
    from datetime import date

    from sqlalchemy import func, or_

    from docpro_backend.db.session import SessionLocal
    from docpro_backend.schema import Client, Document
    from docpro_backend.schema.quotes.quotes import Quote

    page      = params["page"]
    page_size = params["page_size"]
    search    = params["search"]
    sort      = params["sort"]

    session = SessionLocal()
    try:
        # ── Stats ──────────────────────────────────────────────────────────
        total_clients = session.query(func.count(Client.id)).scalar() or 0

        today = date.today()
        first_of_month = today.replace(day=1).strftime("%Y-%m-%d")
        new_this_month = (
            session.query(func.count(Client.id))
            .filter(Client.created_at >= first_of_month)
            .scalar() or 0
        )

        total_docs = session.query(func.count(Document.id)).scalar() or 0

        potential_income = (
            session.query(func.sum(Quote.total))
            .join(Document, Document.id == Quote.document_id)
            .filter(Document.status == "Aprobado")
            .scalar() or 0.0
        )

        # ── doc_count subquery (always needed for output rows) ─────────────
        doc_count_sub = (
            session.query(Document.client_id, func.count(Document.id).label("cnt"))
            .group_by(Document.client_id)
            .subquery()
        )

        # ── Sort column ────────────────────────────────────────────────────
        sort_col = {
            "Más reciente":  Client.created_at.desc(),
            "Nombre (A-Z)":  Client.name.collate("NOCASE").asc(),
            "Más documentos": func.coalesce(doc_count_sub.c.cnt, 0).desc(),
        }.get(sort, Client.created_at.desc())

        # ── Pagination count ───────────────────────────────────────────────
        count_q = session.query(func.count(Client.id))
        if search:
            like = f"%{search}%"
            count_q = count_q.filter(
                or_(
                    Client.name.ilike(like),
                    Client.rut.ilike(like),
                    Client.email.ilike(like),
                )
            )
        total_count = count_q.scalar() or 0
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        # ── Paginated rows ─────────────────────────────────────────────────
        base_q = session.query(Client)
        if search:
            like = f"%{search}%"
            base_q = base_q.filter(
                or_(
                    Client.name.ilike(like),
                    Client.rut.ilike(like),
                    Client.email.ilike(like),
                )
            )

        rows = (
            base_q
            .outerjoin(doc_count_sub, doc_count_sub.c.client_id == Client.id)
            .add_columns(func.coalesce(doc_count_sub.c.cnt, 0).label("doc_count"))
            .order_by(sort_col)
            .limit(page_size)
            .offset(page * page_size)
            .all()
        )

        return {
            "total_clients":    total_clients,
            "new_this_month":   new_this_month,
            "total_docs":       total_docs,
            "potential_income": float(potential_income),
            "current_page":     page,
            "total_pages":      total_pages,
            "rows": [
                {
                    "client_id":        client.id,
                    "name":             client.name,
                    "rut":              client.rut,
                    "email":            client.email,
                    "phone":            client.phone,
                    "doc_count":        int(doc_count),
                    "created_at_label": _created_at_label(client.created_at),
                }
                for client, doc_count in rows
            ],
        }
    finally:
        session.close()


_MONTH_ES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def _created_at_label(dt_str: str) -> str:
    if not dt_str:
        return ""
    try:
        from datetime import datetime
        dt = datetime.strptime(dt_str[:10], "%Y-%m-%d")
        return f"{_MONTH_ES[dt.month]} {dt.year}"
    except (ValueError, KeyError):
        return ""
