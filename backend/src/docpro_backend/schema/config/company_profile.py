from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class CompanyProfile(Base):
    __tablename__ = "company_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    city: Mapped[str | None]
    email: Mapped[str | None]
    phone: Mapped[str | None]
