"""Tests for theme_service.

Mix of pure-function unit tests (`resolve_font_stack`, `build_font_face_css`)
and integration tests that round-trip through the `settings` table
(`get_theme`, `get_header_imagen`).
"""
from __future__ import annotations

import base64

import pytest
from sqlalchemy.orm import Session

from docpro_backend.db.profile_context import ProfileContext
from docpro_backend.repositories.config.settings import SettingRepository
from docpro_backend.services import theme_service
from docpro_backend.services.theme_service import (
    DEFAULT_THEME,
    FONT_STACKS,
    build_font_face_css,
    get_header_imagen,
    get_theme,
    resolve_font_stack,
)


# ── resolve_font_stack (pure) ─────────────────────────────────────────

@pytest.mark.parametrize("family", list(FONT_STACKS.keys()))
def test_resolve_known_family_returns_full_stack(family: str) -> None:
    assert resolve_font_stack(family) == FONT_STACKS[family]


def test_resolve_unknown_family_returns_input(monkeypatch: pytest.MonkeyPatch) -> None:
    assert resolve_font_stack("Comic Sans MS") == "Comic Sans MS"


def test_resolve_empty_returns_default(monkeypatch: pytest.MonkeyPatch) -> None:
    assert resolve_font_stack("") == DEFAULT_THEME["font_family"]


# ── build_font_face_css ────────────────────────────────────────────────

def test_font_face_css_empty_on_non_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(theme_service.sys, "platform", "linux")

    assert build_font_face_css("Arial, sans-serif") == ""


def test_font_face_css_empty_for_empty_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(theme_service.sys, "platform", "win32")

    assert build_font_face_css("") == ""


def test_font_face_css_empty_for_unknown_family(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(theme_service.sys, "platform", "win32")

    assert build_font_face_css("Comic Sans MS, sans-serif") == ""


def test_font_face_css_uses_first_family_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Given a stack, only the first family drives the @font-face rules."""
    monkeypatch.setattr(theme_service.sys, "platform", "win32")
    fonts_dir = tmp_path / "Fonts"
    fonts_dir.mkdir()
    (fonts_dir / "arial.ttf").write_bytes(b"fake")
    (fonts_dir / "arialbd.ttf").write_bytes(b"fake")
    monkeypatch.setattr(theme_service, "_WINDOWS_FONTS_DIR", fonts_dir)

    css = build_font_face_css("Arial, Helvetica, sans-serif")

    assert "@font-face" in css
    assert "font-family: 'Arial'" in css
    assert "font-weight: normal" in css
    assert "font-weight: bold" in css
    assert "arial.ttf" in css
    assert "arialbd.ttf" in css


def test_font_face_css_skips_missing_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setattr(theme_service.sys, "platform", "win32")
    fonts_dir = tmp_path / "Fonts"
    fonts_dir.mkdir()
    (fonts_dir / "arial.ttf").write_bytes(b"fake")
    monkeypatch.setattr(theme_service, "_WINDOWS_FONTS_DIR", fonts_dir)

    css = build_font_face_css("Arial")

    assert "arial.ttf" in css
    assert "arialbd.ttf" not in css


# ── get_theme (integration) ───────────────────────────────────────────

def test_get_theme_returns_defaults_on_empty_db(session: Session) -> None:
    theme = get_theme(session)

    assert theme["primary"] == DEFAULT_THEME["primary"]
    assert theme["accent"] == DEFAULT_THEME["accent"]
    assert theme["text"] == DEFAULT_THEME["text"]
    assert theme["font_family"] == DEFAULT_THEME["font_family"]


def test_get_theme_reads_stored_colors(session: Session) -> None:
    repo = SettingRepository(session)
    repo.set("theme.primary", "#FF0000")
    repo.set("theme.accent", "#00FF00")
    repo.set("theme.text", "#0000FF")

    theme = get_theme(session)

    assert theme["primary"] == "#FF0000"
    assert theme["accent"] == "#00FF00"
    assert theme["text"] == "#0000FF"


def test_get_theme_resolves_font_family_to_full_stack(session: Session) -> None:
    SettingRepository(session).set("theme.font_family", "Georgia")

    assert get_theme(session)["font_family"] == FONT_STACKS["Georgia"]


def test_get_theme_partial_override_keeps_defaults_for_rest(
    session: Session,
) -> None:
    SettingRepository(session).set("theme.primary", "#ABCDEF")

    theme = get_theme(session)

    assert theme["primary"] == "#ABCDEF"
    assert theme["accent"] == DEFAULT_THEME["accent"]


# ── get_header_imagen (integration) ───────────────────────────────────

def test_header_imagen_none_when_setting_missing(session: Session) -> None:
    assert get_header_imagen(session) is None


def test_header_imagen_none_when_setting_empty(session: Session) -> None:
    SettingRepository(session).set("header.imagen", "")

    assert get_header_imagen(session) is None


def test_header_imagen_relative_path_uses_profile_assets_dir(
    session: Session,
) -> None:
    """A bare filename is resolved against the active profile's assets/ dir
    and returned as a base64 data-URI ready to embed in the PDF template."""
    payload = b"\x89PNG\r\n\x1a\nreal-png-bytes"
    assets_dir = ProfileContext.get().assets_dir()
    (assets_dir / "logo.png").write_bytes(payload)
    SettingRepository(session).set("header.imagen", "logo.png")

    uri = get_header_imagen(session)

    assert uri is not None
    assert uri.startswith("data:image/png;base64,")
    assert base64.b64decode(uri.split(",", 1)[1]) == payload


def test_header_imagen_absolute_path_is_used_directly(
    session: Session, tmp_path
) -> None:
    payload = b"\xff\xd8\xff\xe0jpg-bytes"
    img = tmp_path / "external.jpg"
    img.write_bytes(payload)
    SettingRepository(session).set("header.imagen", str(img))

    uri = get_header_imagen(session)

    assert uri is not None
    assert uri.startswith("data:image/jpeg;base64,")
    assert base64.b64decode(uri.split(",", 1)[1]) == payload


def test_header_imagen_none_when_file_missing(session: Session) -> None:
    SettingRepository(session).set("header.imagen", "ghost.png")

    assert get_header_imagen(session) is None


def test_header_imagen_mime_maps_jpg_to_jpeg(session: Session) -> None:
    assets_dir = ProfileContext.get().assets_dir()
    (assets_dir / "photo.jpg").write_bytes(b"data")
    SettingRepository(session).set("header.imagen", "photo.jpg")

    uri = get_header_imagen(session)

    assert uri is not None
    assert uri.startswith("data:image/jpeg;base64,")
