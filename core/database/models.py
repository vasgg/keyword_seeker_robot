from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.current_timestamp()
    )


class Group(Base):
    __tablename__ = "groups"

    telegram_id: Mapped[int] = mapped_column(unique=True)
    link: Mapped[str]
    title: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)

    def __str__(self):
        return f"{self.__class__.__name__}(id={self.id}, group_name={self.link!r})"


class Word(Base):
    __tablename__ = "words"
    keyword: Mapped[str] = mapped_column(unique=True)
    minus_word: Mapped[bool] = mapped_column(default=False, server_default="0")
