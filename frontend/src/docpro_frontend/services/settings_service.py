from datetime import datetime
from pathlib import Path

from docpro_backend.db.engine import engine
from docpro_backend.db.session import SessionLocal
from docpro_backend.repositories.config.company_profile import CompanyProfileRepository
from docpro_backend.repositories.config.settings import SettingRepository
from docpro_backend.repositories.documents.section_templates import SectionTemplateRepository

import docpro_frontend.theme as theme
from docpro_frontend.services.backup_service import BackupService
from docpro_frontend.services.encryption_service import EncryptionService
from docpro_frontend.services.groq_service import GroqService
from docpro_frontend.settings.views.settings_widget import SettingsWidget


class SettingsService:
    def __init__(self, widget: SettingsWidget, db_path: Path) -> None:
        self._widget = widget
        self._forms = widget.content
        self._db_path = db_path
        self._enc = EncryptionService()
        self._groq_svc = GroqService()
        self._backup_svc = BackupService()
        self._clean_snapshot: dict = {}
        self._wire_signals()

    # ── Public ────────────────────────────────────────────────────────

    def load_all(self) -> None:
        session = SessionLocal()
        try:
            self._load_perfil(session)
            self._load_numeracion(session)
            self._load_apariencia(session)
            self._load_groq(session)
            self._load_plantillas(session)
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
        if profile:
            self._forms.company_form.set_data(
                name=profile.name or "",
                city=profile.city or "",
                phone=profile.phone or "",
                email=profile.email or "",
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
        model = repo.get_or_none("groq_model") or "llama3-70b-8192"
        self._forms.groq_form.set_data(api_key, model)
        if api_key:
            self._widget.content.update_card_status("groq", "Sin validar", "warn")
            self._widget.sidebar.update_tile_status("groq", "Conf.", "warn")
        else:
            self._widget.content.update_card_status("groq", "Sin configurar", "off")
            self._widget.sidebar.update_tile_status("groq", "Sin key", "off")

    def _load_plantillas(self, session) -> None:
        templates = SectionTemplateRepository(session).list_all()
        self._forms.templates_form.set_templates([
            {"id": t.id, "name": t.name, "usage_count": t.usage_count}
            for t in templates
        ])
        count = len(templates)
        self._widget.sidebar.update_tile_status("plantillas", str(count), "off")

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
        return {
            **self._forms.company_form.get_data(),
            **self._forms.numbering_form.get_data(),
            **self._forms.appearance_form.get_data(),
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

        # Plantillas: immediate CRUD
        self._forms.templates_form.add_template_requested.connect(self._on_template_add)
        self._forms.templates_form.delete_template_requested.connect(self._on_template_delete)

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
        pass  # OAuth flow — phase 8

    def _on_gmail_disconnect(self) -> None:
        self._enc.clear_gmail_token()
        session = SessionLocal()
        try:
            SettingRepository(session).set("gmail_email", "")
            session.commit()
        finally:
            session.close()
        self._load_gmail()

    def _on_template_add(self) -> None:
        pass  # CreateTemplateDialog — phase 5

    def _on_template_delete(self, template_id: int) -> None:
        session = SessionLocal()
        try:
            SectionTemplateRepository(session).delete(template_id)
            session.commit()
            self._load_plantillas(session)
        finally:
            session.close()

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
        engine.dispose()
        self.load_all()
