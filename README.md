# FastAPI-kit

**Production-ready шаблон для создания FastAPI сервисов с чистой архитектурой**

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-V2-red.svg)

---

## Оглавление

1. [Введение](#введение)
2. [Быстрый старт](#быстрый-старт)
3. [Структура проекта](#структура-проекта)
4. [Архитектура: Трёхслойная модель](#архитектура-трёхслойная-модель)
   - [Router (Presentation Layer)](#router-presentation-layer)
   - [Service (Business Logic Layer)](#service-business-logic-layer)
   - [Repository (Data Access Layer)](#repository-data-access-layer)
5. [Компоненты домена](#компоненты-домена)
   - [models.py](#modelspy)
   - [schemas.py](#schemaspy)
   - [repository.py](#repositorypy)
   - [service.py](#servicepy)
   - [router.py](#routerpy)
   - [dependencies.py](#dependenciespy)
   - [exceptions.py](#exceptionspy)
   - [constants.py](#constantspy)
6. [Dependency Injection](#dependency-injection)
7. [Обработка ошибок](#обработка-ошибок)
8. [База данных](#база-данных)
9. [Конфигурация](#конфигурация)
10. [Логирование](#логирование)
11. [Создание нового домена](#создание-нового-домена)
12. [Тестирование](#тестирование)
13. [Docker](#docker)
14. [Best Practices и Анти-паттерны](#best-practices-и-анти-паттерны)
15. [Полезные ссылки](#полезные-ссылки)

---

## Введение

### Что это?

FastAPI-kit — это референсная реализация FastAPI-приложения, демонстрирующая современные архитектурные паттерны и best practices. Проект служит шаблоном для создания production-ready микросервисов.

### Какие проблемы решает?

- **Архитектурная неопределённость**: Даёт готовую структуру с чётким разделением ответственности
- **Boilerplate код**: Содержит все необходимые компоненты, которые можно копировать
- **Consistency**: Обеспечивает единообразие кода в команде
- **Best Practices**: Демонстрирует современные подходы FastAPI + SQLAlchemy 2.0 + Pydantic V2

### Философия проекта

1. **Thin Router, Thick Service** — роутер только принимает/отдаёт HTTP, вся логика в сервисе
2. **Dependency Injection** — все зависимости инжектируются через FastAPI `Depends`
3. **Domain-Based Structure** — код организован по доменам, а не по типам файлов
4. **Type Safety** — полная типизация везде (Mapped, Pydantic, type hints)
5. **Async-First** — все I/O операции асинхронные

### Технологический стек

| Компонент | Технология | Версия |
|-----------|------------|--------|
| Web Framework | FastAPI | 0.115+ |
| ORM | SQLAlchemy | 2.0+ |
| Validation | Pydantic | V2 |
| Config | pydantic-settings | 2.x |
| Logging | structlog | 24.x |
| Testing | pytest-asyncio | latest |
| HTTP Client | httpx | 0.28+ |

---

## Быстрый старт

### Требования

- Python 3.12+
- pip или poetry

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/your-username/FastAPI-kit.git
cd FastAPI-kit

# 2. Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. (Опционально) Создать .env файл
cp .env.example .env
```

### Запуск

```bash
# Из корня проекта
cd backend
fastapi dev src/main.py --reload

# Или напрямую через uvicorn
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Проверка

```bash
# Health check
curl http://localhost:8000/health

# Swagger UI (только в development)
open http://localhost:8000/docs

# Создать example
curl -X POST http://localhost:8000/api/v1/examples \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "description": "My first example"}'
```

---

## Структура проекта

```
FastAPI-kit/
├── backend/
│   ├── src/
│   │   ├── main.py                 # Точка входа FastAPI
│   │   ├── config.py               # Конфигурация (pydantic-settings)
│   │   ├── database.py             # SQLAlchemy setup
│   │   ├── logging_config.py       # structlog конфигурация
│   │   │
│   │   ├── shared/                 # Общие компоненты
│   │   │   ├── exceptions.py       # Базовые исключения
│   │   │   └── schemas.py          # Общие Pydantic схемы
│   │   │
│   │   └── example/                # Пример домена (ШАБЛОН)
│   │       ├── __init__.py
│   │       ├── constants.py        # Константы домена
│   │       ├── models.py           # SQLAlchemy модели
│   │       ├── schemas.py          # Pydantic DTOs
│   │       ├── repository.py       # Слой доступа к данным
│   │       ├── service.py          # Бизнес-логика
│   │       ├── router.py           # HTTP endpoints
│   │       ├── dependencies.py     # DI цепочка
│   │       └── exceptions.py       # Доменные исключения
│   │
│   ├── tests/
│   │   ├── conftest.py             # Pytest фикстуры
│   │   └── example/
│   │       ├── test_router.py
│   │       └── test_service.py
│   │
│   ├── Dockerfile
│   └── pyproject.toml
│
├── docs/                           # Документация
├── requirements.txt
└── README.md
```

### Диаграмма архитектуры

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Request                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ROUTER (Thin Layer)                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  • Валидация request через Pydantic schemas                 ││
│  │  • Вызов service через Depends()                            ││
│  │  • Форматирование response                                   ││
│  │  • HTTP статус-коды                                          ││
│  │  • OpenAPI документация                                      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │ Depends(get_example_service)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE (Business Logic)                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  • ВСЯ бизнес-логика                                        ││
│  │  • Валидация бизнес-правил                                  ││
│  │  • Оркестрация операций                                     ││
│  │  • Выброс доменных исключений                               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                  REPOSITORY (Data Access)                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  • CRUD операции                                            ││
│  │  • SQL запросы (через SQLAlchemy)                           ││
│  │  • Возвращает объекты или None                              ││
│  │  • НИКАКОЙ бизнес-логики                                    ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                         ┌───────────┐
                         │  Database │
                         └───────────┘
```

---

## Архитектура: Трёхслойная модель

Проект использует **трёхслойную архитектуру** (3-Tier Architecture) с чётким разделением ответственности между слоями.

### Router (Presentation Layer)

**Файл**: `router.py`

**Ответственность**: Только HTTP-забота

- Приём HTTP запросов
- Валидация входных данных через Pydantic
- Делегирование в Service
- Форматирование ответа
- Установка статус-кодов
- OpenAPI документация

**Принцип**: Router должен быть ТОНКИМ. Никакой бизнес-логики!

```python
# router.py — ПРАВИЛЬНО
@router.post("", response_model=ExampleResponse, status_code=status.HTTP_201_CREATED)
async def create_example(
    data: ExampleCreate,
    service: ExampleService = Depends(get_example_service),
) -> ExampleResponse:
    """Создать новый example."""
    example = await service.create(data)
    return ExampleResponse.model_validate(example)
```

```python
# router.py — НЕПРАВИЛЬНО (бизнес-логика в роутере)
@router.post("")
async def create_example(data: ExampleCreate, db: AsyncSession = Depends(get_db)):
    # ❌ Бизнес-логика в роутере!
    existing = await db.execute(select(Example).where(Example.title == data.title))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Title already exists")

    example = Example(title=data.title)
    db.add(example)
    await db.commit()
    return example
```

### Service (Business Logic Layer)

**Файл**: `service.py`

**Ответственность**: ВСЯ бизнес-логика

- Проверка бизнес-правил
- Валидация на уровне домена
- Оркестрация операций
- Выброс доменных исключений
- Работа с несколькими репозиториями (если нужно)

**Принцип**: Сервис — это сердце домена. Вся логика живёт здесь.

```python
# service.py
class ExampleService:
    def __init__(self, repository: ExampleRepository) -> None:
        self.repository = repository

    async def create(self, data: ExampleCreate) -> Example:
        """
        Создать новый example.

        Raises:
            ExampleAlreadyExistsError: Если заголовок уже существует
        """
        # Бизнес-правило: заголовок должен быть уникальным
        existing = await self.repository.get_by_title(data.title)
        if existing:
            raise ExampleAlreadyExistsError(
                f"Example with title '{data.title}' already exists"
            )

        example = Example(
            title=data.title,
            description=data.description,
        )
        return await self.repository.create(example)

    async def update(self, example_id: int, data: ExampleUpdate) -> Example:
        """Обновить example с валидацией."""
        example = await self.get_by_id(example_id)  # Проверит существование

        # Бизнес-правило: при изменении заголовка проверить уникальность
        if data.title and data.title != example.title:
            existing = await self.repository.get_by_title(data.title)
            if existing:
                raise ExampleAlreadyExistsError(
                    f"Example with title '{data.title}' already exists"
                )

        # Применить только переданные поля
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(example, field, value)

        return await self.repository.update(example)
```

### Repository (Data Access Layer)

**Файл**: `repository.py`

**Ответственность**: Только работа с базой данных

- CRUD операции
- Построение SQL запросов
- Пагинация и фильтрация
- Возврат объектов или `None`

**Принцип**: Репозиторий НИКОГДА не выбрасывает бизнес-исключения и не содержит бизнес-логику.

```python
# repository.py
class ExampleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, example: Example) -> Example:
        """Создать новый example."""
        self.session.add(example)
        await self.session.flush()
        await self.session.refresh(example)
        return example

    async def get_by_id(self, example_id: int) -> Example | None:
        """Получить example по ID. Возвращает None если не найден."""
        return await self.session.get(Example, example_id)

    async def get_by_title(self, title: str) -> Example | None:
        """Получить example по заголовку."""
        result = await self.session.execute(
            select(Example).where(Example.title == title)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> list[Example]:
        """Получить все examples с пагинацией и фильтрацией."""
        query = select(Example).offset(skip).limit(limit)

        if is_active is not None:
            query = query.where(Example.is_active == is_active)

        query = query.order_by(Example.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
```

### Взаимодействие слоёв

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Router                                                           │
│   data: ExampleCreate (Pydantic валидация)                       │
│   service = Depends(get_example_service)                         │
│   example = await service.create(data)  ─────────────────────┐   │
│   return ExampleResponse.model_validate(example)              │   │
└─────────────────────────────────────────────────────────────────┘
                                                                 │
    ┌───────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Service                                                          │
│   # Бизнес-правило: проверить уникальность                       │
│   existing = await self.repository.get_by_title(data.title)  ──┐ │
│   if existing:                                                  │ │
│       raise ExampleAlreadyExistsError(...)                      │ │
│   example = Example(...)                                        │ │
│   return await self.repository.create(example)  ────────────────┼─┤
└─────────────────────────────────────────────────────────────────┘ │
                                                                    │
    ┌───────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ Repository                                                       │
│   self.session.add(example)                                      │
│   await self.session.flush()                                     │
│   await self.session.refresh(example)                            │
│   return example                                                 │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
  Database
```

---

## Компоненты домена

Каждый домен состоит из 8 файлов. Рассмотрим каждый детально.

### models.py

**SQLAlchemy ORM модели** с синтаксисом версии 2.0.

```python
"""
SQLAlchemy модели домена Example.

Синтаксис SQLAlchemy 2.0 с Mapped типами для полной поддержки type hints.
"""

from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from src.example.constants import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH


class Example(Base):
    """
    Модель Example, демонстрирующая паттерны SQLAlchemy 2.0.

    Используйте Mapped[type] для всех полей для автокомплита IDE и проверки типов.
    """

    __tablename__ = "examples"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)

    # String с ограничением длины и индексом
    title: Mapped[str] = mapped_column(String(MAX_TITLE_LENGTH), index=True)

    # Nullable поле (str | None)
    description: Mapped[str | None] = mapped_column(Text, default=None)

    # String с дефолтным значением
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # Boolean с дефолтом
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps с server-side дефолтами
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),  # Автообновление при изменении
    )

    def __repr__(self) -> str:
        return f"<Example {self.id}: {self.title}>"
```

**Ключевые паттерны:**

| Паттерн | Описание |
|---------|----------|
| `Mapped[type]` | Обязательно для всех полей (SQLAlchemy 2.0) |
| `String(MAX_LENGTH)` | Ограничение длины на уровне БД |
| `index=True` | Индекс для полей, по которым часто ищут |
| `server_default=func.now()` | Дефолт на стороне БД, а не Python |
| `onupdate=func.now()` | Автообновление timestamp при изменении |
| `str \| None` | Union синтаксис Python 3.10+ для nullable |

### schemas.py

**Pydantic V2 схемы** для валидации и сериализации.

```python
"""
Pydantic схемы домена Example.

Синтаксис Pydantic V2 с model_config вместо class Config.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.example.constants import MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH


class ExampleBase(BaseModel):
    """Базовая схема с общими полями."""

    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)


class ExampleCreate(ExampleBase):
    """Схема для создания (POST). Наследует обязательные поля."""
    pass


class ExampleUpdate(BaseModel):
    """
    Схема для обновления (PATCH).

    Все поля опциональны — partial update.
    НЕ наследуется от Base, чтобы title не был обязательным.
    """

    title: str | None = Field(None, min_length=1, max_length=MAX_TITLE_LENGTH)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    status: str | None = None
    is_active: bool | None = None


class ExampleResponse(ExampleBase):
    """
    Схема для ответа API.

    from_attributes=True позволяет создавать из ORM объекта.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

**Паттерн схем:**

```
ExampleBase (общие поля)
    ├── ExampleCreate (POST, все поля обязательны)
    └── ExampleResponse (GET, включает id и timestamps)

ExampleUpdate (PATCH, все поля опциональны)
```

**Pydantic V2 API:**

| Метод V1 | Метод V2 | Описание |
|----------|----------|----------|
| `.dict()` | `.model_dump()` | Конвертация в dict |
| `.json()` | `.model_dump_json()` | Конвертация в JSON string |
| `.parse_obj(data)` | `.model_validate(data)` | Создание из dict/ORM |
| `orm_mode = True` | `from_attributes=True` | Работа с ORM объектами |
| `class Config:` | `model_config = ConfigDict()` | Конфигурация |

### repository.py

**Слой доступа к данным** — только CRUD операции.

```python
"""
Репозиторий домена Example.

Слой репозитория обрабатывает ТОЛЬКО доступ к БД.
Никакой бизнес-логики здесь — только CRUD операции.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.example.models import Example


class ExampleRepository:
    """
    Репозиторий для модели Example.

    Выполняет все операции с БД для examples.
    Возвращает ORM объекты или None, никогда не выбрасывает бизнес-исключения.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, example: Example) -> Example:
        """Создать новый example."""
        self.session.add(example)
        await self.session.flush()      # Записать в БД (без commit)
        await self.session.refresh(example)  # Получить сгенерированные поля
        return example

    async def get_by_id(self, example_id: int) -> Example | None:
        """Получить example по ID."""
        return await self.session.get(Example, example_id)

    async def get_by_title(self, title: str) -> Example | None:
        """Получить example по заголовку."""
        result = await self.session.execute(
            select(Example).where(Example.title == title)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> list[Example]:
        """Получить все examples с опциональной фильтрацией."""
        query = select(Example).offset(skip).limit(limit)

        if is_active is not None:
            query = query.where(Example.is_active == is_active)

        query = query.order_by(Example.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, is_active: bool | None = None) -> int:
        """Подсчитать общее количество examples."""
        query = select(func.count(Example.id))

        if is_active is not None:
            query = query.where(Example.is_active == is_active)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(self, example: Example) -> Example:
        """Обновить example (изменения уже внесены в объект)."""
        await self.session.flush()
        await self.session.refresh(example)
        return example

    async def delete(self, example: Example) -> None:
        """Удалить example."""
        await self.session.delete(example)
        await self.session.flush()
```

**Важно**:
- Repository возвращает `None` если объект не найден (не выбрасывает исключение)
- `flush()` записывает в БД, но не коммитит (commit делает dependency в конце запроса)
- `refresh()` обновляет объект данными из БД (для получения `id`, `created_at` и т.д.)

### service.py

**Бизнес-логика** — сердце домена.

```python
"""
Сервис домена Example.

Слой сервиса содержит ВСЮ бизнес-логику.
Это сердце домена — валидация, правила, оркестрация.
"""

from src.example.exceptions import ExampleAlreadyExistsError, ExampleNotFoundError
from src.example.models import Example
from src.example.repository import ExampleRepository
from src.example.schemas import ExampleCreate, ExampleUpdate


class ExampleService:
    """
    Сервис для бизнес-логики домена Example.

    Все бизнес-правила и валидация происходят здесь.
    Роутер должен быть ТОНКИМ — только HTTP-заботы.
    """

    def __init__(self, repository: ExampleRepository) -> None:
        self.repository = repository

    async def create(self, data: ExampleCreate) -> Example:
        """
        Создать новый example.

        Raises:
            ExampleAlreadyExistsError: Если заголовок уже существует
        """
        # Бизнес-правило: заголовок должен быть уникальным
        existing = await self.repository.get_by_title(data.title)
        if existing:
            raise ExampleAlreadyExistsError(
                f"Example with title '{data.title}' already exists"
            )

        example = Example(
            title=data.title,
            description=data.description,
        )
        return await self.repository.create(example)

    async def get_by_id(self, example_id: int) -> Example:
        """
        Получить example по ID.

        Raises:
            ExampleNotFoundError: Если example не найден
        """
        example = await self.repository.get_by_id(example_id)
        if not example:
            raise ExampleNotFoundError(f"Example {example_id} not found")
        return example

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        is_active: bool | None = None,
    ) -> tuple[list[Example], int]:
        """
        Получить все examples с пагинацией.

        Returns:
            Tuple из (список examples, общее количество)
        """
        examples = await self.repository.get_all(
            skip=skip, limit=limit, is_active=is_active
        )
        total = await self.repository.count(is_active=is_active)
        return examples, total

    async def update(self, example_id: int, data: ExampleUpdate) -> Example:
        """
        Обновить example.

        Raises:
            ExampleNotFoundError: Если example не найден
            ExampleAlreadyExistsError: Если новый заголовок уже существует
        """
        example = await self.get_by_id(example_id)

        # Бизнес-правило: проверить уникальность при изменении title
        if data.title and data.title != example.title:
            existing = await self.repository.get_by_title(data.title)
            if existing:
                raise ExampleAlreadyExistsError(
                    f"Example with title '{data.title}' already exists"
                )

        # Применить только переданные поля (partial update)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(example, field, value)

        return await self.repository.update(example)

    async def delete(self, example_id: int) -> None:
        """
        Удалить example.

        Raises:
            ExampleNotFoundError: Если example не найден
        """
        example = await self.get_by_id(example_id)
        await self.repository.delete(example)
```

**Ключевые паттерны:**

- Service получает Repository через конструктор (инъекция зависимости)
- Все бизнес-правила проверяются здесь
- При ошибках выбрасываются типизированные исключения
- `model_dump(exclude_unset=True)` — для partial update (только переданные поля)

### router.py

**HTTP endpoints** — тонкий слой.

```python
"""
Роутер домена Example.

Роутер ТОНКИЙ — только HTTP-заботы:
- Валидация запросов (через Pydantic)
- Вызов сервиса
- Форматирование ответа
- Статус-коды

Никакой бизнес-логики здесь!
"""

from fastapi import APIRouter, Depends, Query, status

from src.example.dependencies import get_example_service
from src.example.schemas import ExampleCreate, ExampleResponse, ExampleUpdate
from src.example.service import ExampleService
from src.shared.schemas import PaginatedResponse

router = APIRouter()


@router.post(
    "",
    response_model=ExampleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый example",
)
async def create_example(
    data: ExampleCreate,
    service: ExampleService = Depends(get_example_service),
) -> ExampleResponse:
    """Создать новый элемент example."""
    example = await service.create(data)
    return ExampleResponse.model_validate(example)


@router.get(
    "",
    response_model=PaginatedResponse[ExampleResponse],
    summary="Список всех examples",
)
async def list_examples(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(20, ge=1, le=100, description="Макс. записей для возврата"),
    is_active: bool | None = Query(None, description="Фильтр по статусу активности"),
    service: ExampleService = Depends(get_example_service),
) -> PaginatedResponse[ExampleResponse]:
    """Получить пагинированный список examples."""
    examples, total = await service.get_all(skip=skip, limit=limit, is_active=is_active)
    return PaginatedResponse(
        items=[ExampleResponse.model_validate(e) for e in examples],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{example_id}",
    response_model=ExampleResponse,
    summary="Получить example по ID",
)
async def get_example(
    example_id: int,
    service: ExampleService = Depends(get_example_service),
) -> ExampleResponse:
    """Получить один example по ID."""
    example = await service.get_by_id(example_id)
    return ExampleResponse.model_validate(example)


@router.patch(
    "/{example_id}",
    response_model=ExampleResponse,
    summary="Обновить example",
)
async def update_example(
    example_id: int,
    data: ExampleUpdate,
    service: ExampleService = Depends(get_example_service),
) -> ExampleResponse:
    """Частично обновить example."""
    example = await service.update(example_id, data)
    return ExampleResponse.model_validate(example)


@router.delete(
    "/{example_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить example",
)
async def delete_example(
    example_id: int,
    service: ExampleService = Depends(get_example_service),
) -> None:
    """Удалить example."""
    await service.delete(example_id)
```

**HTTP методы и статус-коды:**

| Операция | Метод | Статус | Описание |
|----------|-------|--------|----------|
| Create | POST | 201 Created | Новый ресурс создан |
| Read | GET | 200 OK | Успешное получение |
| Update | PATCH | 200 OK | Частичное обновление |
| Replace | PUT | 200 OK | Полная замена |
| Delete | DELETE | 204 No Content | Успешное удаление |

### dependencies.py

**Цепочка Dependency Injection**.

```python
"""
Зависимости домена Example.

FastAPI Depends для dependency injection.
Цепочка: get_db -> get_example_repository -> get_example_service
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.example.repository import ExampleRepository
from src.example.service import ExampleService


async def get_example_repository(
    session: AsyncSession = Depends(get_db),
) -> ExampleRepository:
    """Получить ExampleRepository с сессией базы данных."""
    return ExampleRepository(session)


async def get_example_service(
    repository: ExampleRepository = Depends(get_example_repository),
) -> ExampleService:
    """Получить ExampleService с репозиторием."""
    return ExampleService(repository)
```

**Визуализация цепочки:**

```
Request
   │
   ▼
get_example_service()
   │
   ├── Depends(get_example_repository)
   │       │
   │       ├── Depends(get_db)
   │       │       │
   │       │       └── AsyncSession
   │       │
   │       └── ExampleRepository(session)
   │
   └── ExampleService(repository)
```

### exceptions.py

**Доменные исключения**.

```python
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
```

### constants.py

**Константы домена**.

```python
"""
Константы домена Example.

Специфичные для домена константы и конфигурационные значения.
"""

# Значения статусов Example
class ExampleStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# Значения по умолчанию
DEFAULT_PAGE_SIZE = 20
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
```

---

## Dependency Injection

FastAPI имеет мощную встроенную систему DI через `Depends()`.

### Как это работает

```python
from fastapi import Depends

# 1. Dependency — функция, которая что-то возвращает
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmanager.session_factory() as session:
        yield session  # Код после yield выполнится после endpoint

# 2. Использование в endpoint
@router.get("/items")
async def get_items(db: AsyncSession = Depends(get_db)):
    # FastAPI автоматически вызовет get_db() и передаст результат
    ...
```

### Цепочка зависимостей

```python
# database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmanager.session_factory() as session:
        try:
            yield session
            await session.commit()  # Commit после успеха
        except Exception:
            await session.rollback()  # Rollback при ошибке
            raise

# dependencies.py
async def get_example_repository(
    session: AsyncSession = Depends(get_db),  # ← Зависит от get_db
) -> ExampleRepository:
    return ExampleRepository(session)

async def get_example_service(
    repository: ExampleRepository = Depends(get_example_repository),  # ← Зависит от repository
) -> ExampleService:
    return ExampleService(repository)

# router.py
@router.post("")
async def create_example(
    data: ExampleCreate,
    service: ExampleService = Depends(get_example_service),  # ← Вся цепочка
) -> ExampleResponse:
    ...
```

### Преимущества

1. **Тестируемость** — можно подменить любую зависимость через `app.dependency_overrides`
2. **Переиспользование** — одна зависимость может использоваться в разных endpoints
3. **Автоматическое управление ресурсами** — `yield` гарантирует cleanup
4. **Кэширование на уровне запроса** — FastAPI кэширует результат dependency в рамках одного запроса

### Dependencies с yield (cleanup)

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with sessionmanager.session_factory() as session:
        try:
            yield session          # ← Код ДО yield выполняется до endpoint
            await session.commit() # ← Код ПОСЛЕ yield выполняется после endpoint
        except Exception:
            await session.rollback()
            raise
```

---

## Обработка ошибок

### Иерархия исключений

```python
# shared/exceptions.py
class DomainError(Exception):
    """Базовое исключение для всех доменных ошибок."""

    message: str = "A domain error occurred"
    error_code: str = "domain_error"
    status_code: int = 400

    def __init__(
        self,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(DomainError):
    """Ресурс не найден."""
    message = "Resource not found"
    error_code = "not_found"
    status_code = 404


class AlreadyExistsError(DomainError):
    """Ресурс уже существует."""
    message = "Resource already exists"
    error_code = "already_exists"
    status_code = 409


class ValidationError(DomainError):
    """Бизнес-валидация не пройдена."""
    message = "Validation failed"
    error_code = "validation_error"
    status_code = 422


class AuthenticationError(DomainError):
    """Аутентификация не пройдена."""
    message = "Authentication failed"
    error_code = "authentication_error"
    status_code = 401


class AuthorizationError(DomainError):
    """Авторизация не пройдена."""
    message = "Insufficient permissions"
    error_code = "authorization_error"
    status_code = 403
```

**Дерево исключений:**

```
DomainError (400)
├── NotFoundError (404)
│   └── ExampleNotFoundError
├── AlreadyExistsError (409)
│   └── ExampleAlreadyExistsError
├── ValidationError (422)
├── AuthenticationError (401)
└── AuthorizationError (403)
```

### Глобальный Exception Handler

```python
# main.py
@app.exception_handler(DomainError)
async def domain_error_handler(
    request: Request, exc: DomainError
) -> JSONResponse:
    """Обработчик доменных исключений."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
        },
    )
```

### Формат ответа об ошибке

```json
{
    "error": "example_not_found",
    "message": "Example 123 not found",
    "details": {}
}
```

### Использование в Service

```python
# service.py
async def get_by_id(self, example_id: int) -> Example:
    example = await self.repository.get_by_id(example_id)
    if not example:
        raise ExampleNotFoundError(f"Example {example_id} not found")
    return example
```

---

## База данных

### Конфигурация подключения

```python
# database.py
class DatabaseSessionManager:
    """Управляет жизненным циклом движка БД и фабрики сессий."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None

    def init(self, db_url: str) -> None:
        """Инициализировать движок БД."""
        if settings.is_sqlite:
            # SQLite не поддерживает настройки пула
            self._engine = create_async_engine(
                db_url,
                echo=settings.DB_ECHO,
                connect_args={"check_same_thread": False},
            )
        else:
            # PostgreSQL с пулом соединений
            self._engine = create_async_engine(
                db_url,
                echo=settings.DB_ECHO,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
                pool_recycle=settings.DB_POOL_RECYCLE,
                pool_pre_ping=True,  # КРИТИЧНО для production
            )

        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,  # КРИТИЧНО для async
            autocommit=False,
            autoflush=False,
        )
```

### Настройки пула (PostgreSQL)

| Параметр | Development | Production | Описание |
|----------|-------------|------------|----------|
| `pool_size` | 2-5 | 5-20 | Постоянные соединения |
| `max_overflow` | 5 | 10-20 | Временные при пиках |
| `pool_pre_ping` | True | **True** | Проверка соединений |
| `pool_recycle` | 3600 | 3600 | Пересоздание соединений |
| `echo` | True | **False** | SQL логирование |

### Управление сессиями

```python
# database.py
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency, предоставляющий сессию базы данных.

    Сессия автоматически коммитится при успехе, откатывается при ошибке.
    """
    async with sessionmanager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### PostgreSQL в production

```bash
# .env для PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/mydb
```

```python
# requirements.txt (добавить)
asyncpg  # PostgreSQL async driver
```

### Миграции (Alembic)

Для production используйте Alembic:

```bash
# Установка
pip install alembic

# Инициализация
alembic init alembic

# Создание миграции
alembic revision --autogenerate -m "Add users table"

# Применение миграций
alembic upgrade head
```

---

## Конфигурация

### pydantic-settings

```python
# config.py
from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # Файл с переменными
        env_file_encoding="utf-8",
        extra="ignore",            # Игнорировать лишние переменные
    )

    # Application
    PROJECT_NAME: str = "FastAPI Application"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "production"] = "development"
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    # Database pool settings
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    @computed_field
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Кэшированный доступ к настройкам."""
    return Settings()


settings = get_settings()
```

### Переменные окружения

```bash
# .env
PROJECT_NAME="My API"
VERSION="1.0.0"
ENVIRONMENT=production
DEBUG=false

LOG_LEVEL=WARNING

DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/mydb
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=false
```

### Приоритет загрузки

1. Переменные окружения системы (высший приоритет)
2. `.env` файл
3. Дефолтные значения в классе Settings

---

## Логирование

### structlog конфигурация

```python
# logging_config.py
import structlog
from src.config import settings


def setup_logging() -> None:
    """Инициализировать structlog."""
    if settings.ENVIRONMENT == "development":
        # Цветной консольный вывод для разработки
        processors = [
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON для production (ELK, Grafana Loki)
        processors = [
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(processors=processors)
```

### Использование

```python
import structlog

logger = structlog.get_logger(__name__)

# Простое логирование
logger.info("user_created", user_id=123, email="user@example.com")

# С контекстом ошибки
try:
    ...
except Exception as e:
    logger.error("operation_failed", error=str(e), exc_info=True)
```

### Вывод

**Development:**
```
2024-01-15 10:30:45 [info     ] user_created                   email=user@example.com user_id=123
```

**Production (JSON):**
```json
{"event": "user_created", "user_id": 123, "email": "user@example.com", "level": "info", "timestamp": "2024-01-15T10:30:45.123456Z"}
```

---

## Создание нового домена

Пошаговая инструкция по созданию нового домена `users`.

### Шаг 1: Создать директорию

```bash
mkdir -p backend/src/users
touch backend/src/users/__init__.py
```

### Шаг 2: Создать constants.py

```python
# users/constants.py
class UserRole:
    ADMIN = "admin"
    USER = "user"

MAX_USERNAME_LENGTH = 50
MAX_EMAIL_LENGTH = 255
```

### Шаг 3: Создать models.py

```python
# users/models.py
from datetime import datetime
from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base
from src.users.constants import MAX_EMAIL_LENGTH, MAX_USERNAME_LENGTH


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(MAX_EMAIL_LENGTH), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(MAX_USERNAME_LENGTH), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
```

### Шаг 4: Создать schemas.py

```python
# users/schemas.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from src.users.constants import MAX_EMAIL_LENGTH, MAX_USERNAME_LENGTH


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=MAX_USERNAME_LENGTH)


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=MAX_USERNAME_LENGTH)
    is_active: bool | None = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

### Шаг 5: Создать exceptions.py

```python
# users/exceptions.py
from src.shared.exceptions import AlreadyExistsError, NotFoundError


class UserNotFoundError(NotFoundError):
    message = "User not found"
    error_code = "user_not_found"


class UserAlreadyExistsError(AlreadyExistsError):
    message = "User already exists"
    error_code = "user_already_exists"
```

### Шаг 6: Создать repository.py

```python
# users/repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.flush()
```

### Шаг 7: Создать service.py

```python
# users/service.py
from src.users.exceptions import UserAlreadyExistsError, UserNotFoundError
from src.users.models import User
from src.users.repository import UserRepository
from src.users.schemas import UserCreate, UserUpdate


def hash_password(password: str) -> str:
    """Хэширование пароля (заглушка, используйте bcrypt в реальности)."""
    return f"hashed_{password}"


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create(self, data: UserCreate) -> User:
        # Проверить уникальность email
        if await self.repository.get_by_email(data.email):
            raise UserAlreadyExistsError(f"Email {data.email} already registered")

        # Проверить уникальность username
        if await self.repository.get_by_username(data.username):
            raise UserAlreadyExistsError(f"Username {data.username} already taken")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        return await self.repository.create(user)

    async def get_by_id(self, user_id: int) -> User:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user

    async def update(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_by_id(user_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        return await self.repository.update(user)

    async def delete(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        await self.repository.delete(user)
```

### Шаг 8: Создать dependencies.py

```python
# users/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.users.repository import UserRepository
from src.users.service import UserService


async def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(session)


async def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)
```

### Шаг 9: Создать router.py

```python
# users/router.py
from fastapi import APIRouter, Depends, status
from src.users.dependencies import get_user_service
from src.users.schemas import UserCreate, UserResponse, UserUpdate
from src.users.service import UserService

router = APIRouter()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create(data)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.get_by_id(user_id)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.update(user_id, data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> None:
    await service.delete(user_id)
```

### Шаг 10: Создать __init__.py

```python
# users/__init__.py
from src.users.router import router

__all__ = ["router"]
```

### Шаг 11: Зарегистрировать в main.py

```python
# main.py
from src.users.router import router as users_router

# В функции create_application():
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
```

### Шаг 12: Написать тесты

```python
# tests/users/test_service.py
import pytest
from src.users.service import UserService
from src.users.repository import UserRepository
from src.users.schemas import UserCreate
from src.users.exceptions import UserAlreadyExistsError


async def test_create_user(db_session):
    repository = UserRepository(db_session)
    service = UserService(repository)

    data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    user = await service.create(data)

    assert user.id is not None
    assert user.email == "test@example.com"


async def test_create_user_duplicate_email(db_session):
    repository = UserRepository(db_session)
    service = UserService(repository)

    data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    await service.create(data)

    data2 = UserCreate(
        email="test@example.com",  # Тот же email
        username="testuser2",
        password="password123"
    )

    with pytest.raises(UserAlreadyExistsError):
        await service.create(data2)
```

---

## Тестирование

### Структура тестов

```
tests/
├── conftest.py          # Общие фикстуры
├── factories.py         # Фабрики тестовых данных
└── example/
    ├── test_router.py   # Тесты endpoints
    └── test_service.py  # Тесты бизнес-логики
```

### Фикстуры (conftest.py)

```python
# tests/conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base, get_db
from main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Использовать asyncio backend."""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_engine():
    """Создать движок тестовой БД (in-memory SQLite)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncSession:
    """Предоставить чистую сессию БД для каждого теста."""
    async_session = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncClient:
    """Тестовый клиент с переопределёнными зависимостями."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
```

### Тестирование Router (интеграционные тесты)

```python
# tests/example/test_router.py
async def test_create_example(client: AsyncClient):
    response = await client.post(
        "/api/v1/examples",
        json={"title": "Test", "description": "Description"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test"
    assert "id" in data


async def test_create_example_duplicate_title(client: AsyncClient):
    # Создать первый
    await client.post(
        "/api/v1/examples",
        json={"title": "Duplicate", "description": "First"},
    )

    # Попытаться создать с тем же title
    response = await client.post(
        "/api/v1/examples",
        json={"title": "Duplicate", "description": "Second"},
    )

    assert response.status_code == 409
    assert response.json()["error"] == "example_already_exists"


async def test_get_example_not_found(client: AsyncClient):
    response = await client.get("/api/v1/examples/99999")

    assert response.status_code == 404
    assert response.json()["error"] == "example_not_found"
```

### Тестирование Service (unit тесты)

```python
# tests/example/test_service.py
import pytest
from example.service import ExampleService
from example.repository import ExampleRepository
from example.schemas import ExampleCreate
from example.exceptions import ExampleAlreadyExistsError, ExampleNotFoundError


async def test_create_example(db_session):
    repository = ExampleRepository(db_session)
    service = ExampleService(repository)

    data = ExampleCreate(title="Test", description="Description")
    example = await service.create(data)

    assert example.id is not None
    assert example.title == "Test"


async def test_create_example_duplicate(db_session):
    repository = ExampleRepository(db_session)
    service = ExampleService(repository)

    data = ExampleCreate(title="Duplicate")
    await service.create(data)

    with pytest.raises(ExampleAlreadyExistsError):
        await service.create(data)


async def test_get_by_id_not_found(db_session):
    repository = ExampleRepository(db_session)
    service = ExampleService(repository)

    with pytest.raises(ExampleNotFoundError):
        await service.get_by_id(99999)
```

### Запуск тестов

```bash
# Все тесты
cd backend
pytest

# С покрытием
pytest --cov=src

# Конкретный файл
pytest tests/example/test_service.py

# Verbose режим
pytest -v

# Только failed тесты
pytest --lf
```

### Конфигурация pytest

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
python_files = ["test_*.py"]
```

---

## Docker

### Dockerfile (multi-stage build)

```dockerfile
# syntax=docker/dockerfile:1

# ─────────────────────────────────────────────────────────────
# Stage 1: Builder
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ─────────────────────────────────────────────────────────────
# Stage 2: Runtime
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY ./src ./src

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run application using FastAPI CLI
CMD ["fastapi", "run", "src/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Сборка и запуск

```bash
# Сборка образа
docker build -t fastapi-kit ./backend

# Запуск контейнера
docker run -d \
  --name fastapi-app \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db \
  -e ENVIRONMENT=production \
  fastapi-kit

# Проверка логов
docker logs -f fastapi-app
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/app
      - ENVIRONMENT=production
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

---

## Best Practices и Анти-паттерны

### ЧТО ДЕЛАТЬ

| Практика | Описание |
|----------|----------|
| **Thin Router** | Роутер только принимает/отдаёт HTTP, вся логика в Service |
| **Dependency Injection** | Все зависимости через `Depends()` |
| **Type Hints везде** | `Mapped[type]`, Pydantic модели, аннотации функций |
| **async/await** | Все I/O операции асинхронные |
| **Pydantic для Response** | Всегда конвертировать ORM в Pydantic перед возвратом |
| **Domain Exceptions** | Типизированные исключения вместо HTTPException |
| **expire_on_commit=False** | Критично для async SQLAlchemy |
| **pool_pre_ping=True** | Проверка соединений в production |
| **exclude_unset=True** | Для partial update в PATCH |
| **lifespan context** | Вместо устаревших on_startup/on_shutdown |

### ЧЕГО ИЗБЕГАТЬ

| Анти-паттерн | Проблема |
|--------------|----------|
| **Бизнес-логика в Router** | Нарушает separation of concerns |
| **Возврат ORM моделей** | Проблемы с lazy loading, circular refs |
| **sync библиотеки в async** | Блокирует event loop |
| **asyncio.gather() с одной сессией** | Race conditions |
| **HTTPException в Service** | Service не должен знать о HTTP |
| **Hardcoded secrets** | Только через переменные окружения |
| **@app.on_event** | Устарело, используйте lifespan |
| **N+1 запросы** | Используйте eager loading |
| **allow_origins=["*"] с credentials** | Уязвимость безопасности |

### Типичные ошибки

**1. Бизнес-логика в роутере:**

```python
# НЕПРАВИЛЬНО
@router.post("")
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email exists")  # Бизнес-логика в роутере!
    ...

# ПРАВИЛЬНО
@router.post("")
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.create(data)  # Делегирование в service
    return UserResponse.model_validate(user)
```

**2. Возврат ORM модели напрямую:**

```python
# НЕПРАВИЛЬНО
@router.get("/{id}")
async def get_user(id: int, db: AsyncSession = Depends(get_db)) -> User:
    return await db.get(User, id)  # Возврат ORM модели!

# ПРАВИЛЬНО
@router.get("/{id}", response_model=UserResponse)
async def get_user(id: int, service: UserService = Depends(get_user_service)) -> UserResponse:
    user = await service.get_by_id(id)
    return UserResponse.model_validate(user)
```

**3. Sync библиотеки в async:**

```python
# НЕПРАВИЛЬНО
import requests

@router.get("/external")
async def get_external():
    response = requests.get("https://api.example.com")  # Блокирует event loop!
    return response.json()

# ПРАВИЛЬНО
import httpx

@router.get("/external")
async def get_external():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()
```

**4. asyncio.gather() с одной сессией:**

```python
# НЕПРАВИЛЬНО (race conditions)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    users, posts = await asyncio.gather(
        db.execute(select(func.count(User.id))),
        db.execute(select(func.count(Post.id))),
    )
    return {"users": users.scalar_one(), "posts": posts.scalar_one()}

# ПРАВИЛЬНО (один запрос)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.count(User.id).label("users"),
            func.count(Post.id).label("posts"),
        )
    )
    row = result.one()
    return {"users": row.users, "posts": row.posts}
```

---

## Полезные ссылки

### Официальная документация

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [structlog](https://www.structlog.org/en/stable/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/en/latest/)

### Референсные репозитории

- [Full-Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template) — официальный шаблон от создателя FastAPI
- [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices) — 13,600+ stars, комьюнити best practices

### Документация проекта

- [docs/FastAPI_architecture_research.md](docs/FastAPI_architecture_research.md) — исследование современных архитектур FastAPI
- [docs/FASTAPI_RULES_CLAUDE_V2.md](docs/FASTAPI_RULES_CLAUDE_V2.md) — детальные правила разработки

---

## Лицензия

MIT License

---

**Создано с использованием FastAPI-kit** — шаблона для production-ready микросервисов.
