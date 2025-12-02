"""
Pydantic схемы домена Mistral.

Модели для chat completion и agents/tools.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.mistral.constants import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    MAX_CONTENT_LENGTH,
    MAX_MESSAGES,
    MAX_TOOLS,
    MessageRole,
    MistralModel,
)


# ─────────────────────────────────────────────────────────────
# Общие типы
# ─────────────────────────────────────────────────────────────


class FunctionCall(BaseModel):
    """Детали вызова функции."""

    name: str
    arguments: str


class ToolCall(BaseModel):
    """Вызов инструмента от модели."""

    id: str
    type: Literal["function"] = "function"
    function: FunctionCall


class Message(BaseModel):
    """Сообщение в чате."""

    role: MessageRole = Field(
        description="Роль отправителя сообщения (ОБЯЗАТЕЛЬНО)"
    )
    content: str | None = Field(
        default=None,
        max_length=MAX_CONTENT_LENGTH,
        description="Текст сообщения (None для assistant с tool_calls)",
    )
    tool_call_id: str | None = Field(
        default=None,
        description="ID вызова инструмента (только для role=tool)",
    )
    name: str | None = Field(
        default=None,
        description="Имя функции (только для role=tool)",
    )
    tool_calls: list[ToolCall] | None = Field(
        default=None,
        description="Вызовы инструментов (только для role=assistant)",
    )


# ─────────────────────────────────────────────────────────────
# Tool/Function Definitions
# ─────────────────────────────────────────────────────────────


class FunctionParameter(BaseModel):
    """Параметр функции для JSON Schema."""

    model_config = ConfigDict(exclude_none=True)

    type: str
    description: str | None = None
    enum: list[str] | None = None


class FunctionParameters(BaseModel):
    """Параметры функции в формате JSON Schema."""

    type: Literal["object"] = "object"
    properties: dict[str, FunctionParameter]
    required: list[str] = Field(default_factory=list)


class FunctionDefinition(BaseModel):
    """Определение функции для tool."""

    name: str = Field(min_length=1, max_length=64)
    description: str = Field(max_length=1024)
    parameters: FunctionParameters


class Tool(BaseModel):
    """Инструмент для использования моделью."""

    type: Literal["function"] = "function"
    function: FunctionDefinition


# ─────────────────────────────────────────────────────────────
# Usage Info
# ─────────────────────────────────────────────────────────────


class UsageInfo(BaseModel):
    """Информация об использовании токенов."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# ─────────────────────────────────────────────────────────────
# Chat Completion
# ─────────────────────────────────────────────────────────────


class ChatCompletionRequest(BaseModel):
    """Запрос на chat completion."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "user", "content": "Привет! Как дела?"}
                ],
            }
        }
    )

    messages: list[Message] = Field(
        min_length=1,
        max_length=MAX_MESSAGES,
        description="Список сообщений чата (ОБЯЗАТЕЛЬНО, минимум 1)",
    )
    model: MistralModel = Field(
        default=DEFAULT_MODEL,
        description="Модель Mistral (по умолчанию: mistral-small-latest)",
    )
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        ge=1,
        le=32000,
        description="Максимум токенов в ответе (по умолчанию: 1024)",
    )
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=0.0,
        le=1.0,
        description="Температура генерации 0.0-1.0 (по умолчанию: 0.7)",
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Top-p sampling (по умолчанию: 1.0)",
    )
    random_seed: int | None = Field(
        default=None,
        description="Seed для воспроизводимости (опционально)",
    )
    safe_prompt: bool = Field(
        default=False,
        description="Добавить safety prompt (по умолчанию: false)",
    )


class ChatCompletionResponse(BaseModel):
    """Ответ chat completion."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    model: str
    content: str
    finish_reason: str
    usage: UsageInfo


# ─────────────────────────────────────────────────────────────
# Agent with Tools
# ─────────────────────────────────────────────────────────────


class ToolChoice(BaseModel):
    """Выбор стратегии использования инструментов."""

    type: Literal["auto", "any", "none"] = "auto"


class AgentRequest(BaseModel):
    """Запрос к агенту с инструментами."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "messages": [
                    {"role": "user", "content": "Сколько будет 25 * 17?"}
                ],
            }
        }
    )

    messages: list[Message] = Field(
        min_length=1,
        max_length=MAX_MESSAGES,
        description="Список сообщений (ОБЯЗАТЕЛЬНО, минимум 1)",
    )
    model: MistralModel = Field(
        default=DEFAULT_MODEL,
        description="Модель Mistral (по умолчанию: mistral-small-latest)",
    )
    tools: list[Tool] = Field(
        default_factory=list,
        max_length=MAX_TOOLS,
        description="Инструменты для агента (по умолчанию: встроенные calculator, get_current_time)",
    )
    tool_choice: ToolChoice = Field(
        default_factory=ToolChoice,
        description="Стратегия выбора инструментов: auto/any/none (по умолчанию: auto)",
    )
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        ge=1,
        le=32000,
        description="Максимум токенов (по умолчанию: 1024)",
    )
    temperature: float = Field(
        default=DEFAULT_TEMPERATURE,
        ge=0.0,
        le=1.0,
        description="Температура генерации (по умолчанию: 0.7)",
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Максимум итераций tool calls (по умолчанию: 10)",
    )


class ToolCallResult(BaseModel):
    """Результат выполнения одного tool call."""

    tool_call_id: str
    name: str
    arguments: dict[str, Any]
    result: str | None = None
    error: str | None = None


class AgentResponse(BaseModel):
    """Ответ агента."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    model: str
    content: str
    finish_reason: str
    usage: UsageInfo
    tool_calls_made: list[ToolCallResult] = Field(default_factory=list)
    iterations: int = 0
