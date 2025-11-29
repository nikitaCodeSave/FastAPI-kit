"""
Pydantic схемы домена Example.

Синтаксис Pydantic V2 с model_config вместо class Config.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.example.constants import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH


class ExampleBase(BaseModel):
    """Базовая схема с общими полями."""

    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)


class ExampleCreate(ExampleBase):
    """Схема для создания нового example."""

    pass


class ExampleUpdate(BaseModel):
    """Схема для обновления example. Все поля опциональны."""

    title: str | None = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    status: str | None = None
    is_active: bool | None = None


class ExampleResponse(ExampleBase):
    """Схема для ответа example."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
