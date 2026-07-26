"""SQLAlchemy engine — resolves the DB path from the active ProfileContext.

The engine is lazy: it is created on first `get_engine()` call and rebuilt
whenever `switch_profile()` is invoked. Before profiles are initialized
(e.g. during the one-shot migration on first launch), `get_db_path()` falls
back to the legacy location so the old DB can be located and moved.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from .profile_context import ProfileContext


_engine: Engine | None = None


def legacy_db_path() -> Path:
    """Pre-profiles DB location. Used only during the initial migration."""
    if getattr(sys, "frozen", False):
        base = Path(os.environ["APPDATA"]) / "DocPro"
    else:
        base = Path(__file__).resolve().parents[4]  # repo root
    base.mkdir(parents=True, exist_ok=True)
    return base / "docpro.db"


def get_db_path() -> Path:
    """DB path for the active profile, or legacy path if not yet initialized."""
    ctx = ProfileContext.get()
    if ctx.is_initialized():
        return ctx.db_path()
    return legacy_db_path()


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine(get_db_path())
    return _engine


def switch_profile() -> Engine:
    """Dispose current engine and rebuild against the new active profile.

    Call after ProfileContext.set_active(...).
    """
    dispose_engine()
    return get_engine()


def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def _build_engine(db_path: Path) -> Engine:
    eng = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(conn, _record):  # noqa: ANN001 — SQLAlchemy signature
        conn.execute("PRAGMA foreign_keys = ON")

    return eng


def __getattr__(name: str):
    """Lazy `engine` attribute — preserves `from ...engine import engine` imports."""
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
