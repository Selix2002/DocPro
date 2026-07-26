from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThreadPool

from docpro_backend.db.engine import dispose_engine, get_db_path
from docpro_backend.db.session import SessionLocal
from docpro_backend.repositories.config.company_profile import CompanyProfileRepository
from docpro_backend.repositories.config.settings import SettingRepository

import docpro_frontend.theme as theme
from docpro_frontend.services.backup_service import BackupService
from docpro_frontend.services.encryption_service import EncryptionService
from docpro_frontend.services.gmail_service import run_oauth_flow
from docpro_frontend.services.groq_service import GroqService
from docpro_frontend.services.worker import Worker
from docpro_frontend.settings.views.settings_widget import SettingsWidget


class SettingsService:
    def __init__(self, widget: SettingsWidget, db_path: Path | None = None) -> None:
        self._widget = widget
        self._forms = widget.content
        self._enc = EncryptionService()
        self._groq_svc = GroqService()
        self._backup_svc = BackupService()
        self._clean_snapshot: dict = {}
        self._wire_signals()

    @property
    def _db_path(self) -> Path:
        return get_db_path()

    # ── Public ────────────────────────────────────────────────────────

    def load_all(self) -> None:
        session = SessionLocal()
        try:
            self._load_perfil(session)
            self._load_numeracion(session)
            self._load_apariencia(session)
            self._load_template(session)
            self._load_groq(session)
            self._load_backup(session)
        finally:
            session.close()
        self._load_gmail()
        self._clean_snapshot = self._take_snapshot()

    def save_all(self) -> None:
        session = SessionLocal()
        try:
            self._save_perfil(session)
            self._save_numeracion(session)
            self._save_apariencia(session)
            self._save_template(session)
            self._save_groq(session)
            session.commit()
        finally:
            session.close()
        self._clean_snapshot = self._take_snapshot()

    def has_unsaved_changes(self) -> bool:
        return self._take_snapshot() != self._clean_snapshot

    # ── Load helpers ──────────────────────────────────────────────────

    def _load_perfil(self, session) -> None:
        profile = CompanyProfileRepository(session).get()
        repo = SettingRepository(session)
        self._forms.company_form.set_data(
            name=profile.name or "" if profile else "",
            city=profile.city or "" if profile else "",
            phone=profile.phone or "" if profile else "",
            email=profile.email or "" if profile else "",
            firma_nombre=repo.get_or_none("firma.nombre") or "",
            firma_cargo=repo.get_or_none("firma.cargo") or "",
            firma_imagen=repo.get_or_none("firma.imagen") or "",
        )

    def _load_numeracion(self, session) -> None:
        repo = SettingRepository(session)
        self._forms.numbering_form.set_data(
            quote_prefix=repo.get_or_none("quote_prefix") or "COT-",
            quote_number=int(repo.get_or_none("quote_number") or 1),
            report_prefix=repo.get_or_none("report_prefix") or "IT-",
            report_number=int(repo.get_or_none("report_number") or 1),
        )

    def _load_apariencia(self, session) -> None:
        mode = SettingRepository(session).get_or_none("theme") or "system"
        self._forms.appearance_form.set_theme(mode)
        theme.activate(mode)

    def _load_template(self, session) -> None:
        repo = SettingRepository(session)
        self._forms.template_page.form.set_data(
            primary=repo.get_or_none("theme.primary") or "",
            accent=repo.get_or_none("theme.accent") or "",
            text=repo.get_or_none("theme.text") or "",
            font_family=repo.get_or_none("theme.font_family") or "Arial",
            header_imagen=repo.get_or_none("header.imagen") or "",
        )
        self._forms.template_page.refresh_preview()

    def _load_gmail(self) -> None:
        token = self._enc.load_gmail_token()
        if token:
            email = token.get("email", "")
            self._forms.gmail_form.set_connected(True, email, "Conectado")
            self._widget.content.update_card_status("gmail", "Conectado", "ok")
            self._widget.sidebar.update_tile_status("gmail", "Conectado", "ok")
        else:
            self._forms.gmail_form.set_connected(False, "", "")
            self._widget.content.update_card_status("gmail", "Desconectado", "off")
            self._widget.sidebar.update_tile_status("gmail", "Desconectado", "off")

    def _load_groq(self, session) -> None:
        repo = SettingRepository(session)
        api_key = self._enc.load_groq_key() or ""
        model = repo.get_or_none("groq_model") or "llama-3.3-70b-versatile"
        self._forms.groq_form.set_data(api_key, model)
        if api_key:
            self._widget.content.update_card_status("groq", "Sin validar", "warn")
            self._widget.sidebar.update_tile_status("groq", "Conf.", "warn")
        else:
            self._widget.content.update_card_status("groq", "Sin configurar", "off")
            self._widget.sidebar.update_tile_status("groq", "Sin key", "off")

    def _load_backup(self, session) -> None:
        last = SettingRepository(session).get_or_none("last_backup")
        if last:
            try:
                dt = datetime.fromisoformat(last)
                text = dt.strftime("%d/%m/%Y a las %H:%M")
            except ValueError:
                text = last
        else:
            text = "nunca"
        self._forms.backup_form.set_last_backup(text)

    def _take_snapshot(self) -> dict:
        template_data = {
            f"template.{k}": v
            for k, v in self._forms.template_page.form.get_data().items()
        }
        return {
            **self._forms.company_form.get_data(),
            **self._forms.numbering_form.get_data(),
            **self._forms.appearance_form.get_data(),
            **template_data,
            **self._forms.groq_form.get_data(),
        }

    # ── Save helpers ──────────────────────────────────────────────────

    def _save_perfil(self, session) -> None:
        data = self._forms.company_form.get_data()
        CompanyProfileRepository(session).save(
            name=data["name"],
            city=data["city"],
            phone=data["phone"],
            email=data["email"],
        )
        repo = SettingRepository(session)
        repo.set("firma.nombre",  data.get("firma_nombre")  or "")
        repo.set("firma.cargo",   data.get("firma_cargo")   or "")
        repo.set("firma.imagen",  data.get("firma_imagen")  or "")

    def _save_numeracion(self, session) -> None:
        data = self._forms.numbering_form.get_data()
        repo = SettingRepository(session)
        repo.set("quote_prefix", data["quote_prefix"])
        repo.set("quote_number", str(data["quote_number"]))
        repo.set("report_prefix", data["report_prefix"])
        repo.set("report_number", str(data["report_number"]))

    def _save_apariencia(self, session) -> None:
        mode = self._forms.appearance_form.get_data()["theme"]
        SettingRepository(session).set("theme", mode)

    def _save_template(self, session) -> None:
        data = self._forms.template_page.form.get_data()
        repo = SettingRepository(session)
        repo.set("theme.primary",     data.get("primary")       or "")
        repo.set("theme.accent",      data.get("accent")        or "")
        repo.set("theme.text",        data.get("text")          or "")
        repo.set("theme.font_family", data.get("font_family")   or "")
        repo.set("header.imagen",     data.get("header_imagen") or "")

    def _save_groq(self, session) -> None:
        data = self._forms.groq_form.get_data()
        if data["api_key"]:
            self._enc.save_groq_key(data["api_key"])
        SettingRepository(session).set("groq_model", data["model"])

    # ── Signal wiring ─────────────────────────────────────────────────

    def _wire_signals(self) -> None:
        # Theme: apply in real time on every chip click (before Guardar)
        self._forms.appearance_form.theme_changed.connect(theme.activate)

        # Groq: validate on demand
        self._forms.groq_form.validate_requested.connect(self._on_groq_validate)

        # Gmail: connect / disconnect (OAuth in phase 8)
        self._forms.gmail_form.connect_requested.connect(self._on_gmail_connect)
        self._forms.gmail_form.disconnect_requested.connect(self._on_gmail_disconnect)

        # Backup: immediate actions
        self._forms.backup_form.export_requested.connect(self._on_backup_export)
        self._forms.backup_form.restore_requested.connect(self._on_backup_restore)

        # Guardar
        self._widget.save_requested.connect(self.save_all)

    # ── Handlers ──────────────────────────────────────────────────────

    def _on_groq_validate(self, api_key: str, model: str) -> None:
        ok, message = self._groq_svc.validate(api_key, model)
        if ok:
            self._widget.content.update_card_status("groq", "Validada", "ok")
            self._widget.sidebar.update_tile_status("groq", "OK", "ok")
        else:
            self._widget.content.update_card_status("groq", message[:20], "warn")
            self._widget.sidebar.update_tile_status("groq", "Error", "warn")

    def _on_gmail_connect(self) -> None:
        self._forms.gmail_form.set_loading(True)
        self._widget.sidebar.update_tile_status("gmail", "Conectando…", "warn")
        worker = Worker(run_oauth_flow)
        worker.signals.result.connect(self._on_gmail_auth_success)
        worker.signals.error.connect(self._on_gmail_auth_error)
        QThreadPool.globalInstance().start(worker)

    def _on_gmail_auth_success(self, token_dict: dict) -> None:
        self._enc.save_gmail_token(token_dict)
        session = SessionLocal()
        try:
            SettingRepository(session).set("gmail_email", token_dict.get("email", ""))
            session.commit()
        finally:
            session.close()
        self._load_gmail()

    def _on_gmail_auth_error(self, message: str) -> None:
        self._forms.gmail_form.set_error(message[:80])
        self._widget.sidebar.update_tile_status("gmail", "Error", "warn")

    def _on_gmail_disconnect(self) -> None:
        self._enc.clear_gmail_token()
        session = SessionLocal()
        try:
            SettingRepository(session).set("gmail_email", "")
            session.commit()
        finally:
            session.close()
        self._load_gmail()

    def _on_backup_export(self) -> None:
        timestamp = self._backup_svc.export(self._db_path, parent=self._widget)
        if not timestamp:
            return
        session = SessionLocal()
        try:
            SettingRepository(session).set("last_backup", timestamp)
            session.commit()
        finally:
            session.close()
        dt = datetime.fromisoformat(timestamp)
        self._forms.backup_form.set_last_backup(dt.strftime("%d/%m/%Y a las %H:%M"))

    def _on_backup_restore(self) -> None:
        restored = self._backup_svc.restore(self._db_path, parent=self._widget)
        if not restored:
            return
        # Dispose connection pool so next SessionLocal() opens a fresh connection
        dispose_engine()
        self.load_all()
