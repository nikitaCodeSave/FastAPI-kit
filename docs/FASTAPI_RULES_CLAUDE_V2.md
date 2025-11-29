# FastAPI Development Rules & Best Practices (2024-2025)

> **Системные правила для AI-агентов и разработчиков при работе с FastAPI проектами**
> 
> Версия: 3.0 (Ноябрь 2025)  
> Основано на официальных рекомендациях, community consensus, production patterns и верифицированном исследовании

---

## 🎯 КРИТИЧЕСКИЕ ИМПЕРАТИВЫ

### Обязательный технологический стек

```python
# ✅ ПРАВИЛЬНО - Current Stack 2024-2025
fastapi = "^0.121.2"
pydantic = "^2.10"
pydantic-settings = "^2.6"
sqlalchemy = "^2.0"
asyncpg = "^0.30"              # PostgreSQL async driver
uvicorn = {extras = ["standard"], version = "^0.32"}
httpx = "^0.28"                # Async HTTP client
structlog = "^24.4"            # Structured logging
```

### Абсолютные запреты

**НИКОГДА не используй:**
- Docker образ `tiangolo/uvicorn-gunicorn-fastapi` (deprecated)
- Декораторы `@app.on_event("startup")` / `@app.on_event("shutdown")` (deprecated)
- Sync библиотеки в async функциях (`requests`, `pymongo`, sync SQLAlchemy)
- `asyncio.gather()` с одним AsyncSession для нескольких DB запросов
- Возврат ORM моделей напрямую из эндпоинтов
- Hardcoded secrets в коде

---

## 📁 DOMAIN-BASED АРХИТЕКТУРА

### Правило #1: Структура проекта по доменам

**Для приложений с 2+ доменами используй Domain-Based структуру:**

```
project/
├── src/
│   ├── auth/                    # Домен авторизации
│   │   ├── __init__.py
│   │   ├── router.py           # API endpoints (THIN, только HTTP)
│   │   ├── service.py          # Бизнес-логика (ОБЯЗАТЕЛЬНО)
│   │   ├── repository.py       # Database access
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── dependencies.py     # Domain-specific Depends
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── constants.py        # Domain constants
│   │
│   ├── users/                  # Другой домен
│   │   └── [аналогичная структура]
│   │
│   ├── posts/                  # Ещё один домен
│   │   └── [аналогичная структура]
│   │
│   ├── shared/                 # Общий код (минимум!)
│   │   ├── __init__.py
│   │   ├── exceptions.py       # Базовые исключения
│   │   └── schemas.py          # Общие схемы (pagination и т.д.)
│   │
│   ├── config.py               # Settings (Pydantic BaseSettings)
│   ├── database.py             # DB connection & session management
│   └── main.py                 # FastAPI app initialization
│
├── tests/
│   ├── auth/
│   │   ├── test_router.py
│   │   └── test_service.py
│   ├── users/
│   ├── conftest.py             # Shared fixtures
│   └── factories.py            # Test data factories
│
├── alembic/
│   ├── versions/
│   └── env.py
├── alembic.ini
├── pyproject.toml
├── .env
├── .env.example
└── Dockerfile
```

**ПРАВИЛО:** Каждый домен = self-contained модуль со ВСЕМИ необходимыми компонентами.

### Правило #2: Строгие правила импортов между слоями

```
┌─────────────────────────────────────────────────────────────┐
│                      HTTP Request                           │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  ROUTER (router.py)                                         │
│  - Только HTTP concerns: валидация входа, формирование      │
│    ответа, статус-коды                                      │
│  - Импортирует: Service, Schemas, Dependencies              │
│  - НЕ импортирует: Repository, Models напрямую              │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  SERVICE (service.py)                                       │
│  - ВСЯ бизнес-логика здесь                                  │
│  - Импортирует: Repository, Schemas, другие Services        │
│  - Бросает Domain Exceptions                                │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  REPOSITORY (repository.py)                                 │
│  - Только доступ к данным, никакой бизнес-логики            │
│  - Импортирует: Models, Database utilities                  │
│  - Возвращает ORM объекты или None                          │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  DATABASE                                                   │
└─────────────────────────────────────────────────────────────┘
```

**Кросс-доменная коммуникация:**

```python
# ✅ ПРАВИЛЬНО - явные префиксные импорты
from src.auth import service as auth_service
from src.users import service as users_service

class PostService:
    async def create_post(self, data: PostCreate, author_id: int) -> Post:
        # Вызов другого сервиса через импорт
        user = await users_service.get_user(author_id)
        if not user.can_create_posts:
            raise InsufficientPermissionsError()
        ...

# ❌ НЕПРАВИЛЬНО - star imports
from src.auth.service import *

# ❌ НЕПРАВИЛЬНО - прямой импорт repository из другого домена
from src.users.repository import UserRepository
```

### Правило #3: Три слоя ответственности (ОБЯЗАТЕЛЬНО)

