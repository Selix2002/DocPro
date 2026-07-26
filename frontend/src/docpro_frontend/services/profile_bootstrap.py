"""One-shot migration + startup profile activation.

Runs before any DB access. Detects a legacy install (docpro.db + encrypted
secrets in their pre-profiles locations) and moves them into a new
'default' profile named after the existing company (or 'Principal').

Idempotent: on second launch, registry exists and only activation happens.
"""
from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from docpro_backend.db.engine import legacy_db_path
from docpro_backend.db.profile_context import ProfileContext, default_root_dir
from docpro_backend.db.profile_registry import ProfileRegistry


_LEGACY_SECRETS_DIR = Path.home() / ".docpro"
_LEGACY_SECRET_FILES = ("secret.key", "groq_key.enc", "gmail_token.enc")
_LEGACY_ASSET_FILES = ("firma_imagen.png",)

log = logging.getLogger(__name__)


def bootstrap_profiles() -> None:
    """Ensure a profile is active before any engine/session is used."""
    root = default_root_dir()
    registry = ProfileRegistry(root)

    if not registry.exists():
        _perform_initial_migration(registry)

    slug = registry.get_active_slug()
    entry = registry.get_by_slug(slug)
    if entry is None:
        # Registry is corrupted (active slug not in list) — reseed from any entry.
        profiles = registry.list_profiles()
        if not profiles:
            entry = registry.create_profile("Principal", set_active=True)
        else:
            entry = profiles[0]
            registry.set_active(entry["slug"])
        slug = entry["slug"]

    ProfileContext.get().initialize(registry, slug, entry["name"])
    log.info("Active profile: %s (%s)", entry["name"], slug)


def run_migrations(db_path: Path | None = None) -> None:
    """Apply pending Alembic migrations against `db_path` (defaults to active profile)."""
    from alembic import command as alembic_command
    from alembic.config import Config
    from docpro_backend.db.engine import get_db_path

    target = db_path or get_db_path()

    if getattr(sys, "frozen", False):
        meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        ini_path = meipass / "alembic.ini"
        script_loc = str(meipass / "alembic")
    else:
        repo_root = Path(__file__).resolve().parents[4]
        ini_path = repo_root / "backend" / "alembic.ini"
        script_loc = str(ini_path.parent / "alembic")

    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", script_loc)
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{target}")
    alembic_command.upgrade(cfg, "head")


# ── Initial migration ────────────────────────────────────────────────────


def _perform_initial_migration(registry: ProfileRegistry) -> None:
    legacy_db = legacy_db_path()
    company_name = _read_company_name(legacy_db) if legacy_db.exists() else ""
    profile_name = company_name.strip() or "Principal"

    entry = registry.create_profile(profile_name, set_active=True)
    slug = entry["slug"]
    dest = registry.profile_dir(slug)
    dest.mkdir(parents=True, exist_ok=True)

    if legacy_db.exists():
        _safe_move(legacy_db, dest / "docpro.db")

    for name in _LEGACY_SECRET_FILES:
        src = _LEGACY_SECRETS_DIR / name
        if src.exists():
            _safe_move(src, dest / name)

    assets_dst = dest / "assets"
    assets_dst.mkdir(parents=True, exist_ok=True)
    for name in _LEGACY_ASSET_FILES:
        src = _LEGACY_SECRETS_DIR / name
        if src.exists():
            _safe_move(src, assets_dst / name)

    _rewrite_asset_settings(dest / "docpro.db")

    log.info(
        "Migración inicial completada: perfil '%s' creado en %s", profile_name, dest
    )


def _rewrite_asset_settings(db_path: Path) -> None:
    """Convert absolute asset paths in the migrated DB to bare filenames."""
    if not db_path.exists():
        return
    try:
        eng = create_engine(f"sqlite:///{db_path}")
        try:
            insp = inspect(eng)
            if "settings" not in insp.get_table_names():
                return
            with eng.begin() as conn:
                row = conn.execute(
                    text("SELECT value FROM settings WHERE key = 'firma.imagen'")
                ).first()
                if not row or not row[0]:
                    return
                filename = Path(row[0]).name
                conn.execute(
                    text("UPDATE settings SET value = :v WHERE key = 'firma.imagen'"),
                    {"v": filename},
                )
        finally:
            eng.dispose()
    except Exception:
        log.exception("No se pudo reescribir firma.imagen en la BD migrada")


def _read_company_name(db_path: Path) -> str:
    """Best-effort read of company_profile.name from the legacy DB."""
    try:
        eng = create_engine(f"sqlite:///{db_path}")
        try:
            insp = inspect(eng)
            if "company_profile" not in insp.get_table_names():
                return ""
            with eng.connect() as conn:
                row = conn.execute(
                    text("SELECT name FROM company_profile LIMIT 1")
                ).first()
                return (row[0] or "") if row else ""
        finally:
            eng.dispose()
    except Exception:
        log.exception("No se pudo leer company_profile.name de la BD legacy")
        return ""


def _safe_move(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        log.warning("Destino ya existe, se conserva legacy en %s", src)
        return
    shutil.move(str(src), str(dst))
