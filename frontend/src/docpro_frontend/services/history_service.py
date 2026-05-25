from PySide6.QtCore import QObject, QThreadPool, Signal

from docpro_frontend.services.worker import Worker


class HistorialService(QObject):
    loaded = Signal(object)
    error  = Signal(str)

    def load(
        self,
        page:          int      = 0,
        page_size:     int      = 5,
        type_filter:   str | None = None,
        status_filter: str | None = None,
        search:        str      = "",
        sort:          str      = "Más reciente",
    ) -> None:
        params = {
            "page":          page,
            "page_size":     page_size,
            "type_filter":   type_filter,
            "status_filter": status_filter,
            "search":        search,
            "sort":          sort,
        }
        worker = Worker(lambda: _fetch_history(params))
        worker.signals.result.connect(self.loaded)
        worker.signals.error.connect(self.error)
        QThreadPool.globalInstance().start(worker)


# ---------------------------------------------------------------------------
# Internal fetch — runs in a worker thread, no Qt objects allowed here
# ---------------------------------------------------------------------------

def _fetch_history(params: dict) -> dict:
    from datetime import date, timedelta

    from sqlalchemy import func, or_

    from docpro_backend.db.session import SessionLocal
    from docpro_backend.schema import Client, Document

    page          = params["page"]
    page_size     = params["page_size"]
    type_filter   = params["type_filter"]
    status_filter = params["status_filter"]
    search        = params["search"]
    sort          = params["sort"]

    session = SessionLocal()
    try:
        # ── Stats ────────────────────────────────────────────────────────
        total_docs = session.query(func.count(Document.id)).scalar() or 0

        today  = date.today()
        monday = today - timedelta(days=today.weekday())
        completed_this_week = (
            session.query(func.count(Document.id))
            .filter(
                Document.finalized_at.isnot(None),
                Document.finalized_at >= monday.strftime("%Y-%m-%d"),
            )
            .scalar() or 0
        )

        approved_count = (
            session.query(func.count(Document.id))
            .filter(Document.status == "Aprobado")
            .scalar() or 0
        )

        # ── Filtered paginated list ───────────────────────────────────────
        def _apply(q):
            q = q.join(Client, Client.id == Document.client_id)
            if type_filter:
                q = q.filter(Document.type == type_filter)
            if status_filter:
                q = q.filter(Document.status == status_filter)
            if search:
                like = f"%{search}%"
                q = q.filter(
                    or_(Document.number.ilike(like), Client.name.ilike(like))
                )
            return q

        total_count = (
            _apply(session.query(func.count(Document.id))).scalar() or 0
        )
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        page = min(page, total_pages - 1)

        sort_col = {
            "Más reciente": Document.updated_at.desc(),
            "Más antiguo":  Document.updated_at.asc(),
            "A-Z":          Client.name.collate("NOCASE").asc(),
        }.get(sort, Document.updated_at.desc())

        rows = (
            _apply(session.query(Document, Client))
            .order_by(sort_col)
            .limit(page_size)
            .offset(page * page_size)
            .all()
        )

        return {
            "total_docs":          total_docs,
            "completed_this_week": completed_this_week,
            "approved_count":      approved_count,
            "current_page":        page,
            "total_pages":         total_pages,
            "rows": [
                {
                    "doc_id":      doc.id,
                    "number":      doc.number,
                    "doc_type":    doc.type,
                    "client_name": client.name,
                    "status":      doc.status,
                    "date_label":  _rel_time(doc.updated_at),
                }
                for doc, client in rows
            ],
        }
    finally:
        session.close()


def _rel_time(dt_str: str) -> str:
    from datetime import datetime
    if not dt_str:
        return ""
    try:
        dt = datetime.strptime(dt_str[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return ""
    seconds = (datetime.now() - dt).total_seconds()
    if seconds < 120:
        return "hace un momento"
    if seconds < 3600:
        return f"hace {int(seconds // 60)} min"
    if seconds < 7200:
        return "hace 1 h"
    if seconds < 86400:
        return f"hace {int(seconds // 3600)} h"
    if seconds < 172800:
        return "ayer"
    return f"hace {int(seconds // 86400)} días"