```python
# ❌ НЕПРАВИЛЬНО - бизнес-логика в router
@router.post("/users")
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # НЕТ! Логика не должна быть здесь
    existing = await db.execute(select(User).where(User.email == user_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email exists")
    user = User(**user_data.model_dump())
    db.add(user)
    await db.commit()
    return user

# ✅ ПРАВИЛЬНО - разделение ответственности

# 1. Router (THIN) - только HTTP concerns
@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Create new user - endpoint handles ONLY HTTP layer."""
    return await service.create_user(user_data)

# 2. Service Layer - ВСЯ бизнес-логика здесь
class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository
    
    async def create_user(self, data: UserCreate) -> User:
        """Business logic for user creation."""
        # Validation
        if await self.repository.get_by_email(data.email):
            raise UserAlreadyExistsError(f"Email {data.email} already registered")
        
        # Business rules
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        return await self.repository.create(user)

# 3. Repository Layer - только доступ к данным
class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def create(self, user: User) -> User:
        """Pure data access - no business logic."""
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)
```

**ИМПЕРАТИВ:** Router НИКОГДА не содержит бизнес-логику. Только HTTP: валидация входа, вызов service, формирование ответа.

---

## 🚀 PRODUCTION-READY ШАБЛОНЫ

### Шаблон main.py

```python
"""
FastAPI Application Entry Point.

This module initializes the FastAPI application with all necessary
configurations, middleware, and routers.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.database import sessionmanager

# Import routers
from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.posts.router import router as posts_router

# Import exception handlers
from src.auth.exceptions import AuthenticationError, AuthorizationError
from src.users.exceptions import UserNotFoundError, UserAlreadyExistsError
from src.shared.exceptions import DomainError

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Replaces deprecated @app.on_event decorators.
    Handles startup and shutdown events.
    """
    # STARTUP
    logger.info(
        "starting_application",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
    )
    
    # Initialize database
    sessionmanager.init(settings.DATABASE_URL)
    
    yield
    
    # SHUTDOWN
    if sessionmanager._engine is not None:
        await sessionmanager.close()
    
    logger.info("application_shutdown_complete")


def create_application() -> FastAPI:
    """Application factory pattern."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    )
    
    # ─────────────────────────────────────────────────────────────
    # MIDDLEWARE (добавляются в обратном порядке выполнения)
    # ─────────────────────────────────────────────────────────────
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )
    
    # ─────────────────────────────────────────────────────────────
    # EXCEPTION HANDLERS
    # ─────────────────────────────────────────────────────────────
    
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        """Handle all domain exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "authentication_error", "message": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(
        request: Request, exc: AuthorizationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "authorization_error", "message": str(exc)},
        )
    
    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "not_found", "message": str(exc)},
        )
    
    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(
        request: Request, exc: UserAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "conflict", "message": str(exc)},
        )
    
    # Generic exception handler (LAST)
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            error=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
            },
        )
    
    # ─────────────────────────────────────────────────────────────
    # HEALTH CHECK
    # ─────────────────────────────────────────────────────────────
    
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """
        Health check endpoint for load balancers and orchestrators.
        
        Returns basic application status and version.
        """
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }
    
    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> dict:
        """
        Readiness check - verifies all dependencies are available.
        
        Used by Kubernetes readiness probes.
        """
        # TODO: Add actual dependency checks (DB, Redis, etc.)
        return {"status": "ready"}
    
    # ─────────────────────────────────────────────────────────────
    # ROUTERS
    # ─────────────────────────────────────────────────────────────
    
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(posts_router, prefix="/api/v1/posts", tags=["Posts"])
    
    return app


app = create_application()
```

### Шаблон config.py

```python
"""
Application Configuration.

All settings are loaded from environment variables with sensible defaults.
Uses pydantic-settings for validation and type coercion.
"""
from functools import lru_cache
from typing import Literal

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.
    
    All settings can be overridden via environment variables.
    Nested settings use double underscore delimiter (e.g., POSTGRES__HOST).
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )
    
    # ─────────────────────────────────────────────────────────────
    # APPLICATION
    # ─────────────────────────────────────────────────────────────
    
    PROJECT_NAME: str = "FastAPI Application"
    PROJECT_DESCRIPTION: str = "Production-ready FastAPI service"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    
    # ─────────────────────────────────────────────────────────────
    # SECURITY
    # ─────────────────────────────────────────────────────────────
    
    SECRET_KEY: str  # ОБЯЗАТЕЛЬНО из environment!
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # ─────────────────────────────────────────────────────────────
    # DATABASE
    # ─────────────────────────────────────────────────────────────
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "app"
    
    # Connection pool settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False  # SQL logging
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Async PostgreSQL connection string."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Sync PostgreSQL connection string (for Alembic)."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ─────────────────────────────────────────────────────────────
    # CORS
    # ─────────────────────────────────────────────────────────────
    
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # ─────────────────────────────────────────────────────────────
    # REDIS (optional)
    # ─────────────────────────────────────────────────────────────
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ─────────────────────────────────────────────────────────────
    # LOGGING
    # ─────────────────────────────────────────────────────────────
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Settings are cached to avoid re-reading .env file on every access.
    """
    return Settings()


settings = get_settings()
```

