from groq import Groq
from groq import AuthenticationError, APIConnectionError, APIStatusError


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
