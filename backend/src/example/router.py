"""
Роутер домена Example.

Роутер ТОНКИЙ — только HTTP-забоы:
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
    examples, total = await service.get_all(
        skip=skip,
        limit=limit,
        is_active=is_active,
    )
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