### Шаблон database.py

```python
"""
Database Configuration and Session Management.

Provides async database engine, session factory, and dependency injection
for database sessions in FastAPI endpoints.
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

# ─────────────────────────────────────────────────────────────
# NAMING CONVENTION FOR CONSTRAINTS
# ─────────────────────────────────────────────────────────────

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# ─────────────────────────────────────────────────────────────
# BASE MODEL
# ─────────────────────────────────────────────────────────────

class Base(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    AsyncAttrs mixin enables safe access to lazy-loaded relationships
    in async context using `await` syntax.
    
    Example:
        user = await session.get(User, 1)
        posts = await user.awaitable_attrs.posts  # Safe async access
    """
    
    metadata = MetaData(naming_convention=convention)


# ─────────────────────────────────────────────────────────────
# DATABASE SESSION MANAGER
# ─────────────────────────────────────────────────────────────

class DatabaseSessionManager:
    """
    Manages database engine and session factory lifecycle.
    
    This class provides a clean way to initialize and dispose of
    database connections during application startup/shutdown.
    """
    
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None
    
    def init(self, db_url: str) -> None:
        """
        Initialize database engine and session factory.
        
        Called during application startup in lifespan manager.
        """
        self._engine = create_async_engine(
            db_url,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # КРИТИЧНО для production
        )
        
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,  # КРИТИЧНО для async
            autocommit=False,
            autoflush=False,
        )
    
    async def close(self) -> None:
        """
        Dispose of database engine.
        
        Called during application shutdown in lifespan manager.
        """
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory, raising if not initialized."""
        if self._sessionmaker is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        return self._sessionmaker
    
    @property
    def engine(self) -> AsyncEngine:
        """Get engine, raising if not initialized."""
        if self._engine is None:
            raise RuntimeError("DatabaseSessionManager is not initialized")
        return self._engine


# Global session manager instance
sessionmanager = DatabaseSessionManager()


# ─────────────────────────────────────────────────────────────
# DEPENDENCY INJECTION
# ─────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Session is automatically committed on success, rolled back on error,
    and closed after the request completes.
    
    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with sessionmanager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### Шаблон shared/exceptions.py

```python
"""
Base Domain Exceptions.

All domain-specific exceptions should inherit from DomainError.
This enables centralized exception handling in main.py.
"""
from typing import Any


class DomainError(Exception):
    """
    Base exception for all domain errors.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (e.g., "user_not_found")
        status_code: HTTP status code for this error
        details: Additional error details (optional)
    """
    
    message: str = "A domain error occurred"
    error_code: str = "domain_error"
    status_code: int = 400
    
    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(DomainError):
    """Resource not found."""
    
    message = "Resource not found"
    error_code = "not_found"
    status_code = 404


class AlreadyExistsError(DomainError):
    """Resource already exists."""
    
    message = "Resource already exists"
    error_code = "already_exists"
    status_code = 409


class ValidationError(DomainError):
    """Business validation failed."""
    
    message = "Validation failed"
    error_code = "validation_error"
    status_code = 422


class AuthenticationError(DomainError):
    """Authentication failed."""
    
    message = "Authentication failed"
    error_code = "authentication_error"
    status_code = 401


class AuthorizationError(DomainError):
    """Authorization failed."""
    
    message = "Insufficient permissions"
    error_code = "authorization_error"
    status_code = 403
```

### Шаблон domain/exceptions.py (пример для users)

```python
"""
User Domain Exceptions.

All user-specific exceptions that can be raised by UserService.
"""
from src.shared.exceptions import NotFoundError, AlreadyExistsError, ValidationError


class UserNotFoundError(NotFoundError):
    """User not found by ID or email."""
    
    message = "User not found"
    error_code = "user_not_found"


class UserAlreadyExistsError(AlreadyExistsError):
    """User with given email already exists."""
    
    message = "User with this email already exists"
    error_code = "user_already_exists"


class InvalidCredentialsError(ValidationError):
    """Invalid email or password."""
    
    message = "Invalid email or password"
    error_code = "invalid_credentials"


class UserInactiveError(ValidationError):
    """User account is inactive."""
    
    message = "User account is inactive"
    error_code = "user_inactive"
```

---

## 💉 DEPENDENCY INJECTION PATTERNS

### Правило #4: Используй встроенный Depends для 95% случаев

```python
# ✅ ПРАВИЛЬНО - стандартный паттерн для большинства приложений

# 1. Database session dependency (в database.py)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmanager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# 2. Repository dependency (в domain/dependencies.py)
async def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(session)

# 3. Service dependency (использует repository)
async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)

# 4. Current user dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service),
) -> User:
    """Get authenticated user from JWT token."""
    payload = decode_token(token)
    user = await service.get_by_id(payload.sub)
    if not user:
        raise AuthenticationError("User not found")
    return user

