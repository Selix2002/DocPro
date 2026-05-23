from PySide6.QtWidgets import QPushButton, QTextEdit
from PySide6.QtCore import QThreadPool

import docpro_frontend.theme as _th
from docpro_frontend.services.worker import Worker


class AiImproveButton(QPushButton):
    """'✦ Mejorar redacción' button wired to a QTextEdit.

    Reads the Groq API key (EncryptionService) and selected model (settings DB)
    inside a background worker, calls GroqService.improve_text(), applies the
    result to the linked field, and shows a FallbackToast when a fallback model
    was used.
    """

    def __init__(self, text_field: QTextEdit, parent=None):
        super().__init__("✦  Mejorar redacción", parent)
        self._field = text_field
        self.setStyleSheet(self._qss())
        self.clicked.connect(self._on_click)

    # ── Internal ──────────────────────────────────────────────────────

    def _qss(self) -> str:
        t = _th.current
        return f"""
QPushButton {{
    background: {t['purple_light']};
    border: 1px solid #E9D5FF;
    border-radius: 7px;
    padding: 5px 10px;
    font-size: 12px; font-weight: 500;
    color: {t['purple']};
}}
QPushButton:hover {{ background: #EDE9FE; }}
QPushButton:disabled {{
    color: {t['placeholder']};
    border-color: {t['border_soft']};
    background: {t['border_soft']};
}}
"""

    def _on_click(self) -> None:
        text = self._field.toPlainText().strip()
        if not text:
            return
        self.setEnabled(False)
        self.setText("Mejorando…")

        def run():
            from docpro_frontend.services.encryption_service import EncryptionService
            from docpro_frontend.services.groq_service import GroqService
            from docpro_backend.db.session import SessionLocal
            from docpro_backend.repositories.config.settings import SettingRepository

            api_key = EncryptionService().load_groq_key()
            if not api_key:
                return None, None, None

            session = SessionLocal()
            try:
                requested = (
                    SettingRepository(session).get_or_none("groq_model")
                    or "llama-3.3-70b-versatile"
                )
            finally:
                session.close()

            improved, actual = GroqService().improve_text(text, api_key, requested)
            return improved, actual, requested

        worker = Worker(run)
        worker.signals.result.connect(self._on_result)
        worker.signals.error.connect(self._on_error)
        QThreadPool.globalInstance().start(worker)

    def _on_result(self, result: tuple) -> None:
        improved, actual_model, requested_model = result
        self._reset()
        if improved is None:
            self.setToolTip(
                "No se pudo mejorar el texto. Verifica tu API key y conexión."
            )
            return
        self.setToolTip("")
        self._show_suggestion_bubble(improved)
        if actual_model and requested_model and actual_model != requested_model:
            self._show_fallback_toast(actual_model)

    def _on_error(self, msg: str) -> None:
        self._reset()
        self.setToolTip(f"Error inesperado: {msg}")

    def _reset(self) -> None:
        self.setEnabled(True)
        self.setText("✦  Mejorar redacción")

    def _show_suggestion_bubble(self, suggestion: str) -> None:
        from docpro_frontend.widgets.suggestion_bubble import SuggestionBubble

        win = self.window()
        if not hasattr(win, "_groq_suggestion_bubble"):
            win._groq_suggestion_bubble = SuggestionBubble(win)
        win._groq_suggestion_bubble.show_suggestion(self._field, suggestion)

    def _show_fallback_toast(self, model_id: str) -> None:
        from docpro_frontend.widgets.fallback_toast import FallbackToast

        win = self.window()
        if not hasattr(win, "_groq_fallback_toast"):
            win._groq_fallback_toast = FallbackToast(win)
        win._groq_fallback_toast.show_message(model_id)
