from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from search_trends.domain.models import SearchEvent
from search_trends.infrastructure.redis_store import RecordOutcome, RedisTrendStore
from search_trends.services.trends import TrendService


@pytest.fixture
def store() -> AsyncMock:
    mock = AsyncMock(spec=RedisTrendStore)
    mock.stop_words.return_value = set()
    mock.record.return_value = RecordOutcome.ACCEPTED
    mock.top.return_value = [("iphone", 7)]
    return mock


@pytest.fixture
def service(store: AsyncMock) -> TrendService:
    return TrendService(
        store,
        window_seconds=300,
        bucket_seconds=10,
        cache_seconds=1,
        max_events_per_actor_query=30,
        rate_window_seconds=10,
    )


def event(now: datetime, query: str = "iPhone") -> SearchEvent:
    return SearchEvent(
        event_id=uuid4(),
        query=query,
        occurred_at=now,
        actor_id="actor-1",
    )


async def test_accepts_normalized_event(service: TrendService, store: AsyncMock) -> None:
    now = datetime.now(UTC)

    outcome = await service.record(event(now, "  iPhone  "), now)

    assert outcome == "accepted"
    assert store.record.await_args.kwargs["query"] == "iphone"


async def test_ignores_stop_word(service: TrendService, store: AsyncMock) -> None:
    now = datetime.now(UTC)
    store.stop_words.return_value = {"казино"}

    outcome = await service.record(event(now, "лучшее казино"), now)

    assert outcome == "ignored_stop_word"
    store.record.assert_not_awaited()


async def test_ignores_event_outside_window(service: TrendService, store: AsyncMock) -> None:
    now = datetime.now(UTC)

    outcome = await service.record(event(now - timedelta(seconds=301)), now)

    assert outcome == "ignored_too_old"
    store.record.assert_not_awaited()


@pytest.mark.parametrize(
    ("store_outcome", "expected"),
    [
        (RecordOutcome.DUPLICATE, "duplicate"),
        (RecordOutcome.RATE_LIMITED, "rate_limited"),
    ],
)
async def test_propagates_store_outcomes(
    service: TrendService,
    store: AsyncMock,
    store_outcome: RecordOutcome,
    expected: str,
) -> None:
    now = datetime.now(UTC)
    store.record.return_value = store_outcome

    assert await service.record(event(now), now) == expected


async def test_returns_ranked_top(service: TrendService) -> None:
    response = await service.top(10, datetime.now(UTC))

    assert [(item.query, item.count) for item in response.items] == [("iphone", 7)]