# 5. Использование в endpoint
@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI автоматически resolve всю цепочку зависимостей:
    get_current_user -> get_user_service -> get_user_repository -> get_db
    """
    return current_user
```

**ПРАВИЛО:** Dependency может зависеть от других dependencies. FastAPI автоматически строит граф зависимостей и кэширует результаты в рамках одного запроса.

### Правило #5: Dependencies с yield для cleanup (ОБЯЗАТЕЛЬНО)

```python
# ✅ ПРАВИЛЬНО - async generator с yield для ресурсов

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmanager.session_factory() as session:
        try:
            yield session  # Код до yield выполняется ДО эндпоинта
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        # Код после yield ВСЕГДА выполнится (cleanup)

# Для sync зависимостей
def get_redis() -> Generator[Redis, None, None]:
    client = Redis(host="localhost")
    try:
        yield client
    finally:
        client.close()
```

**КРИТИЧНО:** Cleanup код после `yield` выполняется ДАЖЕ при exceptions в endpoint.

### Правило #6: Sub-dependencies для композиции

```python
# ✅ ПРАВИЛЬНО - композиция зависимостей для authorization

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверяет что пользователь активен."""
    if not current_user.is_active:
        raise AuthorizationError("User account is inactive")
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Проверяет что пользователь активен И суперюзер."""
    if not current_user.is_superuser:
        raise AuthorizationError("Superuser access required")
    return current_user

# Использование
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    service: UserService = Depends(get_user_service),
) -> None:
    """Только активные суперюзеры могут удалять пользователей."""
    await service.delete_user(user_id)
```

**ПАТТЕРН:** Строй сложные authorization/validation проверки через композицию простых dependencies.

---

## ⚡ ASYNC PATTERNS (КРИТИЧЕСКИ ВАЖНО)

### Правило #7: Async определения везде, await только для I/O

```python
# ✅ ПРАВИЛЬНО - async def ВЕЗДЕ для консистентности

@router.get("/users/{user_id}")
async def get_user(  # async def ВСЕГДА, даже если нет await внутри
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Endpoint определен как async для консистентности."""
    return await service.get_by_id(user_id)

# ❌ НЕПРАВИЛЬНО - sync def в async приложении
@router.get("/users/{user_id}")
def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    # Не сможешь использовать await!
    pass
```

**ИМПЕРАТИВ:** Определяй ВСЕ эндпоинты как `async def` для консистентности, даже если внутри нет `await`.

### Правило #8: Используй async только с async библиотеками

```python
# ❌ НЕПРАВИЛЬНО - blocking библиотека в async функции
import requests  # Sync библиотека

@router.get("/external")
async def get_external():
    # БЛОКИРУЕТ event loop на время HTTP запроса!
    response = requests.get("https://api.example.com")  
    return response.json()

# ✅ ПРАВИЛЬНО - async библиотека
import httpx  # Async библиотека

@router.get("/external")
async def get_external():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()
```

**Async библиотеки для разных задач:**

| Задача | Sync (❌ НЕ используй) | Async (✅ Используй) |
|--------|----------------------|---------------------|
| HTTP requests | requests | httpx |
| PostgreSQL | psycopg2 | asyncpg |
| MongoDB | pymongo | motor |
| Redis | redis | redis.asyncio, aioredis |
| Files | open() | aiofiles |

**ПРАВИЛО:** НИКОГДА не используй sync библиотеки (requests, pymongo, sync SQLAlchemy) в async функциях.

### Правило #9: CPU-bound операции в executor

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

def cpu_intensive_task(data: list[int]) -> int:
    """Sync функция для CPU-bound операции."""
    return sum(x * x for x in data)

@router.post("/compute")
async def compute(data: list[int]) -> dict:
    """Async endpoint выполняет CPU-bound работу в отдельном процессе."""
    loop = asyncio.get_running_loop()
    
    # Выполнить в отдельном процессе, не блокируя event loop
    result = await loop.run_in_executor(
        None,  # None = default ThreadPoolExecutor
        cpu_intensive_task,
        data,
    )
    
    return {"result": result}
```

**ПРАВИЛО:** Для CPU-intensive операций (вычисления, обработка изображений) используй `run_in_executor()`.

### Правило #10: AsyncSession НЕ для concurrent операций

