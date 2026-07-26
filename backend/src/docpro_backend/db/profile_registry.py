"""Profile registry: manages the list of DocPro profiles on disk.

Each profile owns an isolated DB and secrets directory. This module handles
only the metadata (profiles.json). Actual DB switching lives in
`profile_context` + `engine`.
"""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path


class ProfileRegistryError(Exception):
    """Raised on invalid registry operations (duplicate slug, missing, etc.)."""


class ProfileRegistry:
    """Reads/writes profiles.json and provides paths to profile directories."""

    def __init__(self, root_dir: Path) -> None:
        self._root = root_dir
        self._root.mkdir(parents=True, exist_ok=True)
        self._file = root_dir / "profiles.json"

    # ── Query ────────────────────────────────────────────────────────────

    def exists(self) -> bool:
        return self._file.exists()

    def list_profiles(self) -> list[dict]:
        return list(self._load().get("profiles", []))

    def get_active_slug(self) -> str:
        data = self._load()
        active = data.get("active", "")
        if not active:
            raise ProfileRegistryError("No active profile set")
        return active

    def get_by_slug(self, slug: str) -> dict | None:
        for p in self.list_profiles():
            if p["slug"] == slug:
                return p
        return None

    def profile_dir(self, slug: str) -> Path:
        return self._root / "profiles" / slug

    # ── Mutations ────────────────────────────────────────────────────────

    def create_profile(self, name: str, *, set_active: bool = False) -> dict:
        name = name.strip() or "Perfil"
        slug = self._unique_slug(name)
        entry = {
            "slug": slug,
            "name": name,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        data = self._load() if self.exists() else {"active": "", "profiles": []}
        data["profiles"].append(entry)
        if set_active or not data.get("active"):
            data["active"] = slug
        self._save(data)
        self.profile_dir(slug).mkdir(parents=True, exist_ok=True)
        return entry

    def rename_profile(self, slug: str, new_name: str) -> None:
        new_name = new_name.strip()
        if not new_name:
            raise ProfileRegistryError("El nombre no puede estar vacío")
        data = self._load()
        for p in data["profiles"]:
            if p["slug"] == slug:
                p["name"] = new_name
                self._save(data)
                return
        raise ProfileRegistryError(f"Perfil no encontrado: {slug}")

    def delete_profile(self, slug: str, *, trash: bool = True) -> None:
        data = self._load()
        if data.get("active") == slug:
            raise ProfileRegistryError(
                "No se puede eliminar el perfil activo. Cambia a otro perfil primero."
            )
        if len(data["profiles"]) <= 1:
            raise ProfileRegistryError("No se puede eliminar el último perfil.")
        data["profiles"] = [p for p in data["profiles"] if p["slug"] != slug]
        self._save(data)

        src = self.profile_dir(slug)
        if not src.exists():
            return
        if trash:
            trash_dir = self._root / "profiles" / "_trash"
            trash_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.move(str(src), str(trash_dir / f"{slug}-{stamp}"))
        else:
            shutil.rmtree(src, ignore_errors=True)

    def set_active(self, slug: str) -> None:
        data = self._load()
        if not any(p["slug"] == slug for p in data["profiles"]):
            raise ProfileRegistryError(f"Perfil no encontrado: {slug}")
        data["active"] = slug
        self._save(data)

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def slugify(name: str) -> str:
        n = unicodedata.normalize("NFKD", name)
        n = "".join(c for c in n if not unicodedata.combining(c))
        n = n.lower()
        n = re.sub(r"[^a-z0-9]+", "-", n).strip("-")
        return n or "perfil"

    def _unique_slug(self, name: str) -> str:
        base = self.slugify(name)
        existing = {p["slug"] for p in self.list_profiles()} if self.exists() else set()
        if base not in existing:
            return base
        i = 2
        while f"{base}-{i}" in existing:
            i += 1
        return f"{base}-{i}"

    def _load(self) -> dict:
        if not self._file.exists():
            return {"active": "", "profiles": []}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProfileRegistryError(f"profiles.json corrupto: {exc}") from exc

    def _save(self, data: dict) -> None:
        tmp = self._file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._file)
