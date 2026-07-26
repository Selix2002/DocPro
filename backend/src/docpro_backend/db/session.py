"""Dynamic SessionLocal — always builds against the active profile's engine.

Call sites use `SessionLocal()` as before; the wrapper rebuilds the internal
sessionmaker whenever the engine is rebuilt (i.e. on profile switch).
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .engine import get_engine


_maker: sessionmaker[Session] | None = None
_maker_engine: Engine | None = None


def _get_maker() -> sessionmaker[Session]:
    global _maker, _maker_engine
    eng = get_engine()
    if _maker is None or _maker_engine is not eng:
        _maker = sessionmaker(bind=eng, autoflush=False, autocommit=False)
        _maker_engine = eng
    return _maker


def SessionLocal() -> Session:  # noqa: N802 — kept as attribute-style for callers
    return _get_maker()()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
