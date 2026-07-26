"""Profile management service: create, switch and rename profiles.

Wraps ProfileContext + ProfileRegistry and takes care of engine disposal
and migration when the active profile changes.
"""
from __future__ import annotations

import logging

from docpro_backend.db.engine import dispose_engine
from docpro_backend.db.profile_context import ProfileContext
from docpro_backend.db.profile_registry import ProfileRegistryError

from docpro_frontend.services.profile_bootstrap import run_migrations


log = logging.getLogger(__name__)


class ProfileServiceError(Exception):
    """Raised when a profile operation cannot be completed."""


def list_profiles() -> list[dict]:
    return ProfileContext.get().registry().list_profiles()


def active_slug() -> str:
    return ProfileContext.get().active_slug()


def active_name() -> str:
    return ProfileContext.get().active_name()


def create_and_activate(name: str) -> dict:
    """Create a new profile, switch to it, and run migrations on its DB."""
    name = (name or "").strip()
    if not name:
        raise ProfileServiceError("El nombre no puede estar vacío.")

    ctx = ProfileContext.get()
    registry = ctx.registry()

    try:
        entry = registry.create_profile(name, set_active=False)
    except ProfileRegistryError as exc:
        raise ProfileServiceError(str(exc)) from exc

    try:
        switch_to(entry["slug"])
    except Exception:
        log.exception("No se pudo activar el perfil recién creado; se conservó en registro")
        raise
    return entry


def switch_to(slug: str) -> None:
    """Dispose the current engine, activate `slug`, and run migrations."""
    ctx = ProfileContext.get()
    if slug == ctx.active_slug():
        return

    dispose_engine()
    try:
        ctx.set_active(slug)
    except (ValueError, ProfileRegistryError) as exc:
        raise ProfileServiceError(str(exc)) from exc

    try:
        run_migrations()
    except Exception:
        log.exception("Alembic migration failed on switch to %s", slug)
        raise


def rename(slug: str, new_name: str) -> None:
    new_name = (new_name or "").strip()
    if not new_name:
        raise ProfileServiceError("El nombre no puede estar vacío.")
    try:
        ProfileContext.get().rename(slug, new_name)
    except ProfileRegistryError as exc:
        raise ProfileServiceError(str(exc)) from exc
