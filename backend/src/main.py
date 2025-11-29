"""
Точка входа FastAPI приложения.

Структура модуля:
─────────────────────────────────────
- lifespan()           — управление жизненным циклом приложения
- create_application() — фабрика для создания экземпляра FastAPI
- app                  — готовый экземпляр приложения

Запуск:
    uvicorn ./backend.src.main:app --reload
    fastapi run ./backend/src/main.py --reload
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.config import settings
from src.database import sessionmanager
from src.logging_config import setup_logging
from src.shared.exceptions import DomainError

# Import routers
from src.example.router import router as example_router

# Инициализация логирования должна происходить до создания логгера
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Управление жизненным циклом приложения.

    Lifespan context manager заменяет устаревшие on_startup/on_shutdown события.
    Код до yield выполняется при старте, после yield — при остановке.

    Типичное использование:
        - Инициализация пула соединений к БД
        - Подключение к Redis/RabbitMQ
        - Загрузка ML моделей в память
        - Graceful shutdown ресурсов
    """
    # Startup: выполняется один раз при запуске приложения
    logger.info(
        "app_starting",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
    )

    # Initialize database
    sessionmanager.init(settings.DATABASE_URL)
    await sessionmanager.create_tables()
    logger.info("database_initialized", url=settings.DATABASE_URL.split("@")[-1])

    yield

    # Shutdown: выполняется при остановке (SIGTERM, Ctrl+C)
    if sessionmanager._engine is not None:
        await sessionmanager.close()
        logger.info("database_closed")

    logger.info("app_stopped")


def create_application() -> FastAPI:
    """
    Фабрика приложения (Application Factory Pattern).

    Паттерн позволяет:
        - Создавать несколько экземпляров с разными настройками (для тестов)
        - Избежать циклических импортов
        - Отложить инициализацию до момента вызова
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
        # Swagger UI и ReDoc отключены в production из соображений безопасности:
        # - Скрывает структуру API от потенциальных атакующих
        # - Уменьшает поверхность атаки
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    )

    # ─────────────────────────────────────────────────────────────
    # EXCEPTION HANDLERS
    # ─────────────────────────────────────────────────────────────

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        """
        Обработчик доменных исключений.

        Все исключения наследующиеся от DomainError автоматически
        конвертируются в JSON ответ с правильным статус-кодом.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """
        Глобальный обработчик необработанных исключений.

        Срабатывает когда исключение не было поймано ни в endpoint,
        ни специфичным handler'ом. Это последняя линия защиты.

        Что делает:
        - Логирует ошибку с полным контекстом (путь, метод, traceback)
        - Возвращает клиенту безопасный JSON без деталей реализации
        - Гарантирует что клиент получит корректный ответ, а не HTML или разрыв соединения
        """
        logger.error(
            "unhandled_exception",
            error=str(exc),
            path=request.url.path,
            method=request.method,
            exc_info=True,  # Полный traceback в логи
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "Произошла непредвиденная ошибка",
            },
        )

    # ─────────────────────────────────────────────────────────────
    # HEALTH CHECK
    # ─────────────────────────────────────────────────────────────
    # Используется для:
    # - Kubernetes liveness/readiness probes
    # - Load balancer health checks
    # - Мониторинга (Prometheus, Datadog и т.д.)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict:
        """Проверка работоспособности сервиса."""
        return {
            "status": "healthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    # ─────────────────────────────────────────────────────────────
    # ROUTERS
    # ─────────────────────────────────────────────────────────────

    app.include_router(example_router, prefix="/api/v1/examples", tags=["Examples"])

    return app


# Экземпляр приложения создаётся при импорте модуля.
# uvicorn ожидает именно переменную `app` для запуска.
app = create_application()
