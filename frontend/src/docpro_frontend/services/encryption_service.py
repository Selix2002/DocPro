import json
from pathlib import Path

from cryptography.fernet import Fernet

from docpro_backend.db.profile_context import ProfileContext


_LEGACY_DIR = Path.home() / ".docpro"


def _resolve_dir(explicit: Path | None) -> Path:
    """Prefer explicit path → active profile → legacy ~/.docpro/ (migration only)."""
    if explicit is not None:
        return explicit
    ctx = ProfileContext.get()
    if ctx.is_initialized():
        return ctx.secrets_dir()
    return _LEGACY_DIR


class EncryptionService:
    def __init__(self, secrets_dir: Path | None = None) -> None:
        self._dir = _resolve_dir(secrets_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        key_file = self._dir / "secret.key"
        if key_file.exists():
            self._fernet = Fernet(key_file.read_bytes())
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            self._fernet = Fernet(key)

    # ── Groq ──────────────────────────────────────────────────────────

    def load_groq_key(self) -> str | None:
        f = self._dir / "groq_key.enc"
        if not f.exists():
            return None
        return self._fernet.decrypt(f.read_bytes()).decode()

    def save_groq_key(self, key: str) -> None:
        (self._dir / "groq_key.enc").write_bytes(self._fernet.encrypt(key.encode()))

    # ── Gmail ─────────────────────────────────────────────────────────

    def load_gmail_token(self) -> dict | None:
        f = self._dir / "gmail_token.enc"
        if not f.exists():
            return None
        return json.loads(self._fernet.decrypt(f.read_bytes()).decode())

    def save_gmail_token(self, token: dict) -> None:
        (self._dir / "gmail_token.enc").write_bytes(
            self._fernet.encrypt(json.dumps(token).encode())
        )

    def clear_gmail_token(self) -> None:
        f = self._dir / "gmail_token.enc"
        if f.exists():
            f.unlink()
