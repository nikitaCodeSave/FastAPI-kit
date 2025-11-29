"""
Shared module.

Contains common code used across all domains:
- Base exceptions
- Common schemas (pagination, etc.)
"""

from src.shared.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    AuthorizationError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from src.shared.schemas import PaginatedResponse, PaginationParams

__all__ = [
    "DomainError",
    "NotFoundError",
    "AlreadyExistsError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "PaginationParams",
    "PaginatedResponse",
]
