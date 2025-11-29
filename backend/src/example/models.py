"""
SQLAlchemy модели домена Example.

Синтаксис SQLAlchemy 2.0 с Mapped типами для полной поддержки type hints.
"""

from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.example.constants import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH


class Example(Base):
    """
    Модель Example, демонстрирующая паттерны SQLAlchemy 2.0.

    Используйте Mapped[type] для всех полей для автокомплита IDE и проверки типов.
    """

    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LENGTH), index=True)
    description: Mapped[str | None] = mapped_column(
        Text,
        default=None,
    )
    status: Mapped[str] = mapped_column(String(20), default="draft")
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Example {self.id}: {self.title}>"
