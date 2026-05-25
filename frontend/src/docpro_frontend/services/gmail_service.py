from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from docpro_frontend.services.encryption_service import EncryptionService
from docpro_frontend.services.network import is_online

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "openid",
    "email",
]


def _get_credentials_path() -> Path:
    # 1. %APPDATA%\DocPro\credentials.json  (post-install drop-in, all modes)
    appdata_path = Path(os.environ.get("APPDATA", Path.home())) / "DocPro" / "credentials.json"
    if appdata_path.exists():
        return appdata_path
    # 2. ~/.docpro/credentials.json
    user_path = Path.home() / ".docpro" / "credentials.json"
    if user_path.exists():
        return user_path
    if getattr(sys, "frozen", False):
        # 3. Bundled copy inside the executable
        return Path(sys._MEIPASS) / "credentials.json"  # type: ignore[attr-defined]
    return Path(__file__).parent.parent / "resources" / "credentials.json"


def run_oauth_flow() -> dict:
    """Blocking — must run in a Worker thread. Returns token dict including 'email'."""
    import base64
    import os
    from google_auth_oauthlib.flow import InstalledAppFlow

    # oauthlib raises ScopeChanged if Google returns scopes in a different order;
    # relaxing this is the standard fix for desktop OAuth flows.
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

    creds_path = _get_credentials_path()
    if not creds_path.exists():
        appdata = Path(os.environ.get("APPDATA", Path.home())) / "DocPro"
        raise FileNotFoundError(
            f"No se encontró credentials.json. "
            f"Colócalo en: {appdata}\\credentials.json"
        )

    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), _SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)

    # Extract email from the id_token JWT (no extra API call needed)
    email = ""
    if creds.id_token:
        try:
            payload = creds.id_token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            claims = json.loads(base64.b64decode(payload))
            email = claims.get("email", "")
        except Exception:
            pass

    token: dict = json.loads(creds.to_json())
    token["email"] = email
    return token


class GmailService:
    def __init__(self) -> None:
        self._enc = EncryptionService()

    def is_connected(self) -> bool:
        return self._enc.load_gmail_token() is not None

    def is_online(self) -> bool:
        return is_online()

    def get_credentials(self):
        """Load token and silently refresh if expired. Returns None on any failure."""
        from google.auth.exceptions import RefreshError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials

        token = self._enc.load_gmail_token()
        if not token:
            return None

        try:
            creds = Credentials.from_authorized_user_info(token)
        except Exception:
            self._enc.clear_gmail_token()
            return None

        if creds.valid:
            return creds

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                updated: dict = json.loads(creds.to_json())
                updated["email"] = token.get("email", "")
                self._enc.save_gmail_token(updated)
                return creds
            except RefreshError:
                self._enc.clear_gmail_token()
                return None

        return None

    def send(
        self,
        creds,
        recipient: str,
        subject: str,
        body: str,
        pdf_path: Path,
        extra_attachments: list[Path] | None = None,
    ) -> None:
        """Build MIME message and send via Gmail API. Raises on failure."""
        import base64
        import mimetypes
        from email import encoders
        from email.mime.base import MIMEBase
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        from googleapiclient.discovery import build

        msg = MIMEMultipart()
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        for path in [pdf_path] + (extra_attachments or []):
            mime_type, _ = mimetypes.guess_type(str(path))
            main, sub = (mime_type or "application/octet-stream").split("/", 1)
            with path.open("rb") as f:
                part = MIMEBase(main, sub)
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{path.name}"',
            )
            msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service = build("gmail", "v1", credentials=creds)
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

    def build_mailto(self, recipient: str, subject: str) -> str:
        from urllib.parse import quote
        return f"mailto:{recipient}?subject={quote(subject)}"
