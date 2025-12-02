"""
Зависимости домена Mistral.

FastAPI Depends для dependency injection.
"""

from functools import lru_cache

from fastapi import Depends

from src.config import get_settings
from src.mistral.client import MistralClient
from src.mistral.service import MistralService
from src.mistral.tools import ToolRegistry, create_default_registry


# Кэшируем клиент на уровне приложения
_mistral_client: MistralClient | None = None


def get_mistral_client() -> MistralClient:
    """Получить MistralClient с API ключом из настроек."""
    global _mistral_client
    if _mistral_client is None:
        settings = get_settings()
        _mistral_client = MistralClient(api_key=settings.MISTRAL_API_KEY)
    return _mistral_client


@lru_cache
def get_tool_registry() -> ToolRegistry:
    """Получить реестр инструментов."""
    return create_default_registry()


def get_mistral_service(
    client: MistralClient = Depends(get_mistral_client),
    tool_registry: ToolRegistry = Depends(get_tool_registry),
) -> MistralService:
    """Получить MistralService с клиентом и реестром инструментов."""
    return MistralService(client=client, tool_registry=tool_registry)
