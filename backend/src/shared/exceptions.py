"""
Базовые доменные исключения.

Все специфичные для домена исключения должны наследоваться от DomainError.
Это позволяет централизованно обрабатывать исключения в main.py.
"""

from typing import Any


class DomainError(Exception):
    """
    Базовое исключение для всех доменных ошибок.

    Атрибуты:
        message: Человекочитаемое сообщение об ошибке
        error_code: Машиночитаемый код ошибки (например, "user_not_found")
        status_code: HTTP статус-код для этой ошибки
        details: Дополнительные детали ошибки (опционально)
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
    """Ресурс не найден."""

    message = "Resource not found"
    error_code = "not_found"
    status_code = 404


class AlreadyExistsError(DomainError):
    """Ресурс уже существует."""

    message = "Resource already exists"
    error_code = "already_exists"
    status_code = 409


class ValidationError(DomainError):
    """Бизнес-валидация не пройдена."""

    message = "Validation failed"
    error_code = "validation_error"
    status_code = 422


class AuthenticationError(DomainError):
    """Аутентификация не пройдена."""

    message = "Authentication failed"
    error_code = "authentication_error"
    status_code = 401


class AuthorizationError(DomainError):
    """Авторизация не пройдена."""

    message = "Insufficient permissions"
    error_code = "authorization_error"
    status_code = 403
