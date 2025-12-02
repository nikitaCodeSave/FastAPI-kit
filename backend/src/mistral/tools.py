"""
Инфраструктура для определения и выполнения tools.

Базовые классы и примеры инструментов для агентов.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from src.mistral.exceptions import ToolExecutionError, ToolNotFoundError
from src.mistral.schemas import (
    FunctionDefinition,
    FunctionParameter,
    FunctionParameters,
    Tool,
)


class BaseTool(ABC):
    """
    Базовый класс для определения инструмента.

    Каждый инструмент должен определить:
    - name: уникальное имя
    - description: описание для модели
    - parameters: JSON Schema параметров
    - execute(): логика выполнения
    """

    name: str
    description: str

    @property
    @abstractmethod
    def parameters(self) -> FunctionParameters:
        """JSON Schema параметров функции."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """
        Выполнить инструмент с переданными аргументами.

        Returns:
            Строковый результат для передачи модели
        """
        pass

    def to_tool_schema(self) -> Tool:
        """Конвертировать в схему Tool для Mistral API."""
        return Tool(
            type="function",
            function=FunctionDefinition(
                name=self.name,
                description=self.description,
                parameters=self.parameters,
            ),
        )


class ToolRegistry:
    """
    Реестр доступных инструментов.

    Позволяет регистрировать и находить инструменты по имени.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Зарегистрировать инструмент."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        """Получить инструмент по имени."""
        tool = self._tools.get(name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{name}' not found")
        return tool

    def get_all_schemas(self) -> list[Tool]:
        """Получить схемы всех зарегистрированных инструментов."""
        return [tool.to_tool_schema() for tool in self._tools.values()]

    async def execute(self, name: str, arguments: str) -> str:
        """
        Выполнить инструмент по имени.

        Args:
            name: Имя инструмента
            arguments: JSON строка с аргументами

        Returns:
            Строковый результат выполнения
        """
        tool = self.get(name)
        try:
            kwargs = json.loads(arguments)
            return await tool.execute(**kwargs)
        except json.JSONDecodeError as e:
            raise ToolExecutionError(f"Invalid arguments JSON: {e}")
        except ToolNotFoundError:
            raise
        except Exception as e:
            raise ToolExecutionError(f"Tool '{name}' execution failed: {e}")


# ─────────────────────────────────────────────────────────────
# Примеры инструментов
# ─────────────────────────────────────────────────────────────


class GetCurrentTimeTool(BaseTool):
    """Инструмент для получения текущего времени."""

    name = "get_current_time"
    description = "Get the current date and time in ISO format"

    @property
    def parameters(self) -> FunctionParameters:
        return FunctionParameters(
            type="object",
            properties={
                "timezone": FunctionParameter(
                    type="string",
                    description="Timezone name (e.g., 'UTC', 'Europe/Moscow')",
                ),
            },
            required=[],
        )

    async def execute(self, timezone: str = "UTC") -> str:
        try:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            return now.isoformat()
        except Exception:
            return datetime.now(ZoneInfo("UTC")).isoformat()


class CalculatorTool(BaseTool):
    """Простой калькулятор."""

    name = "calculator"
    description = "Perform basic arithmetic operations (add, subtract, multiply, divide)"

    @property
    def parameters(self) -> FunctionParameters:
        return FunctionParameters(
            type="object",
            properties={
                "operation": FunctionParameter(
                    type="string",
                    description="The operation to perform",
                    enum=["add", "subtract", "multiply", "divide"],
                ),
                "a": FunctionParameter(
                    type="number",
                    description="First operand",
                ),
                "b": FunctionParameter(
                    type="number",
                    description="Second operand",
                ),
            },
            required=["operation", "a", "b"],
        )

    async def execute(self, operation: str, a: float, b: float) -> str:
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else "Error: division by zero",
        }

        op_func = operations.get(operation)
        if not op_func:
            return f"Error: unknown operation '{operation}'"

        result = op_func(a, b)
        return str(result)


def create_default_registry() -> ToolRegistry:
    """Создать реестр с базовыми инструментами."""
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())
    registry.register(CalculatorTool())
    return registry
