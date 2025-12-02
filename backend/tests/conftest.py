"""
Конфигурация Pytest и общие фикстуры.

Этот модуль предоставляет:
- Настройку тестовой БД (in-memory SQLite)
- AsyncClient для тестирования FastAPI endpoint'ов
- Фикстуры сессий БД
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Импорты с префиксом src. для консистентности с остальным проектом
from src.database import Base, get_db
from src.main import app

# ВАЖНО: Явный импорт всех моделей для регистрации в Base.metadata
# При добавлении новых моделей — добавляйте их сюда
from src.example.models import Example  # noqa: F401


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Использовать asyncio backend для anyio."""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_engine():
    """
    Создать движок тестовой БД.

    Использует in-memory SQLite для быстрых тестов.
    Создаёт чистые таблицы для каждого теста.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    """
    Предоставить чистую сессию БД для каждого теста.

    Сессия откатывается после каждого теста для обеспечения изоляции.
    """
    async_session = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncClient:
    """
    Предоставить тестовый клиент с переопределёнными зависимостями.

    Dependency БД заменяется на тестовую сессию.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
