"""
Тесты для Example Service (Бизнес-логика).

Тестируют слой сервиса — бизнес-правила и валидацию.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.example.exceptions import ExampleAlreadyExistsError, ExampleNotFoundError
from src.example.repository import ExampleRepository
from src.example.schemas import ExampleCreate, ExampleUpdate
from src.example.service import ExampleService


@pytest.fixture
def example_service(db_session: AsyncSession) -> ExampleService:
    """Создать ExampleService с тестовой сессией БД."""
    repository = ExampleRepository(db_session)
    return ExampleService(repository)


@pytest.mark.asyncio
async def test_create_example(example_service: ExampleService) -> None:
    """Тест корректного создания example сервисом."""
    data = ExampleCreate(title="Service Test", description="Description")

    example = await example_service.create(data)

    assert example.id is not None
    assert example.title == "Service Test"
    assert example.description == "Description"
    assert example.status == "draft"


@pytest.mark.asyncio
async def test_create_duplicate_raises(example_service: ExampleService) -> None:
    """Тест выброса ошибки сервисом при дубликате заголовка."""
    data = ExampleCreate(title="Duplicate")

    await example_service.create(data)

    with pytest.raises(ExampleAlreadyExistsError):
        await example_service.create(data)


@pytest.mark.asyncio
async def test_get_by_id(example_service: ExampleService) -> None:
    """Тест получения example по ID сервисом."""
    data = ExampleCreate(title="Get By ID Test")
    created = await example_service.create(data)

    example = await example_service.get_by_id(created.id)

    assert example.id == created.id
    assert example.title == "Get By ID Test"


@pytest.mark.asyncio
async def test_get_by_id_not_found(example_service: ExampleService) -> None:
    """Тест выброса ошибки сервисом при несуществующем ID."""
    with pytest.raises(ExampleNotFoundError):
        await example_service.get_by_id(99999)


@pytest.mark.asyncio
async def test_get_all_with_pagination(example_service: ExampleService) -> None:
    """Тест возврата пагинированных результатов сервисом."""
    # Создать 5 examples
    for i in range(5):
        await example_service.create(ExampleCreate(title=f"Item {i}"))

    examples, total = await example_service.get_all(skip=0, limit=3)

    assert total == 5
    assert len(examples) == 3


@pytest.mark.asyncio
async def test_update_example(example_service: ExampleService) -> None:
    """Тест обновления example сервисом."""
    created = await example_service.create(ExampleCreate(title="Original"))

    updated = await example_service.update(
        created.id,
        ExampleUpdate(title="Updated", status="published"),
    )

    assert updated.title == "Updated"
    assert updated.status == "published"


@pytest.mark.asyncio
async def test_delete_example(example_service: ExampleService) -> None:
    """Тест удаления example сервисом."""
    created = await example_service.create(ExampleCreate(title="To Delete"))

    await example_service.delete(created.id)

    with pytest.raises(ExampleNotFoundError):
        await example_service.get_by_id(created.id)