```python
# ❌ КРИТИЧЕСКАЯ ОШИБКА - asyncio.gather() с одним AsyncSession
@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """НЕПРАВИЛЬНО! AsyncSession не thread-safe для concurrent access."""
    
    # Это вызовет InvalidRequestError или race conditions!
    users_task = db.execute(select(func.count(User.id)))
    posts_task = db.execute(select(func.count(Post.id)))
    
    users_result, posts_result = await asyncio.gather(
        users_task,
        posts_task,
    )

# ✅ ПРАВИЛЬНО - один запрос с несколькими агрегатами
@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)) -> dict:
    """Выполняем все агрегаты одним запросом."""
    
    stmt = select(
        func.count(User.id).label("users_count"),
        func.count(Post.id).label("posts_count"),
    ).select_from(User).outerjoin(Post)
    
    result = await db.execute(stmt)
    row = result.one()
    
    return {"users": row.users_count, "posts": row.posts_count}

# ✅ АЛЬТЕРНАТИВА - отдельные sessions для параллелизма
@router.get("/dashboard-parallel")
async def get_dashboard_parallel() -> dict:
    """Используем отдельные sessions для настоящего параллелизма."""
    
    async def count_users() -> int:
        async with sessionmanager.session_factory() as session:
            result = await session.execute(select(func.count(User.id)))
            return result.scalar_one()
    
    async def count_posts() -> int:
        async with sessionmanager.session_factory() as session:
            result = await session.execute(select(func.count(Post.id)))
            return result.scalar_one()
    
    # Теперь каждая coroutine использует свою session
    users, posts = await asyncio.gather(count_users(), count_posts())
    
    return {"users": users, "posts": posts}

# ✅ asyncio.gather() OK для РАЗНЫХ ресурсов
@router.get("/external-data")
async def get_external_data(db: AsyncSession = Depends(get_db)) -> dict:
    """Параллельные запросы к РАЗНЫМ ресурсам - это OK."""
    
    async def fetch_external_api() -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.example.com/data")
            return response.json()
    
    async def fetch_from_db() -> list:
        result = await db.execute(select(User).limit(10))
        return result.scalars().all()
    
    # Это OK - разные ресурсы (HTTP и DB)
    api_data, db_data = await asyncio.gather(
        fetch_external_api(),
        fetch_from_db(),
    )
    
    return {"api": api_data, "db": [u.email for u in db_data]}
```

**КРИТИЧЕСКОЕ ПРАВИЛО:**
- AsyncSession **НЕ потокобезопасен** и **НЕ для concurrent использования**
- Один AsyncSession = одна последовательность операций
- **НЕ используй** с `asyncio.gather()` для нескольких DB запросов
- **НЕ передавай** в multiple concurrent tasks
- **Для параллелизма DB запросов**: создавай отдельные sessions через `session_factory()`
- **Лучше**: оптимизируй запросы (агрегаты в одном SELECT, JOINs) вместо попыток параллелизма

---

## 🗄️ DATABASE PATTERNS (SQLAlchemy 2.0)

### Правило #11: SQLAlchemy 2.0 синтаксис с Mapped types

```python
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.posts.models import Post

class User(Base):
    __tablename__ = "users"
    
    # Mapped[type] - ОБЯЗАТЕЛЬНО для type hints
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    
    # Optional типы для nullable
    bio: Mapped[str | None] = mapped_column(Text, default=None)
    avatar_url: Mapped[str | None] = mapped_column(String(500), default=None)
    
    # Defaults
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships (type hints КРИТИЧНЫ)
    # lazy="raise" - выбросит ошибку если попытаться загрузить без eager loading
    posts: Mapped[list["Post"]] = relationship(
        back_populates="author",
        lazy="raise",  # Защита от N+1
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"


class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(default=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationship с правильным type hint
    author: Mapped["User"] = relationship(back_populates="posts", lazy="raise")
    
    def __repr__(self) -> str:
        return f"<Post {self.title}>"
```

**ИМПЕРАТИВ:** Используй `Mapped[type]` для ВСЕХ полей. Это даёт IDE autocomplete и type checking.

**ВАЖНО:** `lazy="raise"` на relationships помогает обнаружить N+1 проблемы в development - выбросит исключение если попытаться получить доступ к relationship без явного eager loading.

### Правило #12: Eager loading для N+1 проблемы

```python
from sqlalchemy.orm import selectinload, joinedload

# ❌ НЕПРАВИЛЬНО - N+1 запросов
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)) -> list[UserWithPosts]:
    result = await db.execute(select(User))
    users = result.scalars().all()
    # При сериализации Pydantic попытается получить posts для каждого user
    # = 1 запрос для users + N запросов для posts каждого user
    return [UserWithPosts.model_validate(u) for u in users]

# ✅ ПРАВИЛЬНО - один запрос с eager loading
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)) -> list[UserWithPosts]:
    result = await db.execute(
        select(User).options(selectinload(User.posts))
    )
    users = result.scalars().all()
    # Все данные загружены одним запросом (или двумя с selectinload)
    return [UserWithPosts.model_validate(u) for u in users]
```

**Выбор стратегии загрузки:**

| Тип связи | Стратегия | Причина |
|-----------|-----------|---------|
| many-to-one | `joinedload()` | Один JOIN, эффективно |
| one-to-many | `selectinload()` | Отдельный IN запрос, избегает дублирования |
| many-to-many | `selectinload()` | Отдельные запросы, чище |

```python
# Комбинированный пример
result = await db.execute(
    select(Post)
    .options(
        joinedload(Post.author),           # many-to-one: JOIN
        selectinload(Post.comments),       # one-to-many: отдельный запрос
        selectinload(Post.tags),           # many-to-many: отдельный запрос
    )
    .where(Post.is_published == True)
)
```

**КРИТИЧНО:** ВСЕГДА используй eager loading (`selectinload`, `joinedload`) когда нужны связанные данные.

### Правило #13: AsyncAttrs для безопасного доступа к lazy relationships

