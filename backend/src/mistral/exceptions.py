"""
Исключения домена Mistral.

Специфичные для Mistral AI ошибки.
"""

from src.shared.exceptions import DomainError


class MistralError(DomainError):
    """Базовое исключение для ошибок Mistral."""

    message = "Mistral API error"
    error_code = "mistral_error"
    status_code = 500


class MistralAPIError(MistralError):
    """Ошибка при вызове Mistral API."""

    message = "Failed to call Mistral API"
    error_code = "mistral_api_error"
    status_code = 502


class MistralRateLimitError(MistralError):
    """Превышен лимит запросов к Mistral API."""

    message = "Mistral API rate limit exceeded"
    error_code = "mistral_rate_limit"
    status_code = 429


class MistralInvalidRequestError(MistralError):
    """Некорректный запрос к Mistral API."""

    message = "Invalid request to Mistral API"
    error_code = "mistral_invalid_request"
    status_code = 400


class MistralAuthenticationError(MistralError):
    """Ошибка аутентификации Mistral API."""

    message = "Mistral API authentication failed"
    error_code = "mistral_auth_error"
    status_code = 401


class ToolExecutionError(MistralError):
    """Ошибка выполнения инструмента."""

    message = "Tool execution failed"
    error_code = "tool_execution_error"
    status_code = 500


class ToolNotFoundError(MistralError):
    """Инструмент не найден."""

    message = "Tool not found"
    error_code = "tool_not_found"
    status_code = 404
