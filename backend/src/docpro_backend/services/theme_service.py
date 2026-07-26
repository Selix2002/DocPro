"""Per-profile document theme.

Colors, font family and header image used by quote/report templates.
Values live in the `settings` table; defaults are applied on empty/missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy.orm import Session

from docpro_backend.repositories.config.settings import SettingRepository


DEFAULT_THEME = {
    "primary": "#111111",
    "accent":  "#EBEBEB",
    "text":    "#1A1A1A",
    "font_family": "Arial, Helvetica, 'DejaVu Sans', sans-serif",
    "font_face_css": "",
}

FONT_STACKS = {
    "Arial":           "Arial, Helvetica, 'DejaVu Sans', sans-serif",
    "Helvetica":       "Helvetica, Arial, 'DejaVu Sans', sans-serif",
    "Verdana":         "Verdana, Geneva, 'DejaVu Sans', sans-serif",
    "Georgia":         "Georgia, 'Times New Roman', 'DejaVu Serif', serif",
    "Times New Roman": "'Times New Roman', Times, Georgia, 'DejaVu Serif', serif",
}


def resolve_font_stack(name: str) -> str:
    """Given a font family name, return its full CSS stack (with fallbacks)."""
    return FONT_STACKS.get(name, name or DEFAULT_THEME["font_family"])


_WINDOWS_FONTS_DIR = Path("C:/Windows/Fonts")

# Family → list of (font-style, font-weight, filename) for @font-face rules.
# Helvetica is aliased to Arial (no Helvetica on stock Windows).
_WINDOWS_FONT_FILES: dict[str, list[tuple[str, str, str]]] = {
    "Arial":           [("normal", "normal", "arial.ttf"),   ("normal", "bold", "arialbd.ttf")],
    "Helvetica":       [("normal", "normal", "arial.ttf"),   ("normal", "bold", "arialbd.ttf")],
    "Verdana":         [("normal", "normal", "verdana.ttf"), ("normal", "bold", "verdanab.ttf")],
    "Georgia":         [("normal", "normal", "georgia.ttf"), ("normal", "bold", "georgiab.ttf")],
    "Times New Roman": [("normal", "normal", "times.ttf"),   ("normal", "bold", "timesbd.ttf")],
}


def build_font_face_css(family_stack: str) -> str:
    """
    Build @font-face rules for the first family in `family_stack`, pointing to
    Windows system font files. Ensures WeasyPrint picks the correct font on
    Windows (where fontconfig without GTK often only exposes DejaVu fallbacks).
    Returns '' on non-Windows or unknown family.
    """
    if sys.platform != "win32" or not family_stack:
        return ""
    bare = family_stack.split(",")[0].strip().strip("'\"")
    faces = _WINDOWS_FONT_FILES.get(bare)
    if not faces:
        return ""
    rules: list[str] = []
    for style, weight, filename in faces:
        path = _WINDOWS_FONTS_DIR / filename
        if not path.exists():
            continue
        uri = path.resolve().as_uri()
        rules.append(
            f"@font-face {{ font-family: '{bare}'; "
            f"font-style: {style}; font-weight: {weight}; "
            f"src: url('{uri}'); }}"
        )
    return "\n".join(rules)


def get_theme(session: Session) -> dict:
    """Read theme settings; missing keys fall back to DEFAULT_THEME."""
    repo = SettingRepository(session)
    return {
        "primary":     repo.get_or_none("theme.primary")     or DEFAULT_THEME["primary"],
        "accent":      repo.get_or_none("theme.accent")      or DEFAULT_THEME["accent"],
        "text":        repo.get_or_none("theme.text")        or DEFAULT_THEME["text"],
        "font_family": resolve_font_stack(
            repo.get_or_none("theme.font_family") or ""
        ),
    }


def get_header_imagen(session: Session) -> str | None:
    """Return absolute path (as string) to the profile's header image, or None."""
    from docpro_backend.db.profile_context import ProfileContext
    import base64

    repo = SettingRepository(session)
    stored = repo.get_or_none("header.imagen") or ""
    if not stored:
        return None
    p = Path(stored)
    if not p.is_absolute():
        ctx = ProfileContext.get()
        if not ctx.is_initialized():
            return None
        p = ctx.assets_dir() / stored
    if not p.exists():
        return None
    suffix = p.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else suffix or "png"
    data = p.read_bytes()
    return f"data:image/{mime};base64,{base64.b64encode(data).decode()}"
