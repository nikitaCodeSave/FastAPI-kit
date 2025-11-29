# logging_config.py
"""
Конфигурация структурированного логирования (structlog).

Development: цветной консольный вывод, локальное время
Production: JSON формат, UTC время (для ELK, Grafana Loki и т.д.)
"""

import structlog
from src.config import settings


def setup_logging() -> None:
    """Инициализировать structlog."""
    if settings.ENVIRONMENT == "development":
        processors = [
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        processors = [
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(processors=processors)
