from __future__ import annotations

from dataclasses import dataclass

from docpro_backend.schema import CompanyProfile, SectionTemplate


@dataclass
class CompanyProfileInput:
    name: str
    city: str | None = None
    email: str | None = None
    phone: str | None = None


@dataclass(frozen=True)
class CompanyProfileReadModel:
    id: int
    name: str
    city: str | None
    email: str | None
    phone: str | None

    @classmethod
    def from_orm(cls, obj: CompanyProfile) -> CompanyProfileReadModel:
        return cls(
            id=obj.id,
            name=obj.name,
            city=obj.city,
            email=obj.email,
            phone=obj.phone,
        )


@dataclass(frozen=True)
class SectionTemplateReadModel:
    id: int
    name: str
    title: str
    content: str | None
    content_json: str | None
    created_at: str

    @classmethod
    def from_orm(cls, obj: SectionTemplate) -> SectionTemplateReadModel:
        return cls(
            id=obj.id,
            name=obj.name,
            title=obj.title,
            content=obj.content,
            content_json=obj.content_json,
            created_at=obj.created_at,
        )
