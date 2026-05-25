from __future__ import annotations

from dataclasses import dataclass

from docpro_backend.schema import Client


@dataclass
class ClientInput:
    rut: str
    name: str
    address: str | None = None
    email: str | None = None
    phone: str | None = None


@dataclass(frozen=True)
class ClientReadModel:
    id: int
    rut: str
    name: str
    address: str | None
    email: str | None
    phone: str | None
    created_at: str

    @classmethod
    def from_orm(cls, obj: Client) -> ClientReadModel:
        return cls(
            id=obj.id,
            rut=obj.rut,
            name=obj.name,
            address=obj.address,
            email=obj.email,
            phone=obj.phone,
            created_at=obj.created_at,
        )
