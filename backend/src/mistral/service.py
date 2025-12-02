"""
Сервис домена Mistral.

Бизнес-логика для chat completion и agent сценариев.
"""

import json

import structlog

from src.mistral.client import MistralClient
from src.mistral.constants import MAX_TOOL_CALLS_PER_RESPONSE, MessageRole
from src.mistral.exceptions import ToolExecutionError
from src.mistral.schemas import (
    AgentRequest,
    AgentResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    FunctionCall,
    Message,
    ToolCall,
    ToolCallResult,
    UsageInfo,
)
from src.mistral.tools import ToolRegistry

logger = structlog.get_logger(__name__)


class MistralService:
    """
    Сервис для работы с Mistral AI.

    Инкапсулирует бизнес-логику:
    - Chat completion (простой вопрос-ответ)
    - Agent с инструментами (циклический вызов tools)
    """

    def __init__(
        self,
        client: MistralClient,
        tool_registry: ToolRegistry,
    ) -> None:
        self._client = client
        self._tool_registry = tool_registry

    async def chat(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """
        Выполнить простой chat completion.

        Args:
            request: Запрос с сообщениями и параметрами

        Returns:
            Ответ модели
        """
        logger.info(
            "chat_completion_start",
            model=request.model,
            messages_count=len(request.messages),
        )

        response = await self._client.chat_complete(
            messages=request.messages,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            random_seed=request.random_seed,
            safe_prompt=request.safe_prompt,
        )

        choice = response.choices[0]
        content = choice.message.content or ""

        logger.info(
            "chat_completion_done",
            model=response.model,
            finish_reason=choice.finish_reason,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )

        return ChatCompletionResponse(
            id=response.id,
            model=response.model,
            content=content,
            finish_reason=str(choice.finish_reason),
            usage=UsageInfo(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            ),
        )

    async def agent_chat(self, request: AgentRequest) -> AgentResponse:
        """
        Выполнить agent сценарий с инструментами.

        Агент может:
        1. Ответить напрямую
        2. Вызвать один или несколько инструментов
        3. Повторить шаг 2 до max_iterations раз

        Args:
            request: Запрос с сообщениями, tools и параметрами

        Returns:
            Финальный ответ агента с историей tool calls
        """
        logger.info(
            "agent_chat_start",
            model=request.model,
            messages_count=len(request.messages),
            tools_count=len(request.tools),
            max_iterations=request.max_iterations,
        )

        messages = list(request.messages)

        tools = request.tools or self._tool_registry.get_all_schemas()

        tool_calls_made: list[ToolCallResult] = []
        iterations = 0
        total_usage = UsageInfo(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        while iterations < request.max_iterations:
            iterations += 1

            logger.debug(
                "agent_iteration",
                iteration=iterations,
                messages_count=len(messages),
            )

            response = await self._client.chat_complete(
                messages=messages,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                tools=tools,
                tool_choice=request.tool_choice.type,
            )

            if response.usage:
                total_usage.prompt_tokens += response.usage.prompt_tokens
                total_usage.completion_tokens += response.usage.completion_tokens
                total_usage.total_tokens += response.usage.total_tokens

            choice = response.choices[0]
            assistant_message = choice.message

            if not assistant_message.tool_calls:
                logger.info(
                    "agent_chat_done",
                    iterations=iterations,
                    tool_calls_count=len(tool_calls_made),
                    finish_reason=str(choice.finish_reason),
                )

                return AgentResponse(
                    id=response.id,
                    model=response.model,
                    content=assistant_message.content or "",
                    finish_reason=str(choice.finish_reason),
                    usage=total_usage,
                    tool_calls_made=tool_calls_made,
                    iterations=iterations,
                )

            # Конвертируем tool_calls из ответа API в наши ToolCall объекты
            api_tool_calls = [
                ToolCall(
                    id=tc.id,
                    type="function",
                    function=FunctionCall(
                        name=tc.function.name,
                        arguments=tc.function.arguments,
                    ),
                )
                for tc in assistant_message.tool_calls[:MAX_TOOL_CALLS_PER_RESPONSE]
            ]

            # Добавляем assistant message С tool_calls
            messages.append(
                Message(
                    role=MessageRole.ASSISTANT,
                    content=assistant_message.content,
                    tool_calls=api_tool_calls,
                )
            )

            for tool_call in assistant_message.tool_calls[:MAX_TOOL_CALLS_PER_RESPONSE]:
                func = tool_call.function

                logger.debug(
                    "executing_tool",
                    tool_name=func.name,
                    tool_call_id=tool_call.id,
                )

                try:
                    arguments = json.loads(func.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                result = ToolCallResult(
                    tool_call_id=tool_call.id,
                    name=func.name,
                    arguments=arguments,
                )

                try:
                    execution_result = await self._tool_registry.execute(
                        name=func.name,
                        arguments=func.arguments,
                    )
                    result.result = execution_result
                except ToolExecutionError as e:
                    result.error = str(e)
                    execution_result = f"Error: {e}"
                except Exception as e:
                    result.error = str(e)
                    execution_result = f"Error: {e}"

                tool_calls_made.append(result)

                messages.append(
                    Message(
                        role=MessageRole.TOOL,
                        content=execution_result,
                        tool_call_id=tool_call.id,
                        name=func.name,
                    )
                )

        logger.warning(
            "agent_max_iterations_reached",
            iterations=iterations,
            tool_calls_count=len(tool_calls_made),
        )

        return AgentResponse(
            id="max_iterations_reached",
            model=request.model,
            content="Maximum iterations reached without final answer",
            finish_reason="max_iterations",
            usage=total_usage,
            tool_calls_made=tool_calls_made,
            iterations=iterations,
        )
