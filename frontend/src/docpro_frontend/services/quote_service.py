from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QThreadPool, QTimer, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFileDialog, QMessageBox

from docpro_frontend.quote.views.quote_widget import QuoteWidget
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

    def __init__(self, widget: QuoteWidget) -> None:
        super().__init__()
        self._widget  = widget
        self._header  = widget.header
        self._form    = widget.form
        self._preview = widget.preview

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
        self._header.approve_requested.connect(self._on_approve)
        self._header.reject_requested.connect(self._on_reject)
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

        if client_id is None:
            # New client: create client + quote atomically
            worker = Worker(lambda: _create_client_and_quote(client_data, data))
            worker.signals.result.connect(self._on_client_and_quote_created)
        else:
            # Existing client: update client fields + create or update quote
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
        if self._pending_back:
            self._do_navigate_back()
        elif self._pending_finalize:
            self._pending_finalize = False
            self._execute_finalize()

    def _on_client_and_quote_created(self, result: dict) -> None:
        self._current_client_id = result["client_id"]
        self._doc_id            = result["doc_id"]
        self._doc_number        = result["number"]
        self._form.set_number(result["number"])
        self._form.lock_number()
        self._header.set_document_number(result["number"])
        self._header.set_autosave_state("saved")
        if self._pending_back:
            self._do_navigate_back()
        elif self._pending_finalize:
            self._pending_finalize = False
            self._execute_finalize()

    def _on_autosaved(self, _) -> None:
        self._header.set_autosave_state("saved")
        if self._pending_back:
            self._do_navigate_back()

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
        if rm.status != "Borrador":
            self._form.set_readonly(True)
        self._loading = False
        self._trigger_preview_render(self._doc_id)

    def _on_load_error(self, msg: str) -> None:
        self._loading = False
        self._header.set_autosave_state("error")
        print(f"[quote] load error: {msg}")

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
        self._form.client_section.clear_client_fields()

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
        worker.signals.error.connect(lambda msg: print(f"[quote] finalize error: {msg}"))
        QThreadPool.globalInstance().start(worker)

    def _on_finalized(self, rm) -> None:
        self._status = "Finalizado"
        self._header.set_status("Finalizado")
        self._header.set_autosave_state("saved")
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
            observations=data.get("observations"),
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
            observations=data.get("observations"),
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
            observations=form_data.get("observations"),
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
            observations=form_data.get("observations"),
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

    tmp_dir = Path(_tmp.gettempdir()) / "docpro"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / f"preview_{doc_id}_{slot}.pdf"

    session = SessionLocal()
    try:
        quote   = get_quote(session, doc_id)
        company = get_company(session)
    finally:
        session.close()

    render_quote_pdf(quote, company, path)
    return path


def _render_pdf_to_path(doc_id: int, path: Path) -> Path:
    from docpro_backend.db.session import SessionLocal
    from docpro_backend.services.quote_service import get_quote, get_company
    from docpro_backend.services.pdf_service import render_quote_pdf

    session = SessionLocal()
    try:
        quote   = get_quote(session, doc_id)
        company = get_company(session)
    finally:
        session.close()

    render_quote_pdf(quote, company, path)
    return path


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
