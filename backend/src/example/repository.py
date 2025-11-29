"""
Репозиторий домена Example.

Слой репозитория обрабатывает ТОЛЬКО доступ к БД.
Никакой бизнес-логики здесь — только CRUD операции.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.example.models import Example


class ExampleRepository:
    """
    Репозиторий для модели Example.

    Выполняет все операции с БД для examples.
    Возвращает ORM объекты или None, никогда не выбрасывает бизнес-исключения.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, example: Example) -> Example:
        """Создать новый example."""
        self.session.add(example)
        await self.session.flush()
        await self.session.refresh(example)
        return example

    async def get_by_id(self, example_id: int) -> Example | None:
        """Получить example по ID."""
        return await self.session.get(Example, example_id)

    async def get_by_title(self, title: str) -> Example | None:
        """Получить example по заголовку."""
        result = await self.session.execute(
            select(Example).where(Example.title == title)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> list[Example]:
        """Получить все examples с опциональной фильтрацией."""
        query = select(Example).offset(skip).limit(limit)

        if is_active is not None:
            query = query.where(Example.is_active == is_active)

        query = query.order_by(Example.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, is_active: bool | None = None) -> int:
        """Подсчитать общее количество examples."""
        query = select(func.count(Example.id))

        if is_active is not None:
            query = query.where(Example.is_active == is_active)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(self, example: Example) -> Example:
        """Обновить example."""
        await self.session.flush()
        await self.session.refresh(example)
        return example

    async def delete(self, example: Example) -> None:
        """Удалить example."""
        await self.session.delete(example)
        await self.session.flush()
