import re

from PySide6.QtCore import QObject, QThreadPool, QTimer, Signal

from docpro_frontend.services.worker import Worker


def _sanitize(raw: str) -> str:
    tokens = raw.split()
    safe = []
    for tok in tokens:
        tok = re.sub(r'["\(\)\*\:\^\\]', "", tok)
        if tok:
            safe.append(f'"{tok}"*')
    return " ".join(safe)


def _run(fts_query: str, type_filter: str | None, status_filter: str | None) -> list[dict]:
    from sqlalchemy import text
    from docpro_backend.db.session import SessionLocal

    session = SessionLocal()
    try:
        conditions = ["fts_documents MATCH :q"]
        params: dict = {"q": fts_query}

        if type_filter:
            conditions.append("d.type = :type")
            params["type"] = type_filter
        if status_filter:
            conditions.append("d.status = :status")
            params["status"] = status_filter

        where = " AND ".join(conditions)
        sql = text(f"""
            SELECT d.id, d.number, d.type, d.status, c.name
            FROM fts_documents fts
            JOIN documents d ON fts.rowid = d.id
            JOIN clients  c ON c.id = d.client_id
            WHERE {where}
            ORDER BY rank
            LIMIT 8
        """)
        rows = session.execute(sql, params).fetchall()
        return [
            {
                "doc_id":      row[0],
                "doc_type":    "cot" if row[2] == "quote" else "inf",
                "number":      row[1] or "",
                "client_name": row[4] or "",
                "status":      row[3] or "",
            }
            for row in rows
        ]
    finally:
        session.close()


class SearchService(QObject):
    results_ready = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._query_id     = 0
        self._pending      = ""
        self._type_filter: str | None   = None
        self._status_filter: str | None = None

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self._fire)

    def search(self, text: str) -> None:
        self._pending = text.strip()
        self._timer.start()

    def set_filters(self, type_filter: str | None, status_filter: str | None) -> None:
        self._type_filter   = type_filter
        self._status_filter = status_filter
        # Re-fire immediately with current query
        if self._pending:
            self._timer.start()

    def _fire(self) -> None:
        raw = self._pending
        self._query_id += 1
        qid = self._query_id

        if len(raw) < 2:
            self.results_ready.emit([])
            return

        fts = _sanitize(raw)
        if not fts:
            self.results_ready.emit([])
            return

        tf = self._type_filter
        sf = self._status_filter
        worker = Worker(lambda: _run(fts, tf, sf))
        worker.signals.result.connect(lambda r: self._on_result(r, qid))
        worker.signals.error.connect(lambda _: self._on_result([], qid))
        QThreadPool.globalInstance().start(worker)

    def _on_result(self, results: list, qid: int) -> None:
        if qid == self._query_id:
            self.results_ready.emit(results)
