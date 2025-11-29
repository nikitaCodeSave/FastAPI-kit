"""
Сервис домена Example.

Слой сервиса содержит ВСЮ бизнес-логику.
Это сердце домена — валидация, правила, оркестрация.
"""

from src.example.exceptions import ExampleAlreadyExistsError, ExampleNotFoundError
from src.example.models import Example
from src.example.repository import ExampleRepository
from src.example.schemas import ExampleCreate, ExampleUpdate


class ExampleService:
    """
    Сервис для бизнес-логики домена Example.

    Все бизнес-правила и валидация происходят здесь.
    Роутер должен быть ТОНКИМ — только HTTP-заботы.
    """

    def __init__(self, repository: ExampleRepository) -> None:
        self.repository = repository

    async def create(self, data: ExampleCreate) -> Example:
        """
        Создать новый example.

        Raises:
            ExampleAlreadyExistsError: Если заголовок уже существует
        """
        # Бизнес-правило: заголовок должен быть уникальным
        existing = await self.repository.get_by_title(data.title)
        if existing:
            raise ExampleAlreadyExistsError(
                f"Example with title '{data.title}' already exists"
            )

        example = Example(
            title=data.title,
            description=data.description,
        )
        return await self.repository.create(example)

    async def get_by_id(self, example_id: int) -> Example:
        """
        Получить example по ID.

        Raises:
            ExampleNotFoundError: Если example не найден
        """
        example = await self.repository.get_by_id(example_id)
        if not example:
            raise ExampleNotFoundError(f"Example {example_id} not found")
        return example

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> tuple[list[Example], int]:
        """
        Получить все examples с пагинацией.

        Returns:
            Tuple из (список examples, общее количество)
        """
        examples = await self.repository.get_all(
            skip=skip,
            limit=limit,
            is_active=is_active,
        )
        total = await self.repository.count(is_active=is_active)
        return examples, total

    async def update(self, example_id: int, data: ExampleUpdate) -> Example:
        """
        Обновить example.

        Raises:
            ExampleNotFoundError: Если example не найден
            ExampleAlreadyExistsError: Если новый заголовок уже существует
        """
        example = await self.get_by_id(example_id)

        # Проверить уникальность заголовка при изменении
        if data.title and data.title != example.title:
            existing = await self.repository.get_by_title(data.title)
            if existing:
                raise ExampleAlreadyExistsError(
                    f"Example with title '{data.title}' already exists"
                )

        # Применить обновления (только не-None поля)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(example, field, value)

        return await self.repository.update(example)

    async def delete(self, example_id: int) -> None:
        """
        Удалить example.

        Raises:
            ExampleNotFoundError: Если example не найден
        """
        example = await self.get_by_id(example_id)
        await self.repository.delete(example)
