from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError

from search_trends.api.dependencies import get_store, get_trend_service
from search_trends.domain.models import TrendItem, TrendResponse
from search_trends.infrastructure.redis_store import RedisTrendStore
from search_trends.main import create_app
from search_trends.services.trends import TrendService


@pytest.fixture
async def client() -> AsyncIterator[tuple[AsyncClient, AsyncMock, AsyncMock]]:
    app = create_app()
    store = AsyncMock(spec=RedisTrendStore)
    store.stop_words.return_value = {"казино"}
    service = AsyncMock(spec=TrendService)
    service.top.return_value = TrendResponse(
        window_seconds=300,
        generated_at=datetime(2026, 7, 29, tzinfo=UTC),
        items=[TrendItem(query="iphone", count=42)],
    )
    app.dependency_overrides[get_store] = lambda: store
    app.dependency_overrides[get_trend_service] = lambda: service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client, store, service
    app.dependency_overrides.clear()


async def test_get_top(client: tuple[AsyncClient, AsyncMock, AsyncMock]) -> None:
    http, _, service = client

    response = await http.get("/api/v1/trends", params={"limit": 10})

    assert response.status_code == 200
    assert response.json()["items"] == [{"query": "iphone", "count": 42}]
    service.top.assert_awaited_once_with(10)


async def test_stop_words_require_admin(
    client: tuple[AsyncClient, AsyncMock, AsyncMock],
) -> None:
    http, _, _ = client

    response = await http.get("/api/v1/stop-words")

    assert response.status_code == 401


async def test_list_stop_words(
    client: tuple[AsyncClient, AsyncMock, AsyncMock], admin_token: str
) -> None:
    http, _, _ = client

    response = await http.get(
        "/api/v1/stop-words",
        headers={"X-Admin-Token": admin_token},
    )

    assert response.status_code == 200
    assert response.json() == {"words": ["казино"]}


async def test_readiness_returns_503(
    client: tuple[AsyncClient, AsyncMock, AsyncMock],
) -> None:
    http, store, _ = client
    store.ping.side_effect = RuntimeError("redis unavailable")

    response = await http.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Redis is unavailable"}


async def test_liveness_returns_200_even_when_redis_is_down(
    client: tuple[AsyncClient, AsyncMock, AsyncMock],
) -> None:
    http, store, _ = client
    store.ping.side_effect = RedisConnectionError("connection refused")

    response = await http.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_trends_returns_503_on_redis_connection_error(
    client: tuple[AsyncClient, AsyncMock, AsyncMock],
) -> None:
    http, _, service = client
    service.top.side_effect = RedisConnectionError("connection refused")

    response = await http.get("/api/v1/trends", params={"limit": 10})

    assert response.status_code == 503
    assert response.json() == {"detail": "Redis is unavailable"}


async def test_list_stop_words_returns_503_on_redis_connection_error(
    client: tuple[AsyncClient, AsyncMock, AsyncMock], admin_token: str
) -> None:
    http, store, _ = client
    store.stop_words.side_effect = RedisConnectionError("connection refused")

    response = await http.get(
        "/api/v1/stop-words",
        headers={"X-Admin-Token": admin_token},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Redis is unavailable"}


async def test_add_stop_word_returns_503_on_redis_connection_error(
    client: tuple[AsyncClient, AsyncMock, AsyncMock], admin_token: str
) -> None:
    http, store, _ = client
    store.add_stop_word.side_effect = RedisConnectionError("connection refused")

    response = await http.post(
        "/api/v1/stop-words",
        json={"word": "казино"},
        headers={"X-Admin-Token": admin_token},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Redis is unavailable"}
