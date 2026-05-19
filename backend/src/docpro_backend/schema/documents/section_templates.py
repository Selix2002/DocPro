from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class SectionTemplate(Base):
    __tablename__ = "section_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    title: Mapped[str]
    content: Mapped[str | None]
    content_json: Mapped[str | None]
    usage_count: Mapped[int] = mapped_column(server_default="0")
    created_at: Mapped[str] = mapped_column(server_default="CURRENT_TIMESTAMP")
