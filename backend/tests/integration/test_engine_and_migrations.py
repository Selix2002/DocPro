"""Integration tests: engine wiring + Alembic migrations end-to-end.

These bring up a real SQLite DB in a tmp profile and verify the pieces that
are hard to unit-test in isolation: the singleton→engine→session chain, the
FK pragma, and that migrating from empty produces the same schema our ORM
expects.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from sqlalchemy import inspect, text

from docpro_backend.db import engine as engine_mod
from docpro_backend.db.engine import (
    dispose_engine,
    get_db_path,
    get_engine,
    legacy_db_path,
    switch_profile,
)
from docpro_backend.db.profile_context import ProfileContext
from docpro_backend.db.session import SessionLocal
from docpro_backend.schema import Base


pytestmark = pytest.mark.integration

ActiveProfile = Callable[..., tuple[str, Path]]


# ── migrations produce the ORM schema ────────────────────────────────────

def test_upgrade_head_creates_every_orm_table(active_profile: ActiveProfile) -> None:
    active_profile()

    tables = set(inspect(get_engine()).get_table_names())
    expected = set(Base.metadata.tables.keys())

    missing = expected - tables
    assert not missing, f"Migrations did not create ORM tables: {sorted(missing)}"


def test_upgrade_head_leaves_alembic_at_head(active_profile: ActiveProfile) -> None:
    _, db_path = active_profile()

    with get_engine().connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()

    assert version, f"alembic_version empty in {db_path}"


# ── engine wiring ────────────────────────────────────────────────────────

def test_engine_uses_active_profile_db_path(active_profile: ActiveProfile) -> None:
    _, db_path = active_profile()

    assert get_db_path() == db_path
    assert str(db_path) in str(get_engine().url)


def test_foreign_keys_pragma_enabled(active_profile: ActiveProfile) -> None:
    active_profile()

    with get_engine().connect() as conn:
        enabled = conn.execute(text("PRAGMA foreign_keys")).scalar()

    assert enabled == 1


def test_lazy_engine_module_attribute(active_profile: ActiveProfile) -> None:
    """`from ...db.engine import engine` must still resolve via __getattr__."""
    active_profile()

    lazy = engine_mod.engine  # noqa: SLF001 — the whole point is the lazy attr
    assert lazy is get_engine()


def test_get_engine_is_idempotent(active_profile: ActiveProfile) -> None:
    active_profile()
    assert get_engine() is get_engine()


# ── profile switching ───────────────────────────────────────────────────

def test_switch_profile_rebuilds_engine_against_new_db(
    active_profile: ActiveProfile,
) -> None:
    _, first_db = active_profile("First")
    first_engine = get_engine()

    _, second_db = active_profile("Second")
    second_engine = get_engine()

    assert first_db != second_db
    assert first_engine is not second_engine
    assert str(second_db) in str(second_engine.url)


def test_dispose_engine_resets_cache(active_profile: ActiveProfile) -> None:
    active_profile()
    get_engine()

    dispose_engine()

    assert engine_mod._engine is None  # noqa: SLF001 — asserting cache state


def test_switch_profile_isolates_data(active_profile: ActiveProfile) -> None:
    """A row written in one profile must NOT appear in another."""
    active_profile("First")
    with SessionLocal() as s:
        s.execute(
            text(
                "INSERT INTO settings (key, value) VALUES ('probe', 'first')"
            )
        )
        s.commit()

    active_profile("Second")
    with SessionLocal() as s:
        row = s.execute(
            text("SELECT value FROM settings WHERE key = 'probe'")
        ).first()

    assert row is None


# ── session wiring ──────────────────────────────────────────────────────

def test_session_local_binds_to_current_engine(active_profile: ActiveProfile) -> None:
    active_profile()
    with SessionLocal() as s:
        assert s.get_bind() is get_engine()


def test_session_local_rebinds_after_profile_switch(
    active_profile: ActiveProfile,
) -> None:
    active_profile("First")
    with SessionLocal() as s:
        first_bind = s.get_bind()

    active_profile("Second")
    with SessionLocal() as s:
        second_bind = s.get_bind()

    assert first_bind is not second_bind


# ── legacy path fallback ────────────────────────────────────────────────

def test_get_db_path_falls_back_to_legacy_when_uninitialized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Before `ProfileContext.initialize()`, the engine must resolve to the
    legacy location so `bootstrap_profiles` can find and migrate it."""
    fake_legacy = tmp_path / "legacy.db"
    monkeypatch.setattr(engine_mod, "legacy_db_path", lambda: fake_legacy)

    assert not ProfileContext.get().is_initialized()
    assert get_db_path() == fake_legacy


def test_legacy_db_path_is_stable() -> None:
    """Contract check: legacy_db_path returns a concrete file path, not None."""
    p = legacy_db_path()
    assert p.name == "docpro.db"
    assert p.parent.exists()
