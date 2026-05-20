from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from docpro_backend.schema import Client

from ..base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    model = Client

    def get_by_rut(self, rut: str) -> Client:
        obj = self._session.query(Client).filter(Client.rut == rut).one_or_none()
        if obj is None:
            raise NoResultFound(f"Client rut={rut} not found")
        return obj

    def list_all(self) -> list[Client]:
        return self._session.query(Client).order_by(Client.name).all()

    def create(
        self,
        rut: str,
        name: str,
        address: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> Client:
        client = Client(rut=rut, name=name, address=address,
                        email=email, phone=phone)
        self._session.add(client)
        self._session.flush()
        return client

    def update(self, id: int, **kwargs: str | None) -> Client:
        client = self.get_by_id(id)
        for key, value in kwargs.items():
            setattr(client, key, value)
        self._session.flush()
        return client
