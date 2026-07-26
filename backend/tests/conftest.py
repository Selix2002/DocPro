"""Shared fixtures for backend tests.

Every test runs against an isolated on-disk root (`tmp_path`) with a fresh
`ProfileContext` and a disposed engine, so no state leaks between tests.
"""
from __future__ import annotations

from itertools import count
from pathlib import Path
from typing import Callable, Iterator

import pytest
from sqlalchemy.orm import Session

from docpro_backend.db import engine as engine_mod
from docpro_backend.db import profile_context as profile_context_mod
from docpro_backend.db import session as session_mod
from docpro_backend.db.profile_context import ProfileContext
from docpro_backend.db.profile_registry import ProfileRegistry
from docpro_backend.db.session import SessionLocal
from docpro_backend.schema import Client, Document


BACKEND_ROOT = Path(__file__).resolve().parent.parent
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"
ALEMBIC_SCRIPTS = BACKEND_ROOT / "alembic"


def _reset_global_state() -> None:
    """Drop the singleton + cached engine/session so the next test starts clean."""
    engine_mod.dispose_engine()
    session_mod._maker = None
    session_mod._maker_engine = None
    ProfileContext._instance = None


@pytest.fixture(autouse=True)
def isolated_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect `default_root_dir()` to `tmp_path` and reset global state.

    Autouse: every test gets its own root — no test can accidentally read or
    write the developer's real `~/.docpro/` directory.
    """
    _reset_global_state()
    monkeypatch.setattr(profile_context_mod, "default_root_dir", lambda: tmp_path)
    yield tmp_path
    _reset_global_state()


@pytest.fixture
def registry(isolated_root: Path) -> ProfileRegistry:
    """A fresh ProfileRegistry rooted at the isolated tmp dir."""
    return ProfileRegistry(isolated_root)


def _run_alembic_upgrade(db_path: Path) -> None:
    from alembic import command as alembic_command
    from alembic.config import Config

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(ALEMBIC_SCRIPTS))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    alembic_command.upgrade(cfg, "head")


@pytest.fixture
def active_profile(
    registry: ProfileRegistry,
) -> Callable[..., tuple[str, Path]]:
    """Factory: create a profile, activate it, and run Alembic to head.

    Returns `(slug, db_path)`. Call multiple times in a test to build several
    profiles; only the last one activated is current (via `ProfileContext`).
    """
    def _make(name: str = "Test") -> tuple[str, Path]:
        entry = registry.create_profile(name, set_active=True)
        slug = entry["slug"]
        ProfileContext.get().initialize(registry, slug, entry["name"])
        db_path = ProfileContext.get().db_path()
        # Rebuild the engine BEFORE migrating: alembic/env.py imports the app
        # engine, so a stale cached engine would migrate the wrong DB.
        engine_mod.switch_profile()
        session_mod._maker = None
        session_mod._maker_engine = None
        _run_alembic_upgrade(db_path)
        return slug, db_path

    return _make


@pytest.fixture
def session(active_profile: Callable[..., tuple[str, Path]]) -> Iterator[Session]:
    """A live Session bound to a freshly-migrated profile DB.

    Commits are the caller's responsibility. The session is closed on teardown.
    """
    active_profile()
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()


# ── Row factories ──────────────────────────────────────────────────────

_rut_seq = count(1)
_number_seq = count(1)


@pytest.fixture(autouse=True)
def _reset_factory_sequences() -> None:
    """Factories generate unique RUTs/numbers per session — reset each test
    so failures are reproducible from a known starting point."""
    global _rut_seq, _number_seq
    _rut_seq = count(1)
    _number_seq = count(1)


@pytest.fixture
def make_client(session: Session) -> Callable[..., Client]:
    """Insert a Client with a unique RUT. Overrides via kwargs."""
    def _factory(**overrides) -> Client:
        n = next(_rut_seq)
        defaults = dict(
            rut=f"{10_000_000 + n}-{n % 10}",
            name=f"Cliente {n}",
        )
        defaults.update(overrides)
        client = Client(**defaults)
        session.add(client)
        session.flush()
        return client

    return _factory


@pytest.fixture
def make_document(
    session: Session, make_client: Callable[..., Client]
) -> Callable[..., Document]:
    """Insert a Document. `number` auto-generated if not provided."""
    def _factory(**overrides) -> Document:
        client = overrides.pop("client", None) or make_client()
        n = next(_number_seq)
        defaults = dict(
            type="quote",
            number=f"AUTO-{n:04d}",
            status="Borrador",
            client_id=client.id,
        )
        defaults.update(overrides)
        doc = Document(**defaults)
        session.add(doc)
        session.flush()
        return doc

    return _factory
