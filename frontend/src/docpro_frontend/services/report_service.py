from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from docpro_frontend.mail.views.email_composer_dialog import EmailComposerDialog
from docpro_frontend.report.views.report_widget import ReportWidget
from docpro_frontend.services.gmail_service import GmailService
from docpro_frontend.services.worker import Worker


class ReportService(QObject):
    """
    Service layer for the report editor.
    Owns the 800ms autosave timer and mediates between ReportWidget and the
    backend report service.

    Same lazy-creation pattern as QuoteService: the Document/Report rows are
    only written to DB once a valid client_id is known (after RUT lookup or
    inline client creation).
    """

    navigation_back = Signal()

    def __init__(self, widget: ReportWidget, gmail_svc: GmailService) -> None:
        super().__init__()
        self._widget    = widget
        self._header    = widget.header
        self._form      = widget.form
        self._preview   = widget.preview
        self._gmail_svc = gmail_svc

        self._doc_id:            int | None = None
        self._current_client_id: int | None = None
        self._status:            str        = "Borrador"
        self._pending_back:      bool       = False
        self._pending_finalize:  bool       = False
        self._loading:           bool       = False
        self._doc_number:        str        = ""
        self._preview_locked:    bool       = False
        self._preview_slot:      int        = 0

        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(800)
        self._autosave_timer.timeout.connect(self._do_autosave)

        self._wire_signals()

    # ── Public ────────────────────────────────────────────────────────────────

    def open_new(self) -> None:
        self._autosave_timer.stop()
        self._doc_id            = None
        self._current_client_id = None
        self._status            = "Borrador"
        self._pending_back      = False
        self._pending_finalize  = False
        self._doc_number        = ""
        self._preview_locked    = False
        self._preview_slot      = 0
        self._form.reset()
        self._form.set_readonly(False)
        self._header.set_document_number("—")
        self._header.set_status("Borrador")
        self._header.set_autosave_state("idle")
        self._header.set_number_editable(False)
        self._header.set_duplicate_enabled(False)
        self._preview.clear()

        worker = Worker(_preview_next_number)
        worker.signals.result.connect(self._on_preview_loaded)
        worker.signals.error.connect(lambda _: None)
        QThreadPool.globalInstance().start(worker)

    def open_existing(self, doc_id: int) -> None:
        self._autosave_timer.stop()
        self._doc_id            = doc_id
        self._current_client_id = None
        self._status            = "Borrador"
        self._pending_back      = False
        self._pending_finalize  = False
        self._loading           = True
        self._doc_number        = ""
        self._preview_locked    = False
        self._preview_slot      = 0
        self._header.set_document_number("…")
        self._header.set_autosave_state("idle")
        self._form.reset()
        self._preview.clear()

        worker = Worker(lambda: _load_report(doc_id))
        worker.signals.result.connect(self._on_loaded)
        worker.signals.error.connect(self._on_load_error)
        QThreadPool.globalInstance().start(worker)

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _wire_signals(self) -> None:
        self._form.field_changed.connect(self._on_field_changed)
        self._form.rut_entered.connect(self._on_rut_entered)
        self._header.back_requested.connect(self._on_back)
        self._header.finalize_requested.connect(self._on_finalize)
        self._header.delete_requested.connect(self._on_delete)
        self._header.generate_pdf_requested.connect(self._on_generate_pdf)
        self._header.send_requested.connect(self._on_send_gmail)
        self._header.number_change_requested.connect(self._on_number_change_requested)
        self._header.duplicate_requested.connect(self._on_duplicate)
        self._ctrl_s = QShortcut(QKeySequence.StandardKey.Save, self._widget)
        self._ctrl_s.activated.connect(self._on_ctrl_s)

    # ── Autosave ──────────────────────────────────────────────────────────────

    def _can_save(self) -> bool:
        data = self._form.get_client_data()
        return bool(data.get("rut") and data.get("name"))

    def _on_field_changed(self) -> None:
        if self._loading:
            return
        if not self._can_save():
            return
        if self._status != "Borrador":
            return
        self._header.set_autosave_state("saving")
        self._autosave_timer.start(800)

    def _do_autosave(self) -> None:
        if not self._can_save():
            return
        data          = self._form.get_data()
        sections_data = data["sections"]
        trabajo_data  = data.get("trabajo")
        client_data   = self._form.get_client_data()
        doc_id        = self._doc_id
        client_id     = self._current_client_id

        if client_id is None:
            worker = Worker(lambda: _create_client_and_report(client_data, sections_data, trabajo_data))
            worker.signals.result.connect(self._on_client_and_report_created)
        else:
            worker = Worker(
                lambda: _save_with_client(client_id, client_data, sections_data, doc_id, trabajo_data)
            )
            worker.signals.result.connect(
                self._on_created if doc_id is None else self._on_autosaved
            )

        worker.signals.error.connect(self._on_autosave_error)
        QThreadPool.globalInstance().start(worker)

    def _on_preview_loaded(self, number: str) -> None:
        if self._doc_id is None:
            self._form.set_number(number)
            self._header.set_document_number(number)

    def _on_created(self, rm) -> None:
        self._doc_id     = rm.document_id
        self._doc_number = rm.number
        self._form.set_number(rm.number)
        self._form.lock_number()
        self._header.set_document_number(rm.number)
        self._header.set_autosave_state("saved")
        self._header.set_number_editable(True)
        self._header.set_duplicate_enabled(True)
        if self._pending_back:
            self._do_navigate_back()
        elif self._pending_finalize:
            self._pending_finalize = False
            self._execute_finalize()
        elif not self._preview_locked:
            self._trigger_preview_render(self._doc_id)

    def _on_client_and_report_created(self, result: dict) -> None:
        self._current_client_id = result["client_id"]
        self._doc_id            = result["doc_id"]
        self._doc_number        = result["number"]
        self._form.set_number(result["number"])
        self._form.lock_number()
        self._header.set_document_number(result["number"])
        self._header.set_autosave_state("saved")
        self._header.set_number_editable(True)
        self._header.set_duplicate_enabled(True)
        if self._pending_back:
            self._do_navigate_back()
        elif self._pending_finalize:
            self._pending_finalize = False
            self._execute_finalize()
        elif not self._preview_locked:
            self._trigger_preview_render(self._doc_id)

    def _on_autosaved(self, _) -> None:
        self._header.set_autosave_state("saved")
        if self._pending_back:
            self._do_navigate_back()
            return
        if not self._preview_locked:
            self._trigger_preview_render(self._doc_id)

    def _on_autosave_error(self, msg: str) -> None:
        self._header.set_autosave_state("error")
        print(f"[report] autosave error: {msg}")

    # ── Load existing ─────────────────────────────────────────────────────────

    def _on_loaded(self, rm) -> None:
        self._current_client_id = rm.client_id
        self._status            = rm.status
        self._doc_number        = rm.number
        self._form.set_data(rm)
        self._form.set_number(rm.number)
        self._header.set_document_number(rm.number)
        self._header.set_status(rm.status)
        self._header.set_autosave_state("saved")
        self._header.set_number_editable(rm.status == "Borrador")
        self._header.set_duplicate_enabled(True)
        self._form.set_readonly(rm.status != "Borrador")
        self._loading = False
        self._trigger_preview_render(self._doc_id)

    def _on_load_error(self, msg: str) -> None:
        self._loading = False
        self._header.set_autosave_state("error")
        QMessageBox.critical(
            self._widget,
            "Error al cargar informe",
            f"No se pudo cargar el informe técnico.\n{msg[:200]}",
        )
        self._do_navigate_back()

    # ── RUT autocomplete ──────────────────────────────────────────────────────

    def _on_rut_entered(self, rut: str) -> None:
        worker = Worker(lambda: _lookup_client(rut))
        worker.signals.result.connect(self._on_client_found)
        worker.signals.error.connect(lambda _: self._on_client_not_found())
        QThreadPool.globalInstance().start(worker)

    def _on_client_found(self, client) -> None:
        self._current_client_id = client.id
        self._form.client_section.fill_client(
            name=client.name,
            address=client.address,
            email=client.email,
            phone=client.phone,
        )

    def _on_client_not_found(self) -> None:
        self._current_client_id = None
        self._form.client_section.show_not_found()

    # ── Number editing ────────────────────────────────────────────────────────

    def _on_number_change_requested(self, new_number: str) -> None:
        if self._doc_id is None:
            return
        doc_id = self._doc_id
        worker = Worker(lambda: _check_number_exists(new_number, doc_id))
        worker.signals.result.connect(
            lambda exists: self._on_number_check_done(exists, new_number)
        )
        worker.signals.error.connect(lambda _: None)
        QThreadPool.globalInstance().start(worker)

    def _on_number_check_done(self, exists: bool, new_number: str) -> None:
        if exists:
            dlg = QMessageBox(self._widget)
            dlg.setWindowTitle("Número en uso")
            dlg.setText(f'El número "{new_number}" ya está asignado a otro documento.')
            dlg.setInformativeText("Elige un número diferente.")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.setStyleSheet(_DIALOG_STYLE)
            dlg.addButton("Aceptar", QMessageBox.ButtonRole.RejectRole)
            dlg.exec()
            return
        doc_id = self._doc_id
        worker = Worker(lambda: _update_document_number(doc_id, new_number))
        worker.signals.result.connect(lambda _: self._on_number_updated(new_number))
        worker.signals.error.connect(lambda msg: print(f"[report] number update error: {msg}"))
        QThreadPool.globalInstance().start(worker)

    def _on_number_updated(self, new_number: str) -> None:
        self._doc_number = new_number
        self._header.set_document_number(new_number)
        self._form.set_number(new_number)

    # ── State transitions ─────────────────────────────────────────────────────

    def _on_finalize(self) -> None:
        if self._doc_id is None and not self._can_save():
            return

        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Finalizar informe técnico")
        dlg.setText("¿Finalizar este informe técnico?")
        dlg.setInformativeText(
            "Las secciones quedarán fijas. Esta acción no se puede deshacer."
        )
        dlg.setIcon(QMessageBox.Icon.Question)
        dlg.setStyleSheet(_DIALOG_STYLE)
        confirm = dlg.addButton("Finalizar", QMessageBox.ButtonRole.AcceptRole)
        dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dlg.setDefaultButton(confirm)
        dlg.exec()
        if dlg.clickedButton() is not confirm:
            return

        self._autosave_timer.stop()

        if self._doc_id is None:
            self._pending_finalize = True
            self._do_autosave()
            return

        self._execute_finalize()

    def _execute_finalize(self) -> None:
        doc_id = self._doc_id
        worker = Worker(lambda: _finalize_report(doc_id))
        worker.signals.result.connect(self._on_finalized)
        worker.signals.error.connect(
            lambda msg: QMessageBox.critical(
                self._widget, "Error al finalizar", msg[:200]
            )
        )
        QThreadPool.globalInstance().start(worker)

    def _on_finalized(self, rm) -> None:
        self._status = "Finalizado"
        self._header.set_status("Finalizado")
        self._header.set_autosave_state("saved")
        self._header.set_number_editable(False)
        self._form.set_readonly(True)

    def _on_duplicate(self) -> None:
        if self._doc_id is None:
            return
        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Duplicar informe técnico")
        dlg.setText("¿Duplicar este informe técnico?")
        dlg.setInformativeText(
            "Se creará un nuevo Borrador con el mismo cliente y secciones."
        )
        dlg.setIcon(QMessageBox.Icon.Question)
        dlg.setStyleSheet(_DIALOG_STYLE)
        confirm = dlg.addButton("Duplicar", QMessageBox.ButtonRole.AcceptRole)
        dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dlg.setDefaultButton(confirm)
        dlg.exec()
        if dlg.clickedButton() is not confirm:
            return

        doc_id = self._doc_id
        worker = Worker(lambda: _duplicate_report(doc_id))
        worker.signals.result.connect(lambda rm: self.open_existing(rm.document_id))
        worker.signals.error.connect(
            lambda msg: QMessageBox.critical(self._widget, "Error al duplicar", msg)
        )
        QThreadPool.globalInstance().start(worker)

    def _on_delete(self) -> None:
        if self._doc_id is None:
            self._do_navigate_back()
            return
        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Eliminar informe técnico")
        dlg.setText("¿Eliminar este informe técnico?")
        dlg.setInformativeText("Esta acción no se puede deshacer.")
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setStyleSheet(_DIALOG_STYLE)
        confirm = dlg.addButton("Eliminar", QMessageBox.ButtonRole.DestructiveRole)
        dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dlg.setDefaultButton(confirm)
        dlg.exec()
        if dlg.clickedButton() is not confirm:
            return

        self._autosave_timer.stop()
        doc_id = self._doc_id
        worker = Worker(lambda: _delete_report(doc_id))
        worker.signals.result.connect(lambda _: self._do_navigate_back())
        worker.signals.error.connect(
            lambda msg: print(f"[report] delete error: {msg}")
        )
        QThreadPool.globalInstance().start(worker)

    # ── Navigation ────────────────────────────────────────────────────────────

    def _on_back(self) -> None:
        if self._autosave_timer.isActive():
            self._autosave_timer.stop()
            if self._can_save() and self._status == "Borrador":
                self._pending_back = True
                self._do_autosave()
                return
        if self._doc_id is None and self._can_save():
            dlg = QMessageBox(self._widget)
            dlg.setWindowTitle("Cambios sin guardar")
            dlg.setText("El informe aún no se ha guardado.")
            dlg.setInformativeText("¿Volver al inicio sin guardar?")
            dlg.setIcon(QMessageBox.Icon.Warning)
            dlg.setStyleSheet(_DIALOG_STYLE)
            discard = dlg.addButton("Volver sin guardar", QMessageBox.ButtonRole.DestructiveRole)
            dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            dlg.setDefaultButton(discard)
            dlg.exec()
            if dlg.clickedButton() is not discard:
                return
        self._do_navigate_back()

    def _do_navigate_back(self) -> None:
        self._pending_back = False
        self.navigation_back.emit()

    # ── Preview render (Ctrl+S) ───────────────────────────────────────────────

    def _on_ctrl_s(self) -> None:
        if self._doc_id is None or self._preview_locked or self._loading:
            return
        self._trigger_preview_render(self._doc_id)

    def _trigger_preview_render(self, doc_id: int) -> None:
        self._preview_locked = True
        next_slot = 1 - self._preview_slot
        self._preview.set_loading(True)
        worker = Worker(lambda: _render_pdf_preview(doc_id, next_slot))
        worker.signals.result.connect(self._on_preview_ready)
        worker.signals.error.connect(self._on_preview_error)
        QThreadPool.globalInstance().start(worker)

    def _on_preview_ready(self, path: Path) -> None:
        self._preview_slot = 1 - self._preview_slot
        self._preview.load_pdf(path)
        self._preview_locked = False

    def _on_preview_error(self, msg: str) -> None:
        self._preview.set_loading(False)
        self._preview_locked = False
        print(f"[report] preview error: {msg}")

    # ── PDF export ────────────────────────────────────────────────────────────

    def _on_generate_pdf(self) -> None:
        if self._doc_id is None:
            QMessageBox.information(
                self._widget,
                "Sin datos",
                "Guarda el informe antes de exportar el PDF.",
            )
            return
        default_dir = Path.home() / "Documents" / "DocPro"
        default_dir.mkdir(parents=True, exist_ok=True)
        default_name = f"{self._doc_number}.pdf" if self._doc_number else "informe.pdf"
        chosen, _ = QFileDialog.getSaveFileName(
            self._widget,
            "Guardar PDF",
            str(default_dir / default_name),
            "PDF (*.pdf)",
        )
        if not chosen:
            return
        doc_id      = self._doc_id
        chosen_path = Path(chosen)
        worker = Worker(lambda: _render_pdf_to_path(doc_id, chosen_path))
        worker.signals.result.connect(lambda _: self._header.set_autosave_state("saved"))
        worker.signals.error.connect(self._on_pdf_error)
        self._header.set_autosave_state("saving")
        QThreadPool.globalInstance().start(worker)

    def _on_pdf_error(self, msg: str) -> None:
        self._header.set_autosave_state("error")
        QMessageBox.critical(self._widget, "Error al exportar PDF", msg)

    # ── Gmail send ────────────────────────────────────────────────────────────

    def _on_send_gmail(self) -> None:
        if self._doc_id is None or self._status != "Finalizado":
            return
        if not self._gmail_svc.is_online() or not self._gmail_svc.is_connected():
            self._offer_mailto()
            return

        doc_id       = self._doc_id
        client_data  = self._form.get_client_data()
        client_email = client_data.get("email") or ""
        client_name  = client_data.get("name") or ""
        subject      = f"Informe Técnico {self._doc_number} - {client_name}"

        worker = Worker(lambda: _render_report_for_send(doc_id))
        worker.signals.result.connect(
            lambda path: self._open_composer(path, doc_id, client_email, subject)
        )
        worker.signals.error.connect(
            lambda msg: QMessageBox.critical(self._widget, "Error al generar PDF", msg)
        )
        QThreadPool.globalInstance().start(worker)

    def _open_composer(
        self, pdf_path: Path, expected_doc_id: int, recipient: str, subject: str
    ) -> None:
        if self._doc_id != expected_doc_id:
            return
        body = (
            f"Estimado/a cliente,\n\n"
            f"Adjunto encontrará el {subject}.\n\n"
            "Quedamos atentos a cualquier consulta.\n\n"
            "Saludos cordiales,"
        )
        dlg = EmailComposerDialog(
            recipient=recipient,
            subject=subject,
            body=body,
            pdf_path=pdf_path,
            accent_color="#1D4ED8",
            parent=self._widget,
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        r, s, b, extras = dlg.get_data()
        self._do_send(r, s, b, pdf_path, expected_doc_id, extras)

    def _do_send(
        self,
        recipient: str,
        subject: str,
        body: str,
        pdf_path: Path,
        doc_id: int,
        extra_attachments: list[Path] | None = None,
    ) -> None:
        self._header.set_autosave_state("saving")
        gmail_svc = self._gmail_svc
        worker = Worker(
            lambda: _send_email_via_gmail(
                gmail_svc, recipient, subject, body, pdf_path, doc_id, extra_attachments or []
            )
        )
        worker.signals.result.connect(self._on_send_success)
        worker.signals.error.connect(self._on_send_error)
        QThreadPool.globalInstance().start(worker)

    def _on_send_success(self, _) -> None:
        self._status = "Enviado"
        self._header.set_status("Enviado")
        self._header.set_autosave_state("saved")
        self._show_send_toast()

    def _on_send_error(self, message: str) -> None:
        self._header.set_autosave_state("error")
        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Error al enviar")
        dlg.setText("No se pudo enviar el correo.")
        dlg.setInformativeText(message[:200])
        dlg.setIcon(QMessageBox.Icon.Critical)
        dlg.setStyleSheet(_DIALOG_STYLE)
        dlg.addButton("Cerrar", QMessageBox.ButtonRole.RejectRole)
        dlg.exec()
        self._header.set_autosave_state("saved")

    def _show_send_toast(self) -> None:
        from docpro_frontend.widgets.success_toast import SuccessToast
        if not hasattr(self, "_send_toast"):
            self._send_toast = SuccessToast(self._widget)
        self._send_toast.show_message("Correo enviado correctamente.")

    def _offer_mailto(self) -> None:
        client_data  = self._form.get_client_data()
        client_email = client_data.get("email") or ""
        client_name  = client_data.get("name") or ""
        subject      = f"Informe Técnico {self._doc_number} - {client_name}"
        mailto       = self._gmail_svc.build_mailto(client_email, subject)

        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Enviar informe técnico")
        if not self._gmail_svc.is_online():
            dlg.setText("Sin conexión a internet.")
        else:
            dlg.setText("No hay una cuenta de Gmail vinculada.")
        dlg.setInformativeText(
            "Se abrirá tu cliente de correo predeterminado para enviar manualmente."
        )
        dlg.setStyleSheet(_DIALOG_STYLE)
        open_btn = dlg.addButton("Abrir cliente de correo", QMessageBox.ButtonRole.AcceptRole)
        dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dlg.exec()

        if dlg.clickedButton() is not open_btn:
            return

        QDesktopServices.openUrl(QUrl(mailto))

        confirm = QMessageBox(self._widget)
        confirm.setWindowTitle("Marcar como enviado")
        confirm.setText("¿Deseas marcar este informe como Enviado?")
        confirm.setStyleSheet(_DIALOG_STYLE)
        mark_btn = confirm.addButton("Marcar como Enviado", QMessageBox.ButtonRole.AcceptRole)
        confirm.addButton("No", QMessageBox.ButtonRole.RejectRole)
        confirm.exec()

        if confirm.clickedButton() is mark_btn:
            doc_id = self._doc_id
            worker = Worker(lambda: _mark_sent(doc_id, client_email, subject))
            worker.signals.result.connect(
                lambda _: (
                    setattr(self, "_status", "Enviado"),
                    self._header.set_status("Enviado"),
                )
            )
            worker.signals.error.connect(lambda msg: print(f"[report] mark_sent error: {msg}"))
            QThreadPool.globalInstance().start(worker)


# ── Worker functions (run in thread pool, no Qt objects) ──────────────────────

def _preview_next_number() -> str:
    try:
        from docpro_backend.db.session import SessionLocal
        from docpro_backend.services.number_service import preview_next_number
    except ImportError:
        raise NotImplementedError("report backend not yet implemented")
    session = SessionLocal()
    try:
        return preview_next_number(session, "report")
    finally:
        session.close()


def _load_report(doc_id: int):
    try:
        from docpro_backend.db.session import SessionLocal
        from docpro_backend.services.report_service import get_report
    except ImportError:
        raise NotImplementedError("report backend not yet implemented")
    session = SessionLocal()
    try:
        return get_report(session, doc_id)
    finally:
        session.close()


def _create_client_and_report(client_data: dict, sections_data: list[dict], trabajo_data: dict | None) -> dict:
    try:
        from docpro_backend.db.session import SessionLocal
        from docpro_backend.repositories.config.clients import ClientRepository
        from docpro_backend.dtos.reports import ReportInput
        from docpro_backend.services.report_service import create_report, update_sections
        from sqlalchemy.exc import NoResultFound
    except ImportError:
        raise NotImplementedError("report backend not yet implemented")
    session = SessionLocal()
    try:
        try:
            client = ClientRepository(session).get_by_rut(client_data["rut"])
        except NoResultFound:
            client = ClientRepository(session).create(
                rut=client_data["rut"],
                name=client_data["name"],
                address=client_data.get("address"),
                email=client_data.get("email"),
                phone=client_data.get("phone"),
            )
        inp = ReportInput(client_id=client.id, number="")
        result = create_report(session, inp)
        _apply_sections(session, result.document_id, sections_data, update_sections, trabajo_data)
        session.commit()
        return {
            "client_id": client.id,
            "doc_id":    result.document_id,
            "number":    result.number,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _save_with_client(
    client_id: int,
    client_data: dict,
    sections_data: list[dict],
    doc_id: int | None,
    trabajo_data: dict | None = None,
):
    try:
        from docpro_backend.db.session import SessionLocal
        from docpro_backend.repositories.config.clients import ClientRepository
        from docpro_backend.dtos.reports import ReportInput
        from docpro_backend.services.report_service import create_report, update_sections
    except ImportError:
        raise NotImplementedError("report backend not yet implemented")
    session = SessionLocal()
    try:
        ClientRepository(session).update(
            client_id,
            name=client_data.get("name") or "",
            address=client_data.get("address"),
            email=client_data.get("email"),
            phone=client_data.get("phone"),
        )
        if doc_id is None:
            inp    = ReportInput(client_id=client_id, number="")
            result = create_report(session, inp)
            _apply_sections(session, result.document_id, sections_data, update_sections, trabajo_data)
            session.commit()
            return result
        else:
            result = _apply_sections(session, doc_id, sections_data, update_sections, trabajo_data)
            session.commit()
            return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _apply_sections(
    session,
    doc_id: int,
    sections_data: list[dict],
    update_sections_fn,
    trabajo_data: dict | None = None,
):
    """Convert form sections data to SectionInput list and call update_sections."""
    import json as _json
    try:
        from docpro_backend.dtos.reports import SectionInput
    except ImportError:
        raise NotImplementedError("report backend not yet implemented")
    inputs = []

    # "Trabajo efectuado" → context section with content_json (position 0, always first)
    if trabajo_data:
        _FIXED = {"local", "fecha", "tipo_equipo"}
        ctx: dict = {}
        if trabajo_data.get("local"):
            ctx["local"] = trabajo_data["local"]
        if trabajo_data.get("fecha"):
            ctx["fecha"] = trabajo_data["fecha"]
        if trabajo_data.get("equipment_type"):
            ctx["tipo_equipo"] = trabajo_data["equipment_type"]
        for extra in trabajo_data.get("extra_fields", []):
            label = extra.get("label", "").strip()
            value = extra.get("value", "").strip()
            if label and value:
                ctx[label.lower().replace(" ", "_")] = value
        if ctx:
            inputs.append(SectionInput(
                temp_id="s_trabajo",
                parent_temp_id=None,
                title="Trabajo efectuado",
                content=None,
                content_json=_json.dumps(ctx, ensure_ascii=False),
                position=0,
            ))

    for sec in sections_data:
        temp_id = f"s{sec['position']}"
        inputs.append(SectionInput(
            temp_id=temp_id,
            parent_temp_id=None,
            title=sec.get("title") or "Sin título",
            content=sec.get("content") or None,
            position=sec["position"],
        ))
        for sub in sec.get("subsections", []):
            inputs.append(SectionInput(
                temp_id=f"{temp_id}_sub{sub['position']}",
                parent_temp_id=temp_id,
                title=sub.get("title") or "Sin título",
                content=sub.get("content") or None,
                position=sub["position"],
            ))
    return update_sections_fn(session, doc_id, inputs)


def _finalize_report(doc_id: int):
    try:
        from docpro_backend.db.session import SessionLocal
        from docpro_backend.services.report_service import finalize_report
    except ImportError:
        raise NotImplementedError("report backend not yet implemented")
    session = SessionLocal()
    try:
        result = finalize_report(session, doc_id)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _delete_report(doc_id: int):
    try:
        from docpro_backend.db.session import SessionLocal
        from docpro_backend.repositories.reports.reports import ReportRepository
    except ImportError:
        raise NotImplementedError("report backend not yet implemented")
    session = SessionLocal()
    try:
        ReportRepository(session).delete(doc_id)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _lookup_client(rut: str):
    try:
        from docpro_backend.db.session import SessionLocal
        from docpro_backend.repositories.config.clients import ClientRepository
        from docpro_backend.dtos.clients import ClientReadModel
    except ImportError:
        raise NotImplementedError("report backend not yet implemented")
    session = SessionLocal()
    try:
        client = ClientRepository(session).get_by_rut(rut)
        return ClientReadModel.from_orm(client)
    finally:
        session.close()


def _render_pdf_preview(doc_id: int, slot: int) -> Path:
    import tempfile as _tmp
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.report_service import get_report, get_company, get_firma
    from docpro_backend.services.pdf_service import render_report_pdf

    tmp_dir = Path(_tmp.gettempdir()) / "docpro"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / f"preview_{doc_id}_{slot}.pdf"

    session = SessionLocal()
    try:
        report       = get_report(session, doc_id)
        company      = get_company(session)
        firma_nombre, firma_cargo, firma_imagen = get_firma(session)
    finally:
        session.close()

    render_report_pdf(report, company, firma_nombre, firma_cargo, firma_imagen, path)
    return path


def _render_pdf_to_path(doc_id: int, path: Path) -> Path:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.report_service import get_report, get_company, get_firma
    from docpro_backend.services.pdf_service import render_report_pdf

    session = SessionLocal()
    try:
        report       = get_report(session, doc_id)
        company      = get_company(session)
        firma_nombre, firma_cargo, firma_imagen = get_firma(session)
    finally:
        session.close()

    render_report_pdf(report, company, firma_nombre, firma_cargo, firma_imagen, path)
    return path


def _render_report_for_send(doc_id: int) -> Path:
    import tempfile as _tmp
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.report_service import get_report, get_company, get_firma
    from docpro_backend.services.pdf_service import render_report_pdf, report_pdf_filename

    tmp_dir = Path(_tmp.gettempdir()) / "docpro"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    session = SessionLocal()
    try:
        report       = get_report(session, doc_id)
        company      = get_company(session)
        firma_nombre, firma_cargo, firma_imagen = get_firma(session)
    finally:
        session.close()

    path = tmp_dir / report_pdf_filename(report)
    render_report_pdf(report, company, firma_nombre, firma_cargo, firma_imagen, path)
    return path


def _send_email_via_gmail(
    gmail_svc: "GmailService",
    recipient: str,
    subject: str,
    body: str,
    pdf_path: Path,
    doc_id: int,
    extra_attachments: list[Path] | None = None,
) -> None:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.documents.documents import DocumentRepository
    from docpro_backend.repositories.mail.send_log import SendLogRepository

    creds = gmail_svc.get_credentials()
    if creds is None:
        raise ValueError(
            "No hay credenciales válidas de Gmail. "
            "Reconecta la cuenta en Configuración → Gmail."
        )
    gmail_svc.send(creds, recipient, subject, body, pdf_path, extra_attachments or [])

    session = SessionLocal()
    try:
        SendLogRepository(session).log_send(doc_id, recipient, subject)
        DocumentRepository(session).update_status(doc_id, "Enviado")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _mark_sent(doc_id: int, recipient: str, subject: str) -> None:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.documents.documents import DocumentRepository
    from docpro_backend.repositories.mail.send_log import SendLogRepository

    session = SessionLocal()
    try:
        SendLogRepository(session).log_send(doc_id, recipient, subject)
        DocumentRepository(session).update_status(doc_id, "Enviado")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _duplicate_report(doc_id: int):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.report_service import duplicate_report
    session = SessionLocal()
    try:
        result = duplicate_report(session, doc_id)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _check_number_exists(number: str, exclude_doc_id: int) -> bool:
    """Returns True if the number is already used by a *different* document."""
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.schema import Document
    session = SessionLocal()
    try:
        doc = session.query(Document).filter(Document.number == number).one_or_none()
        return doc is not None and doc.id != exclude_doc_id
    finally:
        session.close()


def _update_document_number(doc_id: int, number: str) -> None:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.schema import Document
    session = SessionLocal()
    try:
        doc = session.get(Document, doc_id)
        doc.number = number
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


_DIALOG_STYLE = """
QMessageBox          { background: #FFFFFF; }
QMessageBox QLabel   { color: #111827; background: transparent; }
QPushButton {
    background: #F3F4F6; color: #111827;
    border: 1px solid #D1D5DB; border-radius: 6px;
    padding: 6px 20px; font-size: 15px;
}
QPushButton:hover    { background: #E5E7EB; }
QPushButton:default  { background: #1D4ED8; color: #FFFFFF; border-color: #1D4ED8; }
QPushButton:default:hover { background: #1E3A8A; }
"""
