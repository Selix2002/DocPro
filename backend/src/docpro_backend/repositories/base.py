from typing import Generic, TypeVar

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, id: int) -> T:
        obj = self._session.get(self.model, id)
        if obj is None:
            raise NoResultFound(f"{self.model.__name__} id={id} not found")
        return obj

    def delete(self, id: int) -> None:
        obj = self.get_by_id(id)
        self._session.delete(obj)
        self._session.flush()
