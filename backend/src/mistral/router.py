"""
Роутер домена Mistral.

HTTP endpoints для chat completion и agents.
"""

from fastapi import APIRouter, Depends, status

from src.mistral.dependencies import get_mistral_service
from src.mistral.schemas import (
    AgentRequest,
    AgentResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
)
from src.mistral.service import MistralService

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatCompletionResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat Completion",
    description="Выполнить простой вопрос-ответ с моделью Mistral",
)
async def chat_completion(
    request: ChatCompletionRequest,
    service: MistralService = Depends(get_mistral_service),
) -> ChatCompletionResponse:
    """
    Chat Completion - базовый вопрос-ответ.

    Отправляет список сообщений модели и получает ответ.
    """
    return await service.chat(request)


@router.post(
    "/agent",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Agent Chat with Tools",
    description="Выполнить агентский сценарий с вызовом инструментов",
)
async def agent_chat(
    request: AgentRequest,
    service: MistralService = Depends(get_mistral_service),
) -> AgentResponse:
    """
    Agent Chat - сценарий с инструментами.

    Агент может:
    - Ответить напрямую на вопрос
    - Вызвать один или несколько инструментов
    - Использовать результаты инструментов для формирования ответа
    """
    return await service.agent_chat(request)


@router.get(
    "/tools",
    summary="List Available Tools",
    description="Получить список доступных инструментов для агента",
)
async def list_tools(
    service: MistralService = Depends(get_mistral_service),
) -> dict:
    """Получить список доступных инструментов."""
    tools = service._tool_registry.get_all_schemas()
    return {
        "tools": [tool.model_dump() for tool in tools],
        "count": len(tools),
    }
