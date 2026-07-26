"""Runtime context of the active DocPro profile.

Singleton used by engine, session and encryption to resolve paths to the
currently-active profile. Initialized once at app startup by main.py, then
mutated only by profile switches.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

from .profile_registry import ProfileRegistry


def default_root_dir() -> Path:
    """Root directory that holds profiles.json and profiles/<slug>/ folders."""
    if getattr(sys, "frozen", False):
        base = Path(os.environ["APPDATA"]) / "DocPro"
    else:
        base = Path(__file__).resolve().parents[4] / ".docpro"
    base.mkdir(parents=True, exist_ok=True)
    return base


class ProfileContext:
    _instance: "ProfileContext | None" = None

    def __init__(self) -> None:
        self._registry: ProfileRegistry | None = None
        self._active_slug: str | None = None
        self._active_name: str | None = None
        self._listeners: list[Callable[[], None]] = []

    # ── Singleton ────────────────────────────────────────────────────────

    @classmethod
    def get(cls) -> "ProfileContext":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ── Lifecycle ────────────────────────────────────────────────────────

    def initialize(self, registry: ProfileRegistry, slug: str, name: str) -> None:
        self._registry = registry
        self._active_slug = slug
        self._active_name = name
        self.profile_dir().mkdir(parents=True, exist_ok=True)

    def is_initialized(self) -> bool:
        return self._active_slug is not None

    def set_active(self, slug: str) -> None:
        if self._registry is None:
            raise RuntimeError("ProfileContext no inicializado")
        entry = self._registry.get_by_slug(slug)
        if entry is None:
            raise ValueError(f"Perfil no encontrado: {slug}")
        self._registry.set_active(slug)
        self._active_slug = slug
        self._active_name = entry["name"]
        self._notify()

    def rename(self, slug: str, new_name: str) -> None:
        """Rename a profile. Slug (folder) stays the same; only display name changes."""
        if self._registry is None:
            raise RuntimeError("ProfileContext no inicializado")
        self._registry.rename_profile(slug, new_name)
        if slug == self._active_slug:
            entry = self._registry.get_by_slug(slug)
            if entry is not None:
                self._active_name = entry["name"]
        self._notify()

    # ── Listeners ────────────────────────────────────────────────────────

    def add_listener(self, cb: Callable[[], None]) -> None:
        """Register a callback fired on active-profile changes (rename/switch)."""
        self._listeners.append(cb)

    def _notify(self) -> None:
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:  # noqa: BLE001 — listeners must not break the flow
                import logging
                logging.getLogger(__name__).exception("ProfileContext listener failed")

    # ── Accessors ────────────────────────────────────────────────────────

    def registry(self) -> ProfileRegistry:
        if self._registry is None:
            raise RuntimeError("ProfileContext no inicializado")
        return self._registry

    def active_slug(self) -> str:
        if self._active_slug is None:
            raise RuntimeError("ProfileContext no inicializado")
        return self._active_slug

    def active_name(self) -> str:
        if self._active_name is None:
            raise RuntimeError("ProfileContext no inicializado")
        return self._active_name

    def profile_dir(self) -> Path:
        return self.registry().profile_dir(self.active_slug())

    def db_path(self) -> Path:
        return self.profile_dir() / "docpro.db"

    def secrets_dir(self) -> Path:
        return self.profile_dir()

    def assets_dir(self) -> Path:
        d = self.profile_dir() / "assets"
        d.mkdir(parents=True, exist_ok=True)
        return d
