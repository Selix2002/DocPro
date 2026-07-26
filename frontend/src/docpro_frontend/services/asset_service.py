"""Per-profile asset helpers.

Assets (signature image, later header/logo, fonts) live in
`<profile_dir>/assets/`. The DB stores only the filename; absolute paths
are resolved at read-time so profiles stay portable.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from docpro_backend.db.profile_context import ProfileContext


def assets_dir() -> Path:
    return ProfileContext.get().assets_dir()


def resolve(filename: str) -> Path | None:
    """Return absolute path if the asset exists under the active profile, else None."""
    if not filename:
        return None
    p = assets_dir() / filename
    return p if p.exists() else None


def store(src: Path, dest_filename: str) -> str:
    """Copy src into the active profile's assets/ as dest_filename. Returns dest_filename."""
    dst = assets_dir() / dest_filename
    shutil.copy2(src, dst)
    return dest_filename


def remove(filename: str) -> None:
    if not filename:
        return
    p = assets_dir() / filename
    if p.exists():
        p.unlink()