```python
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

class Base(AsyncAttrs, DeclarativeBase):
    """Base с AsyncAttrs для безопасного async доступа."""
    pass

# Использование
async def get_user_with_posts(db: AsyncSession, user_id: int) -> User:
    user = await db.get(User, user_id)
    
    # ❌ НЕПРАВИЛЬНО - может вызвать MissingGreenlet
    # posts = user.posts
    
    # ✅ ПРАВИЛЬНО - безопасный async доступ
    posts = await user.awaitable_attrs.posts
    
    return user
```

---

## 📝 PYDANTIC V2 SCHEMAS

### Правило #14: Pydantic V2 синтаксис

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ─────────────────────────────────────────────────────────────
# BASE SCHEMAS
# ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    """Base schema - общие поля."""
    
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    bio: str | None = None


class UserCreate(UserBase):
    """Schema для создания - добавляем password."""
    
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    """Schema для обновления - все поля опциональны."""
    
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=50)
    bio: str | None = None
    
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str | None) -> str | None:
        """Normalize email to lowercase."""
        return v.lower() if v else None


class UserResponse(UserBase):
    """Schema для ответа API - включает DB поля."""
    
    id: int
    is_active: bool
    created_at: datetime
    
    # V2: model_config вместо class Config
    model_config = ConfigDict(from_attributes=True)


class UserWithPosts(UserResponse):
    """User с вложенными posts."""
    
    posts: list["PostResponse"] = []


# ─────────────────────────────────────────────────────────────
# USAGE
# ─────────────────────────────────────────────────────────────

# Создание из dict
user_data = {"email": "test@example.com", "username": "testuser", "password": "secure123"}
user = UserCreate.model_validate(user_data)

# Создание из ORM объекта
db_user = await db.get(User, 1)
user_response = UserResponse.model_validate(db_user)

# Конвертация в dict
user_dict = user_response.model_dump()
user_dict_exclude = user_response.model_dump(exclude={"created_at"})
user_dict_include = user_response.model_dump(include={"id", "email"})

# Конвертация в JSON
user_json = user_response.model_dump_json()
```

**V2 API Reference:**

| Действие | Метод |
|----------|-------|
| Создать из dict | `Model.model_validate(data)` |
| Создать из ORM | `Model.model_validate(orm_obj)` (с `from_attributes=True`) |
| В dict | `model.model_dump()` |
| В JSON string | `model.model_dump_json()` |
| JSON Schema | `Model.model_json_schema()` |

### Правило #15: НИКОГДА не возвращай ORM модели напрямую

```python
# ❌ НЕПРАВИЛЬНО - возврат ORM модели
@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    user = await db.get(User, user_id)
    return user  # ПРОБЛЕМЫ: lazy loading, circular refs, лишние поля

# ✅ ПРАВИЛЬНО - конвертация в Pydantic schema
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.get_by_id(user_id)
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    return UserResponse.model_validate(user)
```

**ИМПЕРАТИВ:** ВСЕГДА конвертируй ORM models → Pydantic schemas перед возвратом.

---

## 🎨 API DESIGN PATTERNS

### Правило #16: Правильные HTTP методы и статус-коды

```python
from fastapi import status

# ─────────────────────────────────────────────────────────────
# CRUD ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """POST для создания ресурса, возвращает 201."""
    return await service.create_user(user_data)


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """GET для получения, по умолчанию 200."""
    user = await service.get_by_id(user_id)
    if not user:
        raise UserNotFoundError(f"User {user_id} not found")
    return UserResponse.model_validate(user)


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List all users",
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max users to return"),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """GET для списка с пагинацией."""
    users = await service.get_all(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Replace user",
)
async def replace_user(
    user_id: int,
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """PUT для полной замены ресурса."""
    return await service.replace_user(user_id, user_data)


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """PATCH для частичного обновления."""
    return await service.update_user(user_id, user_data)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> None:
    """DELETE возвращает 204 No Content."""
    await service.delete_user(user_id)


# ─────────────────────────────────────────────────────────────
# ACTION ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.post(
    "/users/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate user",
)
async def activate_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Action endpoint - используй POST."""
    return await service.activate_user(user_id)


@router.post(
    "/users/{user_id}/send-verification-email",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send verification email",
)
async def send_verification_email(
    user_id: int,
    background_tasks: BackgroundTasks,
    service: UserService = Depends(get_user_service),
) -> dict:
    """Async action - возвращает 202 Accepted."""
    user = await service.get_by_id(user_id)
    background_tasks.add_task(send_email, user.email, "verify")
    return {"message": "Verification email queued"}
```

**HTTP методы и статус-коды:**

| Метод | Назначение | Успешный статус |
|-------|------------|-----------------|
| GET | Получение | 200 OK |
| POST | Создание | 201 Created |
| POST | Action | 200 OK или 202 Accepted |
| PUT | Полная замена | 200 OK |
| PATCH | Частичное обновление | 200 OK |
| DELETE | Удаление | 204 No Content |

### Правило #17: Query parameters с валидацией

```python
from fastapi import Query
from enum import Enum

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class UserSortBy(str, Enum):
    CREATED_AT = "created_at"
    USERNAME = "username"
    EMAIL = "email"

