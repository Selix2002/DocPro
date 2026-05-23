import socket

from groq import Groq
from groq import AuthenticationError, APIConnectionError, APIStatusError

_SYSTEM_PROMPT = (
    "Eres un asistente de redacción técnica en español. "
    "Mejora el siguiente texto para que sea claro, formal y profesional, "
    "sin cambiar su significado ni agregar información nueva. "
    "Devuelve únicamente el texto mejorado, sin explicaciones."
)
_FALLBACK_CHAIN = ["llama-3.3-70b-versatile", "groq/compound-mini"]
_ABORT = object()
_RETRY = object()


def _is_online() -> bool:
    try:
        socket.create_connection(("api.groq.com", 443), timeout=2)
        return True
    except OSError:
        return False


def _call_once(text: str, api_key: str, model: str) -> object:
    try:
        resp = Groq(api_key=api_key).chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        content = resp.choices[0].message.content
        return content.strip() if content and content.strip() else _RETRY
    except AuthenticationError:
        return _ABORT
    except APIConnectionError:
        return _ABORT
    except APIStatusError:
        return _RETRY
    except Exception:
        return _ABORT


class GroqService:
    def validate(self, api_key: str, model: str) -> tuple[bool, str]:
        """Returns (ok, message). Calls models.list() as a cheap auth check."""
        if not api_key.strip():
            return False, "La API key no puede estar vacía"
        try:
            Groq(api_key=api_key).models.list()
            return True, "API key válida"
        except AuthenticationError:
            return False, "API key inválida"
        except APIConnectionError:
            return False, "Sin conexión a internet"
        except APIStatusError as e:
            return False, f"Error {e.status_code}"
        except Exception as e:
            return False, str(e)

    def improve_text(
        self, text: str, api_key: str, model: str
    ) -> tuple[str | None, str | None]:
        """Returns (improved_text, actual_model_used). Both None on any failure."""
        if not api_key or not text.strip():
            return None, None
        if not _is_online():
            return None, None
        chain = [model] + [m for m in _FALLBACK_CHAIN if m != model]
        for candidate in chain:
            result = _call_once(text, api_key, candidate)
            if result is _ABORT:
                return None, None
            if result is not _RETRY:
                return result, candidate  # type: ignore[return-value]
        return None, None
