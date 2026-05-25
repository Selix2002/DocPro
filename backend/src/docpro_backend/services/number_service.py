import re

from sqlalchemy.orm import Session

from docpro_backend.repositories.config.settings import SettingRepository

_COUNTER_KEYS = {
    "quote":  "quote_number",
    "report": "report_number",
}
_PREFIX_KEYS = {
    "quote":  "quote_prefix",
    "report": "report_prefix",
}
_DEFAULT_PREFIXES = {
    "quote":  "COT-",
    "report": "IT-",
}


def next_number(session: Session, doc_type: str) -> str:
    """Return the next document number (e.g. 'COT-0024') and increment the counter.
    Reads both prefix and counter from the settings table so the Settings UI
    and the numbering service stay in sync on the same keys.
    """
    repo    = SettingRepository(session)
    prefix  = repo.get_or_none(_PREFIX_KEYS[doc_type]) or _DEFAULT_PREFIXES[doc_type]
    key     = _COUNTER_KEYS[doc_type]
    current = int(repo.get_or_none(key) or "0")
    nxt     = current + 1
    repo.set(key, str(nxt))
    return f"{prefix}{nxt:04d}"


def preview_next_number(session: Session, doc_type: str) -> str:
    """Return what the next document number would be, based on the last actual document in
    the DB.  Falls back to the settings counter only when no documents exist yet."""
    from docpro_backend.schema.documents.documents import Document

    repo   = SettingRepository(session)
    prefix = repo.get_or_none(_PREFIX_KEYS[doc_type]) or _DEFAULT_PREFIXES[doc_type]

    numbers = (
        session.query(Document.number)
        .filter(Document.type == doc_type)
        .all()
    )
    max_num = 0
    for (num,) in numbers:
        m = re.search(r"(\d+)$", num)
        if m:
            max_num = max(max_num, int(m.group(1)))
    if max_num:
        return f"{prefix}{max_num + 1:04d}"

    current = int(repo.get_or_none(_COUNTER_KEYS[doc_type]) or "0")
    return f"{prefix}{current + 1:04d}"


def sync_counter(session: Session, doc_type: str, used_number: str) -> None:
    """Advance the counter to match `used_number` if `used_number` is numerically higher.
    Called when the user provides their own number instead of an auto-generated one,
    so the counter stays in sync with what was actually written to the DB."""
    m = re.search(r"(\d+)$", used_number)
    if not m:
        return
    n = int(m.group(1))
    repo = SettingRepository(session)
    key  = _COUNTER_KEYS[doc_type]
    current = int(repo.get_or_none(key) or "0")
    if n > current:
        repo.set(key, str(n))


def reset_counter(session: Session, doc_type: str, value: int = 0) -> None:
    """Reset the counter for a document type (user-configurable in Settings)."""
    SettingRepository(session).set(_COUNTER_KEYS[doc_type], str(value))