@router.get("/users", response_model=list[UserResponse])
async def list_users(
    # Пагинация
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    
    # Фильтрация
    search: str | None = Query(
        None,
        min_length=2,
        max_length=100,
        description="Search by username or email",
    ),
    is_active: bool | None = Query(None, description="Filter by active status"),
    
    # Сортировка
    sort_by: UserSortBy = Query(UserSortBy.CREATED_AT, description="Sort field"),
    order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    
    # Service
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """
    List users with filtering, sorting, and pagination.
    
    Query parameters с валидацией:
    - skip/limit для пагинации с ограничениями
    - search опциональный с min_length
    - is_active опциональный фильтр
    - sort_by/order с enum для allowed values
    """
    users = await service.get_all(
        skip=skip,
        limit=limit,
        search=search,
        is_active=is_active,
        sort_by=sort_by.value,
        order=order.value,
    )
    return [UserResponse.model_validate(u) for u in users]
```

**ПРАВИЛО:** Используй `Query()` для валидации и документации query parameters.

---

## 🧪 TESTING PATTERNS

### Правило #18: Async tests с pytest-asyncio

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

```python
# tests/conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database import Base, get_db
from src.main import app
from src.config import settings


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio backend for anyio."""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    """Provide clean database session for each test."""
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
    """Provide test client with overridden dependencies."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()


# tests/users/test_router.py
async def test_create_user(client: AsyncClient) -> None:
    """Test user creation endpoint."""
    response = await client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "securepass123",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert "password" not in data
    assert "id" in data


async def test_create_user_duplicate_email(client: AsyncClient) -> None:
    """Test creating user with duplicate email returns 409."""
    user_data = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "password123",
    }
    
    # Create first user
    response = await client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
    
    # Try to create second user with same email
    user_data["username"] = "user2"
    response = await client.post("/api/v1/users", json=user_data)
    assert response.status_code == 409
    assert response.json()["error"] == "user_already_exists"


async def test_get_user_not_found(client: AsyncClient) -> None:
    """Test getting non-existent user returns 404."""
    response = await client.get("/api/v1/users/999999")
    assert response.status_code == 404
    assert response.json()["error"] == "user_not_found"


# tests/users/test_service.py
async def test_user_service_create(db_session: AsyncSession) -> None:
    """Test UserService.create_user method."""
    from src.users.service import UserService
    from src.users.repository import UserRepository
    from src.users.schemas import UserCreate
    
    repository = UserRepository(db_session)
    service = UserService(repository)
    
    user_data = UserCreate(
        email="service@example.com",
        username="serviceuser",
        password="password123",
    )
    
    user = await service.create_user(user_data)
    
    assert user.id is not None
    assert user.email == "service@example.com"
    assert user.hashed_password != "password123"


async def test_user_service_duplicate_raises(db_session: AsyncSession) -> None:
    """Test creating user with duplicate email raises error."""
    from src.users.service import UserService
    from src.users.repository import UserRepository
    from src.users.schemas import UserCreate
    from src.users.exceptions import UserAlreadyExistsError
    
    repository = UserRepository(db_session)
    service = UserService(repository)
    
    user_data = UserCreate(
        email="dupe@example.com",
        username="user1",
        password="password123",
    )
    
    # Create first user
    await service.create_user(user_data)
    
    # Try to create second user with same email
    with pytest.raises(UserAlreadyExistsError):
        await service.create_user(user_data)
```

**ПРАВИЛО:**
- Используй **pytest-asyncio** с `asyncio_mode = "auto"`
- Override dependencies через `app.dependency_overrides`
- Используй in-memory SQLite (`sqlite+aiosqlite:///:memory:`) для быстрых тестов
- ВСЕГДА очищай `dependency_overrides` после тестов

---

## ⚡ PERFORMANCE PATTERNS

### Правило #19: Connection pooling настройки

```python
engine = create_async_engine(
    DATABASE_URL,
    # Connection pool settings
    pool_size=5,            # Размер pool для нормальной нагрузки
    max_overflow=10,        # Дополнительные соединения при пиках
    pool_timeout=30,        # Timeout ожидания свободного соединения
    pool_recycle=3600,      # Пересоздавать соединения каждый час
    pool_pre_ping=True,     # КРИТИЧНО: проверять соединения перед использованием
    
    # Query settings
    echo=False,             # Отключить SQL logging в production
)
```

**Рекомендации:**

| Параметр | Development | Production | Описание |
|----------|-------------|------------|----------|
| `pool_size` | 2-5 | 5-20 | Постоянные соединения |
| `max_overflow` | 5 | 10-20 | Временные при пиках |
| `pool_pre_ping` | True | **True** | Проверка соединений |
| `pool_recycle` | 3600 | 3600 | Обновление соединений |
| `echo` | True | **False** | SQL logging |

**КРИТИЧНО:** `pool_pre_ping=True` необходим для production — предотвращает ошибки от устаревших соединений.

### Правило #20: Streaming responses для больших данных

