"""Unit tests for ProfileRegistry.

Covers slugification, unique-slug generation, JSON persistence, and the
error paths (duplicate/missing/active/last-profile) that guard against data
loss when the user manages profiles.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from docpro_backend.db.profile_registry import ProfileRegistry, ProfileRegistryError


# ── slugify ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Acme", "acme"),
        ("Acme Corp", "acme-corp"),
        ("María Ñandú", "maria-nandu"),
        ("  Spaces   Everywhere  ", "spaces-everywhere"),
        ("Comp@ny/Name!", "comp-ny-name"),
        ("", "perfil"),
        ("!!!", "perfil"),
    ],
)
def test_slugify(name: str, expected: str) -> None:
    assert ProfileRegistry.slugify(name) == expected


# ── create ──────────────────────────────────────────────────────────────

def test_create_first_profile_becomes_active(registry: ProfileRegistry) -> None:
    entry = registry.create_profile("Principal")

    assert entry["slug"] == "principal"
    assert entry["name"] == "Principal"
    assert registry.get_active_slug() == "principal"
    assert registry.profile_dir("principal").is_dir()


def test_create_second_profile_does_not_change_active(
    registry: ProfileRegistry,
) -> None:
    registry.create_profile("First")
    registry.create_profile("Second")

    assert registry.get_active_slug() == "first"


def test_create_with_set_active_switches(registry: ProfileRegistry) -> None:
    registry.create_profile("First")
    registry.create_profile("Second", set_active=True)

    assert registry.get_active_slug() == "second"


def test_create_duplicate_name_gets_unique_slug(
    registry: ProfileRegistry,
) -> None:
    a = registry.create_profile("Acme")
    b = registry.create_profile("Acme")
    c = registry.create_profile("Acme")

    assert (a["slug"], b["slug"], c["slug"]) == ("acme", "acme-2", "acme-3")


def test_create_empty_name_falls_back(registry: ProfileRegistry) -> None:
    entry = registry.create_profile("   ")
    assert entry["name"] == "Perfil"
    assert entry["slug"] == "perfil"


# ── list / get ──────────────────────────────────────────────────────────

def test_list_profiles_returns_all_in_order(registry: ProfileRegistry) -> None:
    registry.create_profile("Alpha")
    registry.create_profile("Bravo")
    registry.create_profile("Charlie")

    names = [p["name"] for p in registry.list_profiles()]
    assert names == ["Alpha", "Bravo", "Charlie"]


def test_get_by_slug_missing_returns_none(registry: ProfileRegistry) -> None:
    registry.create_profile("Only")
    assert registry.get_by_slug("nope") is None


def test_get_active_slug_before_create_raises(
    registry: ProfileRegistry,
) -> None:
    with pytest.raises(ProfileRegistryError):
        registry.get_active_slug()


# ── rename ──────────────────────────────────────────────────────────────

def test_rename_keeps_slug_changes_name(registry: ProfileRegistry) -> None:
    registry.create_profile("Old Name")
    registry.rename_profile("old-name", "New Name")

    entry = registry.get_by_slug("old-name")
    assert entry is not None
    assert entry["name"] == "New Name"


def test_rename_missing_raises(registry: ProfileRegistry) -> None:
    with pytest.raises(ProfileRegistryError):
        registry.rename_profile("ghost", "Name")


def test_rename_empty_raises(registry: ProfileRegistry) -> None:
    registry.create_profile("A")
    with pytest.raises(ProfileRegistryError):
        registry.rename_profile("a", "   ")


# ── set_active ──────────────────────────────────────────────────────────

def test_set_active_switches(registry: ProfileRegistry) -> None:
    registry.create_profile("First")
    registry.create_profile("Second")

    registry.set_active("second")
    assert registry.get_active_slug() == "second"


def test_set_active_unknown_raises(registry: ProfileRegistry) -> None:
    registry.create_profile("Only")
    with pytest.raises(ProfileRegistryError):
        registry.set_active("ghost")


# ── delete ──────────────────────────────────────────────────────────────

def test_delete_moves_to_trash(
    registry: ProfileRegistry, isolated_root: Path
) -> None:
    registry.create_profile("Keep")
    registry.create_profile("Toss")

    registry.delete_profile("toss")

    assert registry.get_by_slug("toss") is None
    trash_dir = isolated_root / "profiles" / "_trash"
    assert trash_dir.exists()
    assert any(p.name.startswith("toss-") for p in trash_dir.iterdir())


def test_delete_without_trash_removes_dir(
    registry: ProfileRegistry, isolated_root: Path
) -> None:
    registry.create_profile("Keep")
    registry.create_profile("Toss")

    registry.delete_profile("toss", trash=False)

    assert not (isolated_root / "profiles" / "toss").exists()
    assert not (isolated_root / "profiles" / "_trash").exists()


def test_delete_active_raises(registry: ProfileRegistry) -> None:
    registry.create_profile("First")
    registry.create_profile("Second")

    with pytest.raises(ProfileRegistryError, match="perfil activo"):
        registry.delete_profile("first")


def test_delete_last_raises_when_active_points_elsewhere(
    registry: ProfileRegistry, isolated_root: Path
) -> None:
    """The `<= 1` guard is unreachable via normal flow (the sole profile is
    always active), so we force the pathological orphan-active state on disk
    to exercise it — this is what keeps a corrupt registry from wiping the
    user's last remaining profile."""
    registry.create_profile("Only")
    data = json.loads((isolated_root / "profiles.json").read_text(encoding="utf-8"))
    data["active"] = "ghost"
    (isolated_root / "profiles.json").write_text(
        json.dumps(data), encoding="utf-8"
    )

    with pytest.raises(ProfileRegistryError, match="último"):
        registry.delete_profile("only")


# ── persistence ─────────────────────────────────────────────────────────

def test_registry_state_survives_reload(
    registry: ProfileRegistry, isolated_root: Path
) -> None:
    registry.create_profile("Alpha")
    registry.create_profile("Bravo", set_active=True)

    reloaded = ProfileRegistry(isolated_root)

    assert [p["slug"] for p in reloaded.list_profiles()] == ["alpha", "bravo"]
    assert reloaded.get_active_slug() == "bravo"


def test_corrupt_json_raises(
    registry: ProfileRegistry, isolated_root: Path
) -> None:
    registry.create_profile("Alpha")
    (isolated_root / "profiles.json").write_text("{ not json", encoding="utf-8")

    with pytest.raises(ProfileRegistryError, match="corrupto"):
        registry.list_profiles()


def test_atomic_write_leaves_valid_json(
    registry: ProfileRegistry, isolated_root: Path
) -> None:
    registry.create_profile("Alpha")
    data = json.loads((isolated_root / "profiles.json").read_text(encoding="utf-8"))

    assert data["active"] == "alpha"
    assert data["profiles"][0]["slug"] == "alpha"
    assert not (isolated_root / "profiles.json.tmp").exists()
