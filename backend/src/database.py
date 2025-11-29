"""
Конфигурация базы данных и управление сессиями.

Предоставляет асинхронный движок БД, фабрику сессий и dependency injection
для сессий базы данных в endpoint'ах FastAPI.
"""

from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

# Соглашение об именовании constraints (для консистентных имён миграций)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(AsyncAttrs, DeclarativeBase):
    """
    Базовый класс для всех SQLAlchemy моделей.

    Mixin AsyncAttrs позволяет безопасно обращаться к lazy-loaded связям
    в асинхронном контексте через синтаксис `await`.

    Пример:
        user = await session.get(User, 1)
        posts = await user.awaitable_attrs.posts  # Безопасный async доступ
    """

    metadata = MetaData(naming_convention=convention)


class DatabaseSessionManager:
    """
    Управляет жизненным циклом движка БД и фабрики сессий.

    Этот класс обеспечивает удобный способ инициализации и освобождения
    подключений к БД при старте/остановке приложения.
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def init(self, db_url: str) -> None:
        """
        Инициализировать движок БД и фабрику сессий.

        Вызывается при старте приложения в lifespan manager.
        """
        # SQLite не поддерживает настройки пула
        if settings.is_sqlite:
            self._engine = create_async_engine(
                db_url,
                echo=settings.DB_ECHO,
                connect_args={"check_same_thread": False},
            )
        else:
            self._engine = create_async_engine(
                db_url,
                echo=settings.DB_ECHO,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_recycle=settings.DB_POOL_RECYCLE,
                pool_pre_ping=True,
            )

        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        """
        Освободить движок БД.

        Вызывается при остановке приложения в lifespan manager.
        """
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    async def create_tables(self) -> None:
        """
        Создать все таблицы, определённые в моделях.

        Только для разработки/демо. В production используйте Alembic миграции.
        """
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Получить фабрику сессий, вызывая исключение если не инициализирована."""
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        return self._sessionmaker

    @property
    def engine(self) -> AsyncEngine:
        """Получить движок, вызывая исключение если не инициализирован."""
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        return self._engine


# Глобальный экземпляр менеджера сессий
sessionmanager = DatabaseSessionManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency, предоставляющий сессию базы данных.

    Сессия автоматически коммитится при успехе, откатывается при ошибке
    и закрывается после завершения запроса.

    Использование:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with sessionmanager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
