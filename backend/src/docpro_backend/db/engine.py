import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine


def get_db_path() -> Path:
    return _db_path()


def _db_path() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(os.environ["APPDATA"]) / "DocPro"
    else:
        base = Path(__file__).resolve().parents[4]  # repo root
    base.mkdir(parents=True, exist_ok=True)
    return base / "docpro.db"


engine = create_engine(
    f"sqlite:///{_db_path()}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(conn, _record):
    conn.execute("PRAGMA foreign_keys = ON")
