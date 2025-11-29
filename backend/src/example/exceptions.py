"""
Исключения домена Example.

Все специфичные для домена исключения, которые может выбрасывать ExampleService.
"""

from src.shared.exceptions import AlreadyExistsError, NotFoundError


class ExampleNotFoundError(NotFoundError):
    """Example не найден по ID."""

    message = "Example not found"
    error_code = "example_not_found"


class ExampleAlreadyExistsError(AlreadyExistsError):
    """Example с таким заголовком уже существует."""

    message = "Example with this title already exists"
    error_code = "example_already_exists"
