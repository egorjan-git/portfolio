from datetime import UTC, datetime
from enum import StrEnum

from search_trends.core.metrics import EVENTS_TOTAL, TOP_REQUEST_SECONDS, TOP_RESULT_SIZE
from search_trends.domain.models import SearchEvent, TrendItem, TrendResponse
from search_trends.domain.normalization import normalize_query, query_tokens
from search_trends.infrastructure.redis_store import RecordOutcome, RedisTrendStore


class IgnoreReason(StrEnum):
    EMPTY = "empty"
    STOP_WORD = "stop_word"
    TOO_OLD = "too_old"
    FROM_FUTURE = "from_future"


class TrendService:
    def __init__(
        self,
        store: RedisTrendStore,
        *,
        window_seconds: int,
        bucket_seconds: int,
        cache_seconds: int,
        max_events_per_actor_query: int,
        rate_window_seconds: int,
    ) -> None:
        self._store = store
        self._window_seconds = window_seconds
        self._bucket_seconds = bucket_seconds
        self._cache_seconds = cache_seconds
        self._max_events = max_events_per_actor_query
        self._rate_window_seconds = rate_window_seconds

    async def record(self, event: SearchEvent, now: datetime | None = None) -> str:
        current = now or datetime.now(UTC)
        query = normalize_query(event.query)
        if not query:
            return self._ignored(IgnoreReason.EMPTY)

        age_seconds = (current - event.occurred_at).total_seconds()
        if age_seconds > self._window_seconds:
            return self._ignored(IgnoreReason.TOO_OLD)
        if age_seconds < -30:
            return self._ignored(IgnoreReason.FROM_FUTURE)

        stop_words = await self._store.stop_words()
        if query_tokens(query) & stop_words:
            return self._ignored(IgnoreReason.STOP_WORD)

        outcome = await self._store.record(
            event_id=str(event.event_id),
            query=query,
            actor_id=event.actor_id,
            occurred_at=event.occurred_at,
            window_seconds=self._window_seconds,
            bucket_seconds=self._bucket_seconds,
            max_events=self._max_events,
            rate_window_seconds=self._rate_window_seconds,
        )
        EVENTS_TOTAL.labels(outcome=outcome.value).inc()
        return outcome.value

    async def top(self, limit: int, now: datetime | None = None) -> TrendResponse:
        current = now or datetime.now(UTC)
        with TOP_REQUEST_SECONDS.time():
            rows = await self._store.top(
                limit=limit,
                now=current,
                window_seconds=self._window_seconds,
                bucket_seconds=self._bucket_seconds,
                cache_seconds=self._cache_seconds,
            )
        items = [TrendItem(query=query, count=count) for query, count in rows]
        TOP_RESULT_SIZE.observe(len(items))
        return TrendResponse(
            window_seconds=self._window_seconds,
            generated_at=current,
            items=items,
        )

    @staticmethod
    def _ignored(reason: IgnoreReason) -> str:
        value = f"ignored_{reason.value}"
        EVENTS_TOTAL.labels(outcome=value).inc()
        return value


__all__ = ["RecordOutcome", "TrendService"]
