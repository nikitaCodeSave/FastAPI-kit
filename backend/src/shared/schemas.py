"""
Общие Pydantic схемы.

Переиспользуемые схемы для различных доменов.
"""

from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationParams:
    """
    Параметры пагинации для list endpoint'ов.

    Использование:
        @router.get("/items")
        async def list_items(
            pagination: PaginationParams = Depends(),
        ) -> PaginatedResponse[ItemResponse]:
            ...
    """

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(20, ge=1, le=100, description="Макс. записей для возврата"),
    ) -> None:
        self.skip = skip
        self.limit = limit


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic обёртка для пагинированного ответа.

    Использование:
        return PaginatedResponse(
            items=items,
            total=total_count,
            skip=pagination.skip,
            limit=pagination.limit,
        )
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    skip: int
    limit: int

    @property
    def has_more(self) -> bool:
        """Проверить, есть ли ещё элементы для получения."""
        return self.skip + len(self.items) < self.total