```python
from fastapi.responses import StreamingResponse
import json

async def generate_users_stream(db: AsyncSession):
    """Generate users JSON stream."""
    yield '{"users": ['
    
    result = await db.stream(select(User))
    first = True
    
    async for user in result.scalars():
        if not first:
            yield ","
        first = False
        
        user_dict = UserResponse.model_validate(user).model_dump()
        yield json.dumps(user_dict)
    
    yield ']}'


@router.get("/users/export")
async def export_users(db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    """Export all users as streaming JSON."""
    return StreamingResponse(
        generate_users_stream(db),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=users.json"},
    )
```

**ПРАВИЛО:** Используй StreamingResponse для больших ответов вместо загрузки всего в память.

---

## 🔒 SECURITY PATTERNS

### Правило #21: OAuth2 + JWT

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {e}")


# Dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service),
) -> User:
    """Get current authenticated user."""
    payload = decode_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload")
    
    user = await service.get_by_id(int(user_id))
    if not user:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthorizationError("User is inactive")
    
    return user


# Login endpoint
@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service),
) -> dict:
    """Authenticate user and return JWT token."""
    user = await service.authenticate(form_data.username, form_data.password)
    
    access_token = create_access_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
```

**ИМПЕРАТИВ:** НИКОГДА не храни пароли plain text. Используй bcrypt. SECRET_KEY только из environment.

### Правило #22: CORS configuration

```python
from src.config import settings

# В main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,  # Явный список!
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=600,
)
```

**ПРАВИЛО:** НИКОГДА не используй `allow_origins=["*"]` с `allow_credentials=True` в production.

---

## 🚀 DEPLOYMENT

### Правило #23: Modern Dockerfile

```dockerfile
# syntax=docker/dockerfile:1

# ─────────────────────────────────────────────────────────────
# Stage 1: Builder
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ─────────────────────────────────────────────────────────────
# Stage 2: Runtime
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY ./src ./src
COPY ./alembic ./alembic
COPY ./alembic.ini .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

**ПРАВИЛО:** 
- Используй official Python image + multi-stage build
- НЕ используй deprecated `tiangolo/uvicorn-gunicorn-fastapi`
- Используй `fastapi run` команду

---

## 📊 OBSERVABILITY

### Правило #24: Structured logging

```python
# src/logging_config.py
import logging
import structlog
from src.config import settings


def configure_logging() -> None:
    """Configure structured logging."""
    
    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]
    
    if settings.LOG_FORMAT == "json":
        # JSON format for production
        renderer = structlog.processors.JSONRenderer()
    else:
        # Console format for development
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LOG_LEVEL)


# Usage in code
import structlog

logger = structlog.get_logger(__name__)

@router.post("/users")
async def create_user(user_data: UserCreate) -> UserResponse:
    logger.info("creating_user", email=user_data.email)
    
    try:
        user = await service.create_user(user_data)
        logger.info("user_created", user_id=user.id)
        return UserResponse.model_validate(user)
    except Exception as e:
        logger.error("user_creation_failed", error=str(e), exc_info=True)
        raise
```

---

## 🎯 ФИНАЛЬНЫЕ ИМПЕРАТИВЫ

### ✅ ВСЕГДА делай:

1. **Lifespan вместо on_event**: Используй `@asynccontextmanager async def lifespan(app)`
2. **Async/await правильно**: async def везде, await только для async библиотек
3. **Dependency Injection**: Используй Depends для всех зависимостей
4. **Service Layer**: Бизнес-логика НЕ в routers, только в service layer
5. **Pydantic schemas**: НИКОГДА не возвращай ORM модели напрямую
6. **Type hints везде**: Для IDE поддержки и автоматической валидации
7. **SQLAlchemy 2.0**: Используй Mapped types и async sessions
8. **expire_on_commit=False**: Критично для async
9. **pool_pre_ping=True**: Критично для production
10. **Environment config**: Secrets только из environment

### ❌ НИКОГДА не делай:

1. **AsyncSession + asyncio.gather**: Для нескольких DB запросов
2. **Sync библиотеки в async**: requests, pymongo, sync SQLAlchemy
3. **Бизнес-логика в routers**: Роутеры только для HTTP layer
4. **ORM модели в response**: Только Pydantic schemas
5. **@app.on_event**: Deprecated, используй lifespan
6. **Hardcoded secrets**: SECRET_KEY только из environment
7. **allow_origins=["*"]**: С credentials в production
8. **Blocking operations**: Без run_in_executor в async code
9. **N+1 queries**: Используй eager loading
10. **tiangolo/uvicorn-gunicorn-fastapi**: Deprecated Docker image

---

## 📚 Дополнительные ресурсы

- **Официальная документация**: https://fastapi.tiangolo.com/
- **Full-Stack Template**: https://github.com/fastapi/full-stack-fastapi-template
- **Community Best Practices**: https://github.com/zhanymkanov/fastapi-best-practices
- **SQLAlchemy 2.0 Docs**: https://docs.sqlalchemy.org/en/20/
- **Pydantic V2 Docs**: https://docs.pydantic.dev/latest/
- **pydantic-settings**: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
