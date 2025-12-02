"""
Константы домена Mistral.

Доступные модели, лимиты и настройки по умолчанию.
"""

from enum import StrEnum


class MistralModel(StrEnum):
    """Доступные модели Mistral AI."""

    MISTRAL_SMALL = "mistral-small-latest"
    MISTRAL_MEDIUM = "mistral-medium-latest"
    MISTRAL_LARGE = "mistral-large-latest"
    CODESTRAL = "codestral-latest"
    OPEN_MISTRAL_7B = "open-mistral-7b"
    OPEN_MIXTRAL_8X7B = "open-mixtral-8x7b"


class MessageRole(StrEnum):
    """Роли сообщений в чате."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


# Значения по умолчанию
DEFAULT_MODEL = MistralModel.MISTRAL_SMALL
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TEMPERATURE = 0.7

# Лимиты
MAX_MESSAGES = 1000
MAX_CONTENT_LENGTH = 32000
MAX_TOOLS = 64
MAX_TOOL_CALLS_PER_RESPONSE = 10
