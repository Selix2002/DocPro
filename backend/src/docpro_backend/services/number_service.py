from sqlalchemy.orm import Session

from docpro_backend.repositories.config.settings import SettingRepository

_COUNTER_KEYS = {
    "quote": "counter.quote",
    "report": "counter.report",
}
_PREFIXES = {
    "quote": "COT",
    "report": "IT",
}


def next_number(session: Session, doc_type: str) -> str:
    """Return the next document number (e.g. 'COT-0024') and increment the counter."""
    key = _COUNTER_KEYS[doc_type]
    prefix = _PREFIXES[doc_type]

    repo = SettingRepository(session)
    current = int(repo.get_or_none(key) or "0")
    nxt = current + 1
    repo.set(key, str(nxt))
    return f"{prefix}-{nxt:04d}"


def reset_counter(session: Session, doc_type: str, value: int = 0) -> None:
    """Reset the counter for a document type (user-configurable in Settings)."""
    SettingRepository(session).set(_COUNTER_KEYS[doc_type], str(value))
