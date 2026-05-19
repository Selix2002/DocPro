from datetime import datetime

from PySide6.QtCore import QObject, QThreadPool, Signal

from docpro_frontend.services.worker import Worker


class DashboardService(QObject):
    loaded = Signal(object)
    error = Signal(str)

    def load(self) -> None:
        worker = Worker(_fetch)
        worker.signals.result.connect(self.loaded)
        worker.signals.error.connect(self.error)
        QThreadPool.globalInstance().start(worker)


# ---------------------------------------------------------------------------
# Internal fetch — runs in a worker thread, no Qt objects allowed here
# ---------------------------------------------------------------------------

def _fetch() -> dict:
    from sqlalchemy import func

    from docpro_backend.db.session import SessionLocal
    from docpro_backend.schema import Client, Document, Setting

    session = SessionLocal()
    try:
        month_prefix = datetime.now().strftime("%Y-%m")

        # Totals
        total_quotes  = session.query(func.count(Document.id)).filter(Document.type == "quote").scalar() or 0
        total_reports = session.query(func.count(Document.id)).filter(Document.type == "report").scalar() or 0
        total_clients = session.query(func.count(Client.id)).scalar() or 0

        # Month summary
        month_quotes = session.query(func.count(Document.id)).filter(
            Document.type == "quote",
            Document.created_at.like(f"{month_prefix}%"),
        ).scalar() or 0
        month_reports = session.query(func.count(Document.id)).filter(
            Document.type == "report",
            Document.created_at.like(f"{month_prefix}%"),
        ).scalar() or 0
        month_clients = session.query(func.count(Document.client_id.distinct())).filter(
            Document.created_at.like(f"{month_prefix}%"),
        ).scalar() or 0

        # Recent documents (5 most recently updated)
        recent_rows = (
            session.query(Document, Client)
            .join(Client, Client.id == Document.client_id)
            .order_by(Document.updated_at.desc())
            .limit(5)
            .all()
        )

        # Drafts (all, ordered by most recently updated)
        draft_rows = (
            session.query(Document, Client)
            .join(Client, Client.id == Document.client_id)
            .filter(Document.status == "Borrador")
            .order_by(Document.updated_at.desc())
            .all()
        )

        # Next document numbers from settings
        def _setting(key: str, default: str) -> str:
            obj = session.get(Setting, key)
            return obj.value if obj else default

        quote_prefix  = _setting("quote_prefix",  "COT-")
        quote_number  = int(_setting("quote_number",  "1"))
        report_prefix = _setting("report_prefix", "IT-")
        report_number = int(_setting("report_number", "1"))

        return {
            "totales": {
                "cotizaciones": total_quotes,
                "informes":     total_reports,
                "clientes":     total_clients,
                "docs_total":   total_quotes + total_reports,
            },
            "resumen_mes": {
                "cotizaciones": month_quotes,
                "informes":     month_reports,
                "clientes":     month_clients,
                "pdfs":         0,
            },
            "documentos_recientes": [
                {
                    "document_id": doc.id,
                    "doc_type":    "cot" if doc.type == "quote" else "inf",
                    "title":       doc.number,
                    "subtitle":    f"{client.name} · {_rel_time(doc.updated_at)}",
                    "status":      doc.status,
                }
                for doc, client in recent_rows
            ],
            "borradores": [
                {
                    "document_id": doc.id,
                    "title":       doc.number,
                    "time":        _rel_time(doc.updated_at),
                }
                for doc, client in draft_rows
            ],
            "siguiente_cot": f"{quote_prefix}{str(quote_number).zfill(4)}",
            "siguiente_inf": f"{report_prefix}{str(report_number).zfill(4)}",
        }
    finally:
        session.close()


def _rel_time(dt_str: str) -> str:
    """Convert a stored datetime string to a Spanish relative label."""
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
