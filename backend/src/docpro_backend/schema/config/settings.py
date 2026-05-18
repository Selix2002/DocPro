from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]
