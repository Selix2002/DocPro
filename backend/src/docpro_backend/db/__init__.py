"""Lazy re-exports — avoids building the engine before profiles bootstrap."""
from .session import SessionLocal, get_session

__all__ = ["engine", "SessionLocal", "get_session"]


def __getattr__(name: str):
    if name == "engine":
        from .engine import get_engine
        return get_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
