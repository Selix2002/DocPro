from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import QFileDialog, QMessageBox

from docpro_frontend.mail.views.email_composer_dialog import EmailComposerDialog
from docpro_frontend.quote.views.quote_widget import QuoteWidget
from docpro_frontend.services.gmail_service import GmailService
from docpro_frontend.services.worker import Worker


class QuoteService(QObject):
    """
    Service layer for the quote editor.
    Owns the 800ms autosave timer and mediates between QuoteWidget and the
    backend service layer (quote_service, pdf_service, ClientRepository).

    Lazy creation: the Document/Quote rows are only written to DB once a valid
    client_id is known (i.e. after RUT lookup or inline client creation).
    Until then _doc_id is None and the autosave timer does nothing.
    """

    # Emitted after navigating back so main.py can refresh the dashboard
    navigation_back = Signal()

    def __init__(self, widget: QuoteWidget, gmail_svc: GmailService) -> None:
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

    def open_new_for_client(self, client_id: int) -> None:
        self.open_new()
        self._current_client_id = client_id
        worker = Worker(lambda: _load_client_by_id(client_id))
        worker.signals.result.connect(self._on_prefill_client)
        worker.signals.error.connect(lambda _: None)
        QThreadPool.globalInstance().start(worker)

    def _on_prefill_client(self, client) -> None:
        self._form.client_section.set_rut(client.rut)
        self._form.client_section.fill_client(
            name=client.name,
            address=client.address,
            email=client.email,
            phone=client.phone,
        )

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

        worker = Worker(lambda: _load_quote(doc_id))
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
        self._header.approve_requested.connect(self._on_approve)
        self._header.reject_requested.connect(self._on_reject)
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
        data        = self._form.get_data()
        client_data = self._form.get_client_data()
        doc_id      = self._doc_id
        client_id   = self._current_client_id

        if client_id is None and doc_id is None:
            # Nuevo cliente, nueva cotización: crear ambos
            worker = Worker(lambda: _create_client_and_quote(client_data, data))
            worker.signals.result.connect(self._on_client_and_quote_created)
        elif client_id is None and doc_id is not None:
            # Cliente cambiado en cotización existente: crear/encontrar cliente y actualizar doc
            worker = Worker(lambda: _reassign_client_and_update_quote(client_data, data, doc_id))
            worker.signals.result.connect(self._on_client_and_quote_created)
        else:
            # Cliente conocido: actualizar datos de cliente y crear/actualizar cotización
            worker = Worker(lambda: _save_with_client(client_id, client_data, data, doc_id))
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

    def _on_client_and_quote_created(self, result: dict) -> None:
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
        print(f"[quote] autosave error: {msg}")

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
            "Error al cargar cotización",
            f"No se pudo cargar la cotización.\n{msg[:200]}",
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
        worker.signals.error.connect(lambda msg: print(f"[quote] number update error: {msg}"))
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
        dlg.setWindowTitle("Finalizar cotización")
        dlg.setText("¿Finalizar esta cotización?")
        dlg.setInformativeText(
            "Los ítems y totales quedarán fijos. Esta acción no se puede deshacer."
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
            # Quote not yet saved — save first, then finalize
            self._pending_finalize = True
            self._do_autosave()
            return

        self._execute_finalize()

    def _execute_finalize(self) -> None:
        doc_id = self._doc_id
        worker = Worker(lambda: _finalize_quote(doc_id))
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

    def _on_approve(self) -> None:
        if self._doc_id is None:
            return
        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Aprobar cotización")
        dlg.setText("¿Aprobar esta cotización?")
        dlg.setInformativeText("Esta acción es definitiva y no se puede deshacer.")
        dlg.setIcon(QMessageBox.Icon.Question)
        dlg.setStyleSheet(_DIALOG_STYLE)
        confirm = dlg.addButton("Aprobar", QMessageBox.ButtonRole.AcceptRole)
        dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dlg.setDefaultButton(confirm)
        dlg.exec()
        if dlg.clickedButton() is not confirm:
            return
        doc_id = self._doc_id
        worker = Worker(lambda: _approve_quote(doc_id))
        worker.signals.result.connect(self._on_resolved)
        worker.signals.error.connect(lambda msg: print(f"[quote] approve error: {msg}"))
        QThreadPool.globalInstance().start(worker)

    def _on_reject(self) -> None:
        if self._doc_id is None:
            return
        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Rechazar cotización")
        dlg.setText("¿Rechazar esta cotización?")
        dlg.setInformativeText("Esta acción es definitiva y no se puede deshacer.")
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setStyleSheet(_DIALOG_STYLE)
        confirm = dlg.addButton("Rechazar", QMessageBox.ButtonRole.DestructiveRole)
        dlg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        dlg.setDefaultButton(confirm)
        dlg.exec()
        if dlg.clickedButton() is not confirm:
            return
        doc_id = self._doc_id
        worker = Worker(lambda: _reject_quote(doc_id))
        worker.signals.result.connect(self._on_resolved)
        worker.signals.error.connect(lambda msg: print(f"[quote] reject error: {msg}"))
        QThreadPool.globalInstance().start(worker)

    def _on_resolved(self, rm) -> None:
        self._status = rm.status
        self._header.set_status(rm.status)

    def _on_duplicate(self) -> None:
        if self._doc_id is None:
            return
        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Duplicar cotización")
        dlg.setText("¿Duplicar esta cotización?")
        dlg.setInformativeText(
            "Se creará un nuevo Borrador con el mismo cliente e ítems."
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
        worker = Worker(lambda: _duplicate_quote(doc_id))
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
        dlg.setWindowTitle("Eliminar cotización")
        dlg.setText("¿Eliminar esta cotización?")
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
        worker = Worker(lambda: _delete_quote(doc_id))
        worker.signals.result.connect(lambda _: self._do_navigate_back())
        worker.signals.error.connect(lambda msg: print(f"[quote] delete error: {msg}"))
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
            # Form has data but nothing was saved yet — warn the user
            dlg = QMessageBox(self._widget)
            dlg.setWindowTitle("Cambios sin guardar")
            dlg.setText("La cotización aún no se ha guardado.")
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
        print(f"[quote] preview error: {msg}")

    # ── PDF export ────────────────────────────────────────────────────────────

    def _on_generate_pdf(self) -> None:
        if self._doc_id is None:
            QMessageBox.information(
                self._widget,
                "Sin datos",
                "Guarda la cotización antes de exportar el PDF.",
            )
            return
        default_dir = Path.home() / "Documents" / "DocPro"
        default_dir.mkdir(parents=True, exist_ok=True)
        default_name = f"{self._doc_number}.pdf" if self._doc_number else "cotizacion.pdf"
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
        if getattr(self, "_composer_dlg", None) is not None:
            self._composer_dlg.showNormal()
            self._composer_dlg.activateWindow()
            return
        if not self._gmail_svc.is_online() or not self._gmail_svc.is_connected():
            self._offer_mailto()
            return

        doc_id       = self._doc_id
        client_data  = self._form.get_client_data()
        client_email = client_data.get("email") or ""
        client_name  = client_data.get("name") or ""
        subject      = f"Cotización {self._doc_number} - {client_name}"

        worker = Worker(lambda: _render_pdf_for_send(doc_id))
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
            f"Adjunto encontrará la {subject}.\n\n"
            "Quedamos atentos a cualquier consulta.\n\n"
            "Saludos cordiales,"
        )
        dlg = EmailComposerDialog(
            recipient=recipient,
            subject=subject,
            body=body,
            pdf_path=pdf_path,
            accent_color="#B45309",
            parent=self._widget,
        )
        self._composer_dlg = dlg  # prevent garbage collection

        def _on_accepted():
            r, s, b, chosen_pdf, pdf_name, extras = dlg.get_data()
            self._do_send(r, s, b, chosen_pdf, pdf_name, expected_doc_id, extras)

        dlg.accepted.connect(_on_accepted)
        dlg.finished.connect(lambda _: setattr(self, "_composer_dlg", None))
        dlg.show()

    def _do_send(
        self,
        recipient: str,
        subject: str,
        body: str,
        pdf_path: Path | None,
        pdf_name: str | None,
        doc_id: int,
        extra_attachments: list[Path] | None = None,
    ) -> None:
        self._header.set_autosave_state("saving")
        gmail_svc = self._gmail_svc
        worker = Worker(
            lambda: _send_email_via_gmail(
                gmail_svc, recipient, subject, body, pdf_path, doc_id,
                extra_attachments or [], pdf_name,
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
        subject      = f"Cotización {self._doc_number} - {client_name}"
        mailto       = self._gmail_svc.build_mailto(client_email, subject)

        dlg = QMessageBox(self._widget)
        dlg.setWindowTitle("Enviar cotización")
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
        confirm.setText("¿Deseas marcar esta cotización como Enviada?")
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
            worker.signals.error.connect(lambda msg: print(f"[quote] mark_sent error: {msg}"))
            QThreadPool.globalInstance().start(worker)


# ── Worker functions (run in thread pool, no Qt objects) ──────────────────────

def _preview_next_number() -> str:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.number_service import preview_next_number
    session = SessionLocal()
    try:
        return preview_next_number(session, "quote")
    finally:
        session.close()


def _load_quote(doc_id: int):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import get_quote
    session = SessionLocal()
    try:
        return get_quote(session, doc_id)
    finally:
        session.close()


def _create_quote(client_id: int, data: dict):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.dtos.quotes import QuoteInput, QuoteItemInput
    from docpro_backend.services.quote_service import create_quote
    session = SessionLocal()
    try:
        inp = QuoteInput(
            client_id=client_id,
            number=data.get("number", ""),
            issue_date=data["issue_date"],
            observations_json=data.get("observations_json"),
            items=[
                QuoteItemInput(
                    quantity=i["quantity"],
                    description=i["description"],
                    unit_price=i["unit_price"],
                    position=i["position"],
                )
                for i in data.get("items", [])
            ],
        )
        result = create_quote(session, inp)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _update_quote(doc_id: int, data: dict):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.dtos.quotes import QuoteInput, QuoteItemInput
    from docpro_backend.services.quote_service import update_quote
    session = SessionLocal()
    try:
        inp = QuoteInput(
            client_id=0,  # client_id not changed by update
            number="",
            issue_date=data["issue_date"],
            observations_json=data.get("observations_json"),
            items=[
                QuoteItemInput(
                    quantity=i["quantity"],
                    description=i["description"],
                    unit_price=i["unit_price"],
                    position=i["position"],
                )
                for i in data.get("items", [])
            ],
        )
        result = update_quote(session, doc_id, inp)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _finalize_quote(doc_id: int):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import finalize_quote
    session = SessionLocal()
    try:
        result = finalize_quote(session, doc_id)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _delete_quote(doc_id: int):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.quotes.quotes import QuoteRepository
    session = SessionLocal()
    try:
        QuoteRepository(session).delete(doc_id)
        session.commit()
        return True
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _save_with_client(client_id: int, client_data: dict, form_data: dict, doc_id: int | None):
    """Update client fields, then create or update the quote — single transaction."""
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.config.clients import ClientRepository
    from docpro_backend.dtos.quotes import QuoteInput, QuoteItemInput
    from docpro_backend.services.quote_service import create_quote, update_quote
    session = SessionLocal()
    try:
        ClientRepository(session).update(
            client_id,
            name=client_data.get("name") or "",
            address=client_data.get("address"),
            email=client_data.get("email"),
            phone=client_data.get("phone"),
        )
        inp = QuoteInput(
            client_id=client_id,
            number=form_data.get("number", ""),
            issue_date=form_data["issue_date"],
            observations_json=form_data.get("observations_json"),
            show_iva=form_data.get("show_iva", True),
            items=[
                QuoteItemInput(
                    quantity=i["quantity"],
                    description=i["description"],
                    unit_price=i["unit_price"],
                    position=i["position"],
                )
                for i in form_data.get("items", [])
            ],
        )
        result = create_quote(session, inp) if doc_id is None else update_quote(session, doc_id, inp)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _reassign_client_and_update_quote(client_data: dict, form_data: dict, doc_id: int) -> dict:
    """Encuentra o crea el cliente con el nuevo RUT, reasigna el documento y actualiza la cotización."""
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.config.clients import ClientRepository
    from docpro_backend.dtos.quotes import QuoteInput, QuoteItemInput
    from docpro_backend.services.quote_service import update_quote
    from docpro_backend.schema.documents.documents import Document
    from sqlalchemy.exc import NoResultFound
    session = SessionLocal()
    try:
        try:
            client = ClientRepository(session).get_by_rut(client_data["rut"])
            ClientRepository(session).update(
                client.id,
                name=client_data.get("name") or "",
                address=client_data.get("address"),
                email=client_data.get("email"),
                phone=client_data.get("phone"),
            )
        except NoResultFound:
            client = ClientRepository(session).create(
                rut=client_data["rut"],
                name=client_data["name"],
                address=client_data.get("address"),
                email=client_data.get("email"),
                phone=client_data.get("phone"),
            )
        doc = session.get(Document, doc_id)
        doc.client_id = client.id
        session.flush()
        inp = QuoteInput(
            client_id=client.id,
            number=form_data.get("number", ""),
            issue_date=form_data["issue_date"],
            observations_json=form_data.get("observations_json"),
            show_iva=form_data.get("show_iva", True),
            items=[
                QuoteItemInput(
                    quantity=i["quantity"],
                    description=i["description"],
                    unit_price=i["unit_price"],
                    position=i["position"],
                )
                for i in form_data.get("items", [])
            ],
        )
        result = update_quote(session, doc_id, inp)
        session.commit()
        return {"client_id": client.id, "doc_id": doc_id, "number": result.number}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _create_client_and_quote(client_data: dict, form_data: dict) -> dict:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.config.clients import ClientRepository
    from docpro_backend.dtos.quotes import QuoteInput, QuoteItemInput
    from docpro_backend.services.quote_service import create_quote
    from sqlalchemy.exc import NoResultFound
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
        inp = QuoteInput(
            client_id=client.id,
            number=form_data.get("number", ""),
            issue_date=form_data["issue_date"],
            observations_json=form_data.get("observations_json"),
            show_iva=form_data.get("show_iva", True),
            items=[
                QuoteItemInput(
                    quantity=i["quantity"],
                    description=i["description"],
                    unit_price=i["unit_price"],
                    position=i["position"],
                )
                for i in form_data.get("items", [])
            ],
        )
        result = create_quote(session, inp)
        session.commit()
        return {"client_id": client.id, "doc_id": result.document_id, "number": result.number}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _approve_quote(doc_id: int):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import approve_quote
    session = SessionLocal()
    try:
        result = approve_quote(session, doc_id)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _reject_quote(doc_id: int):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import reject_quote
    session = SessionLocal()
    try:
        result = reject_quote(session, doc_id)
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _load_client_by_id(client_id: int):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.config.clients import ClientRepository
    from docpro_backend.dtos.clients import ClientReadModel
    session = SessionLocal()
    try:
        client = ClientRepository(session).get_by_id(client_id)
        return ClientReadModel.from_orm(client)
    finally:
        session.close()


def _lookup_client(rut: str):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.config.clients import ClientRepository
    from docpro_backend.dtos.clients import ClientReadModel
    session = SessionLocal()
    try:
        client = ClientRepository(session).get_by_rut(rut)
        return ClientReadModel.from_orm(client)
    finally:
        session.close()


def _create_client(data: dict):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.repositories.config.clients import ClientRepository
    from docpro_backend.dtos.clients import ClientReadModel
    session = SessionLocal()
    try:
        client = ClientRepository(session).create(
            rut=data["rut"],
            name=data["name"],
            address=data.get("address"),

            email=data.get("email"),
            phone=data.get("phone"),
        )
        session.commit()
        return ClientReadModel.from_orm(client)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _render_pdf_preview(doc_id: int, slot: int) -> Path:
    import tempfile as _tmp
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import get_quote, get_company
    from docpro_backend.services.pdf_service import render_quote_pdf
    from docpro_backend.services.theme_service import get_theme, get_header_imagen

    tmp_dir = Path(_tmp.gettempdir()) / "docpro"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / f"preview_{doc_id}_{slot}.pdf"

    session = SessionLocal()
    try:
        quote   = get_quote(session, doc_id)
        company = get_company(session)
        theme   = get_theme(session)
        header  = get_header_imagen(session)
    finally:
        session.close()

    render_quote_pdf(quote, company, path, theme=theme, header_imagen=header)
    return path


def _render_pdf_to_path(doc_id: int, path: Path) -> Path:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import get_quote, get_company
    from docpro_backend.services.pdf_service import render_quote_pdf
    from docpro_backend.services.theme_service import get_theme, get_header_imagen

    session = SessionLocal()
    try:
        quote   = get_quote(session, doc_id)
        company = get_company(session)
        theme   = get_theme(session)
        header  = get_header_imagen(session)
    finally:
        session.close()

    render_quote_pdf(quote, company, path, theme=theme, header_imagen=header)
    return path


def _render_pdf_for_send(doc_id: int) -> Path:
    import tempfile as _tmp
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import get_quote, get_company
    from docpro_backend.services.pdf_service import render_quote_pdf, quote_pdf_filename
    from docpro_backend.services.theme_service import get_theme, get_header_imagen

    tmp_dir = Path(_tmp.gettempdir()) / "docpro"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    session = SessionLocal()
    try:
        quote   = get_quote(session, doc_id)
        company = get_company(session)
        theme   = get_theme(session)
        header  = get_header_imagen(session)
    finally:
        session.close()

    path = tmp_dir / quote_pdf_filename(quote)
    render_quote_pdf(quote, company, path, theme=theme, header_imagen=header)
    return path


def _send_email_via_gmail(
    gmail_svc: "GmailService",
    recipient: str,
    subject: str,
    body: str,
    pdf_path: Path | None,
    doc_id: int,
    extra_attachments: list[Path] | None = None,
    pdf_name: str | None = None,
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
    gmail_svc.send(
        creds, recipient, subject, body, pdf_path,
        extra_attachments or [], pdf_name,
    )

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


def _duplicate_quote(doc_id: int):
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import duplicate_quote
    session = SessionLocal()
    try:
        result = duplicate_quote(session, doc_id)
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
QPushButton:default  { background: #B45309; color: #FFFFFF; border-color: #B45309; }
QPushButton:default:hover { background: #92400E; }
"""
