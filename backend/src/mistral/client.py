"""
Клиент для работы с Mistral AI API.

Инкапсулирует взаимодействие с SDK mistralai.
"""

from typing import Any

import structlog
from mistralai import Mistral
from mistralai.models import ChatCompletionResponse as MistralChatResponse

from src.mistral.constants import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from src.mistral.exceptions import (
    MistralAPIError,
    MistralAuthenticationError,
    MistralInvalidRequestError,
    MistralRateLimitError,
)
from src.mistral.schemas import Message, Tool

logger = structlog.get_logger(__name__)


class MistralClient:
    """
    Клиент для взаимодействия с Mistral AI API.

    Обертка над SDK с обработкой ошибок и логированием.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: Mistral | None = None

    def _get_client(self) -> Mistral:
        """Получить или создать клиент Mistral."""
        if self._client is None:
            self._client = Mistral(api_key=self._api_key)
        return self._client

    def _convert_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Конвертировать сообщения в формат API."""
        api_messages = []
        for msg in messages:
            api_msg: dict[str, Any] = {
                "role": msg.role,
                "content": msg.content or "",
            }
            if msg.tool_call_id:
                api_msg["tool_call_id"] = msg.tool_call_id
            if msg.name:
                api_msg["name"] = msg.name
            if msg.tool_calls:
                api_msg["tool_calls"] = [
                    tc.model_dump() for tc in msg.tool_calls
                ]
            api_messages.append(api_msg)
        return api_messages

    def _convert_tools(self, tools: list[Tool] | None) -> list[dict[str, Any]] | None:
        """Конвертировать tools в формат API."""
        if not tools:
            return None
        return [tool.model_dump(exclude_none=True) for tool in tools]

    async def chat_complete(
        self,
        messages: list[Message],
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = 1.0,
        random_seed: int | None = None,
        safe_prompt: bool = False,
        tools: list[Tool] | None = None,
        tool_choice: str | None = None,
    ) -> MistralChatResponse:
        """
        Выполнить chat completion запрос.

        Args:
            messages: Список сообщений
            model: ID модели
            max_tokens: Максимум токенов в ответе
            temperature: Температура генерации
            top_p: Top-p sampling
            random_seed: Seed для детерминированности
            safe_prompt: Добавить safety prompt
            tools: Список инструментов (для agents)
            tool_choice: Стратегия выбора инструментов

        Returns:
            Ответ от Mistral API

        Raises:
            MistralAPIError: При ошибках API
            MistralAuthenticationError: При ошибках аутентификации
            MistralRateLimitError: При превышении лимитов
            MistralInvalidRequestError: При некорректном запросе
        """
        client = self._get_client()

        api_messages = self._convert_messages(messages)
        api_tools = self._convert_tools(tools)

        try:
            logger.debug(
                "mistral_api_request",
                model=model,
                messages_count=len(messages),
                tools_count=len(tools) if tools else 0,
            )

            response = client.chat.complete(
                model=model,
                messages=api_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                random_seed=random_seed,
                safe_prompt=safe_prompt,
                tools=api_tools,
                tool_choice=tool_choice,
                stream=False,
            )

            if response is None:
                raise MistralAPIError("Empty response from Mistral API")

            logger.debug(
                "mistral_api_response",
                model=response.model,
                finish_reason=response.choices[0].finish_reason if response.choices else None,
                total_tokens=response.usage.total_tokens if response.usage else None,
            )

            return response

        except MistralAPIError:
            raise
        except Exception as e:
            error_str = str(e).lower()

            if "401" in error_str or "unauthorized" in error_str or "authentication" in error_str:
                logger.error("mistral_auth_error", error=str(e))
                raise MistralAuthenticationError("Invalid Mistral API key")

            if "429" in error_str or "rate limit" in error_str:
                logger.warning("mistral_rate_limit", error=str(e))
                raise MistralRateLimitError("Mistral API rate limit exceeded")

            if "400" in error_str or "invalid" in error_str:
                logger.error("mistral_invalid_request", error=str(e))
                raise MistralInvalidRequestError(f"Invalid request: {e}")

            logger.error("mistral_api_error", error=str(e), exc_info=True)
            raise MistralAPIError(f"Mistral API error: {e}")

    def close(self) -> None:
        """Закрыть клиент."""
        self._client = None
