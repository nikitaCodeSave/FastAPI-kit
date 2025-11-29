"""
Тесты для Example Router (API Endpoints).

Тестируют HTTP слой — обработку запросов/ответов.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_example(client: AsyncClient) -> None:
    """Тест создания нового example."""
    response = await client.post(
        "/api/v1/examples",
        json={"title": "Test Example", "description": "Test description"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Example"
    assert data["description"] == "Test description"
    assert data["status"] == "draft"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_example_duplicate_title(client: AsyncClient) -> None:
    """Тест создания example с дублирующимся заголовком возвращает 409."""
    # Создать первый example
    await client.post(
        "/api/v1/examples",
        json={"title": "Unique Title"},
    )

    # Попытаться создать второй с тем же заголовком
    response = await client.post(
        "/api/v1/examples",
        json={"title": "Unique Title"},
    )

    assert response.status_code == 409
    assert response.json()["error"] == "example_already_exists"


@pytest.mark.asyncio
async def test_get_example(client: AsyncClient) -> None:
    """Тест получения example по ID."""
    # Создать example
    create_response = await client.post(
        "/api/v1/examples",
        json={"title": "Get Test"},
    )
    example_id = create_response.json()["id"]

    # Получить example
    response = await client.get(f"/api/v1/examples/{example_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "Get Test"


@pytest.mark.asyncio
async def test_get_example_not_found(client: AsyncClient) -> None:
    """Тест получения несуществующего example возвращает 404."""
    response = await client.get("/api/v1/examples/99999")

    assert response.status_code == 404
    assert response.json()["error"] == "example_not_found"


@pytest.mark.asyncio
async def test_list_examples(client: AsyncClient) -> None:
    """Тест получения списка examples с пагинацией."""
    # Создать examples
    for i in range(3):
        await client.post(
            "/api/v1/examples",
            json={"title": f"Example {i}"},
        )

    # Получить все
    response = await client.get("/api/v1/examples")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_examples_pagination(client: AsyncClient) -> None:
    """Тест правильной работы пагинации."""
    # Создать 5 examples
    for i in range(5):
        await client.post(
            "/api/v1/examples",
            json={"title": f"Example {i}"},
        )

    # Получить первую страницу
    response = await client.get("/api/v1/examples?skip=0&limit=2")
    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["skip"] == 0
    assert data["limit"] == 2


@pytest.mark.asyncio
async def test_update_example(client: AsyncClient) -> None:
    """Тест обновления example."""
    # Создать example
    create_response = await client.post(
        "/api/v1/examples",
        json={"title": "Original"},
    )
    example_id = create_response.json()["id"]

    # Обновить
    response = await client.patch(
        f"/api/v1/examples/{example_id}",
        json={"title": "Updated", "status": "published"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["status"] == "published"


@pytest.mark.asyncio
async def test_delete_example(client: AsyncClient) -> None:
    """Тест удаления example."""
    # Создать example
    create_response = await client.post(
        "/api/v1/examples",
        json={"title": "To Delete"},
    )
    example_id = create_response.json()["id"]

    # Удалить
    response = await client.delete(f"/api/v1/examples/{example_id}")
    assert response.status_code == 204

    # Проверить удаление
    get_response = await client.get(f"/api/v1/examples/{example_id}")
    assert get_response.status_code == 404
