import json
from pathlib import Path

from cryptography.fernet import Fernet

_DIR = Path.home() / ".docpro"
_KEY_FILE = _DIR / "secret.key"
_GROQ_FILE = _DIR / "groq_key.enc"
_GMAIL_FILE = _DIR / "gmail_token.enc"


class EncryptionService:
    def __init__(self) -> None:
        _DIR.mkdir(parents=True, exist_ok=True)
        if _KEY_FILE.exists():
            self._fernet = Fernet(_KEY_FILE.read_bytes())
        else:
            key = Fernet.generate_key()
            _KEY_FILE.write_bytes(key)
            self._fernet = Fernet(key)

    # ── Groq ──────────────────────────────────────────────────────────

    def load_groq_key(self) -> str | None:
        if not _GROQ_FILE.exists():
            return None
        return self._fernet.decrypt(_GROQ_FILE.read_bytes()).decode()

    def save_groq_key(self, key: str) -> None:
        _GROQ_FILE.write_bytes(self._fernet.encrypt(key.encode()))

    # ── Gmail ─────────────────────────────────────────────────────────

    def load_gmail_token(self) -> dict | None:
        if not _GMAIL_FILE.exists():
            return None
        return json.loads(self._fernet.decrypt(_GMAIL_FILE.read_bytes()).decode())

    def save_gmail_token(self, token: dict) -> None:
        _GMAIL_FILE.write_bytes(self._fernet.encrypt(json.dumps(token).encode()))

    def clear_gmail_token(self) -> None:
        if _GMAIL_FILE.exists():
            _GMAIL_FILE.unlink()
