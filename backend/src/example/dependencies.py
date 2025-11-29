"""
Зависимости домена Example.

FastAPI Depends для dependency injection.
Цепочка: get_db -> get_example_repository -> get_example_service
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.example.repository import ExampleRepository
from src.example.service import ExampleService


async def get_example_repository(
    session: AsyncSession = Depends(get_db),
) -> ExampleRepository:
    """Получить ExampleRepository с сессией базы данных."""
    return ExampleRepository(session)


async def get_example_service(
    repository: ExampleRepository = Depends(get_example_repository),
) -> ExampleService:
    """Получить ExampleService с репозиторием."""
    return ExampleService(repository)
