# Mistral AI Domain

Домен для интеграции с [Mistral AI API](https://docs.mistral.ai/).

## Содержание

- [Быстрый старт](#быстрый-старт)
- [API Endpoints](#api-endpoints)
- [Function Calling (Tools)](#function-calling-tools)
- [Создание своих инструментов](#создание-своих-инструментов)
- [Архитектура](#архитектура)
- [Ссылки на документацию](#ссылки-на-документацию)

---

## Быстрый старт

### 1. Настройка API ключа 
Получить ключ после регистрации - https://admin.mistral.ai/organization/api-keys 

Добавьте в `.env`:

```env
MISTRAL_API_KEY=your_api_key_here
```

### 2. Запуск сервера

```bash
cd backend
source ../.venv/bin/activate
uvicorn src.main:app --reload
```

### 3. Тестовые запросы

**Chat Completion (простой вопрос-ответ):**

```bash
curl -X POST 'http://localhost:8000/api/v1/mistral/chat' \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Привет! Как дела?"}]
  }'
```

**Agent с инструментами:**

```bash
curl -X POST 'http://localhost:8000/api/v1/mistral/agent' \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Сколько будет 25 * 17?"}]
  }'
```

---

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/v1/mistral/chat` | Простой вопрос-ответ |
| POST | `/api/v1/mistral/agent` | Агент с инструментами |
| GET | `/api/v1/mistral/tools` | Список доступных инструментов |

### POST `/api/v1/mistral/chat`

Базовый Chat Completion без инструментов.

**Обязательные поля:**
- `messages` — список сообщений (минимум 1)

**Опциональные поля (с дефолтами):**
- `model` — модель (default: `mistral-small-latest`)
- `max_tokens` — максимум токенов (default: `1024`)
- `temperature` — температура 0.0-1.0 (default: `0.7`)

**Пример запроса:**

```json
{
  "messages": [
    {"role": "system", "content": "Ты полезный ассистент"},
    {"role": "user", "content": "Расскажи о Python"}
  ],
  "model": "mistral-small-latest",
  "temperature": 0.5
}
```

### POST `/api/v1/mistral/agent`

Агент с Function Calling — может использовать инструменты для ответа.

**Обязательные поля:**
- `messages` — список сообщений

**Опциональные поля:**
- `tools` — кастомные инструменты (если пусто — используются встроенные)
- `tool_choice` — стратегия выбора инструментов (`auto`/`any`/`none`)
- `max_iterations` — максимум циклов tool calls (default: `10`)

**Пример ответа:**

```json
{
  "id": "abc123",
  "model": "mistral-small-latest",
  "content": "Результат: 25 × 17 = 425",
  "finish_reason": "stop",
  "usage": {
    "prompt_tokens": 503,
    "completion_tokens": 47,
    "total_tokens": 550
  },
  "tool_calls_made": [
    {
      "tool_call_id": "xyz789",
      "name": "calculator",
      "arguments": {"operation": "multiply", "a": 25, "b": 17},
      "result": "425",
      "error": null
    }
  ],
  "iterations": 2
}
```

---

## Function Calling (Tools)

### Что это?

**Function Calling** (он же **Tools**) — механизм, позволяющий модели вызывать внешние функции для получения данных или выполнения действий.

> **Официальная документация:** [docs.mistral.ai/capabilities/function_calling](https://docs.mistral.ai/capabilities/function_calling/)

### Как это работает?

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Пользователь отправляет запрос + список доступных tools    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. Модель анализирует запрос и решает:                        │
│     - Ответить напрямую (если tools не нужны)                  │
│     - Вызвать один или несколько tools                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. Если модель выбрала tool:                                  │
│     - Возвращает имя функции + аргументы (JSON)                │
│     - НЕ выполняет функцию сама!                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. Сервер (наш код) выполняет функцию локально                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. Результат передается обратно модели                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  6. Модель формирует финальный ответ на основе результатов     │
└─────────────────────────────────────────────────────────────────┘
```

### Поддерживаемые модели

Function Calling доступен для:
- **Mistral Large** / Medium / Small
- **Codestral**
- **Ministral** 8B / 3B
- **Pixtral** 12B / Large
- **Mistral Nemo**

### Параметр `tool_choice`

| Значение | Поведение |
|----------|-----------|
| `auto` | Модель сама решает, использовать ли tools (по умолчанию) |
| `any` | Модель **обязана** использовать хотя бы один tool |
| `none` | Модель **не будет** использовать tools |

---

## Создание своих инструментов

### Структура Tool (JSON Schema)

Каждый инструмент описывается по стандарту [JSON Schema](https://json-schema.org/):

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "Получить текущую погоду в указанном городе",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "Название города (например, 'Москва')"
        },
        "units": {
          "type": "string",
          "description": "Единицы измерения температуры",
          "enum": ["celsius", "fahrenheit"]
        }
      },
      "required": ["city"]
    }
  }
}
```

### Обязательные поля

| Поле | Описание |
|------|----------|
| `type` | Всегда `"function"` |
| `function.name` | Уникальное имя функции (1-64 символа) |
| `function.description` | Описание для модели (до 1024 символов) |
| `function.parameters` | JSON Schema параметров |
| `parameters.type` | Всегда `"object"` |
| `parameters.properties` | Словарь параметров |
| `parameters.required` | Массив обязательных параметров |

### Типы параметров

| Тип | Пример | Описание |
|-----|--------|----------|
| `string` | `"hello"` | Строка |
| `number` | `42.5` | Число (целое или дробное) |
| `integer` | `42` | Целое число |
| `boolean` | `true` | Логическое значение |
| `array` | `[1, 2, 3]` | Массив |
| `object` | `{"key": "value"}` | Объект |

### Создание инструмента в коде

**Шаг 1.** Создайте класс, наследующий `BaseTool`:

```python
# backend/src/mistral/tools.py

from src.mistral.tools import BaseTool
from src.mistral.schemas import FunctionParameter, FunctionParameters


class GetWeatherTool(BaseTool):
    """Инструмент для получения погоды."""

    name = "get_weather"
    description = "Get current weather in a city"

    @property
    def parameters(self) -> FunctionParameters:
        return FunctionParameters(
            type="object",
            properties={
                "city": FunctionParameter(
                    type="string",
                    description="City name (e.g., 'Moscow')",
                ),
                "units": FunctionParameter(
                    type="string",
                    description="Temperature units",
                    enum=["celsius", "fahrenheit"],
                ),
            },
            required=["city"],
        )

    async def execute(self, city: str, units: str = "celsius") -> str:
        """
        Выполнить запрос погоды.

        Args:
            city: Название города
            units: Единицы измерения

        Returns:
            JSON строка с результатом
        """
        # Здесь ваша логика (API вызов, БД запрос и т.д.)
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.weather.com/{city}",
                params={"units": units}
            )
            return response.text
```

**Шаг 2.** Зарегистрируйте инструмент:

```python
# backend/src/mistral/tools.py

def create_default_registry() -> ToolRegistry:
    """Создать реестр с инструментами."""
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())
    registry.register(CalculatorTool())
    registry.register(GetWeatherTool())  # Добавьте сюда
    return registry
```

**Шаг 3.** Перезапустите сервер — инструмент доступен!

### Встроенные инструменты

| Инструмент | Описание | Параметры |
|------------|----------|-----------|
| `calculator` | Арифметические операции | `operation`, `a`, `b` |
| `get_current_time` | Текущее время | `timezone` (опционально) |

**Пример вызова calculator:**

```json
{
  "name": "calculator",
  "arguments": {
    "operation": "multiply",
    "a": 25,
    "b": 17
  }
}
```

Доступные операции: `add`, `subtract`, `multiply`, `divide`

---

## Архитектура

### Структура файлов

```
backend/src/mistral/
├── __init__.py          # Экспорт роутера
├── constants.py         # Модели, лимиты, enum'ы
├── exceptions.py        # Доменные исключения
├── schemas.py           # Pydantic модели (Message, Tool, Request/Response)
├── tools.py             # BaseTool, ToolRegistry, встроенные инструменты
├── client.py            # MistralClient (обёртка над SDK)
├── service.py           # Бизнес-логика (chat, agent_chat)
├── dependencies.py      # FastAPI Depends (DI)
├── router.py            # HTTP endpoints
└── README.md            # Эта документация
```

### Слои архитектуры

```
┌─────────────────────────────────────────────────────────────┐
│                    router.py (Presentation)                  │
│                    HTTP endpoints, валидация                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    service.py (Business Logic)              │
│                    Логика chat, agent, tool execution       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    client.py (Infrastructure)               │
│                    Взаимодействие с Mistral API             │
└─────────────────────────────────────────────────────────────┘
```

### Цикл Agent с Tools

```python
# service.py — упрощённая логика

while iterations < max_iterations:
    # 1. Отправить сообщения в API
    response = await client.chat_complete(messages, tools=tools)

    # 2. Если нет tool_calls — вернуть финальный ответ
    if not response.tool_calls:
        return response.content

    # 3. Добавить assistant message с tool_calls
    messages.append(Message(role="assistant", tool_calls=...))

    # 4. Выполнить каждый tool и добавить результат
    for tool_call in response.tool_calls:
        result = await tool_registry.execute(tool_call.name, tool_call.arguments)
        messages.append(Message(role="tool", content=result, tool_call_id=...))

    # 5. Повторить цикл
    iterations += 1
```

---

## Best Practices

### 1. Описания функций

**Плохо:**
```python
description = "weather"
```

**Хорошо:**
```python
description = "Get current weather conditions including temperature, humidity, and wind speed for a specified city"
```

### 2. Описания параметров

**Плохо:**
```python
"city": FunctionParameter(type="string")
```

**Хорошо:**
```python
"city": FunctionParameter(
    type="string",
    description="City name in English (e.g., 'Moscow', 'New York')"
)
```

### 3. Используйте `enum` для ограниченных значений

```python
"operation": FunctionParameter(
    type="string",
    description="Mathematical operation to perform",
    enum=["add", "subtract", "multiply", "divide"]
)
```

### 4. Обработка ошибок

```python
async def execute(self, **kwargs) -> str:
    try:
        result = await self._do_work(**kwargs)
        return json.dumps({"success": True, "data": result})
    except ValueError as e:
        return json.dumps({"success": False, "error": str(e)})
```

### 5. Возвращайте структурированные данные

```python
# Плохо
return "The weather is sunny and 25 degrees"

# Хорошо
return json.dumps({
    "temperature": 25,
    "units": "celsius",
    "conditions": "sunny",
    "humidity": 45
})
```

---

## Ссылки на документацию

### Официальная документация Mistral

- [Function Calling](https://docs.mistral.ai/capabilities/function_calling/) — основное руководство
- [API Reference](https://docs.mistral.ai/api/) — спецификация API
- [Models](https://docs.mistral.ai/getting-started/models/models_overview/) — обзор моделей
- [Python SDK](https://docs.mistral.ai/getting-started/clients/) — клиентские библиотеки

### Спецификации

- [JSON Schema](https://json-schema.org/) — стандарт описания параметров
- [OpenAPI](https://swagger.io/specification/) — спецификация API

### Примеры использования

- [Mistral Cookbook](https://github.com/mistralai/cookbook) — примеры от Mistral
- [Function Calling Examples](https://docs.mistral.ai/capabilities/function_calling/#example) — примеры в документации

---

## Troubleshooting

### Ошибка: "Invalid tool schema: None is not of type 'array'"

**Причина:** Поля с `None` сериализуются как `null`, но API ожидает отсутствие поля.

**Решение:** Используйте `model_dump(exclude_none=True)` при сериализации.

### Ошибка: "Not the same number of function calls and responses"

**Причина:** Assistant message не содержит `tool_calls`.

**Решение:** При добавлении assistant message после tool call, включите поле `tool_calls`.

### Модель не использует инструменты

**Возможные причины:**
1. Неточное описание инструмента
2. Запрос не требует использования инструментов
3. `tool_choice="none"`

**Решение:** Используйте `tool_choice="any"` для принудительного использования.
