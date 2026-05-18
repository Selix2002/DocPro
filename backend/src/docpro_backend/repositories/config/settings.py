from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from docpro_backend.schema import Setting

from ..base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    model = Setting

    def get_by_id(self, id: int) -> Setting:  # type: ignore[override]
        raise NotImplementedError("Use get(key)")

    def get(self, key: str) -> str:
        obj = self._session.get(Setting, key)
        if obj is None:
            raise NoResultFound(f"Setting '{key}' not found")
        return obj.value

    def get_or_none(self, key: str) -> str | None:
        obj = self._session.get(Setting, key)
        return obj.value if obj else None

    def set(self, key: str, value: str) -> Setting:
        obj = self._session.get(Setting, key)
        if obj is None:
            obj = Setting(key=key, value=value)
            self._session.add(obj)
        else:
            obj.value = value
        self._session.flush()
        return obj
