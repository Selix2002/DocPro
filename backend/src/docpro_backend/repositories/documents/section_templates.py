from sqlalchemy.orm import Session

from docpro_backend.schema import SectionTemplate

from ..base import BaseRepository


class SectionTemplateRepository(BaseRepository[SectionTemplate]):
    model = SectionTemplate

    def list_all(self) -> list[SectionTemplate]:
        return (
            self._session.query(SectionTemplate)
            .order_by(SectionTemplate.name)
            .all()
        )

    def create(
        self,
        name: str,
        title: str,
        content: str | None = None,
        content_json: str | None = None,
    ) -> SectionTemplate:
        template = SectionTemplate(name=name, title=title, content=content,
                                   content_json=content_json)
        self._session.add(template)
        self._session.flush()
        return template
