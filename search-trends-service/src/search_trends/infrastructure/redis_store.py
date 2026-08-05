import hashlib
import inspect
import math
from collections.abc import Awaitable
from datetime import datetime
from enum import StrEnum
from typing import cast

from redis.asyncio import Redis

from search_trends.domain.normalization import normalize_query, query_tokens

RECORD_SCRIPT = """
if redis.call('SET', KEYS[1], '1', 'NX', 'EX', ARGV[1]) == false then
  return 1
end
local rate = redis.call('INCR', KEYS[2])
if rate == 1 then
  redis.call('EXPIRE', KEYS[2], ARGV[2])
end
if rate > tonumber(ARGV[3]) then
  return 2
end
redis.call('ZINCRBY', KEYS[3], 1, ARGV[4])
redis.call('EXPIRE', KEYS[3], ARGV[5])
return 0
"""


class RecordOutcome(StrEnum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    RATE_LIMITED = "rate_limited"


class RedisTrendStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def ping(self) -> None:
        await _resolve(self._redis.ping())

    async def record(
        self,
        *,
        event_id: str,
        query: str,
        actor_id: str,
        occurred_at: datetime,
        window_seconds: int,
        bucket_seconds: int,
        max_events: int,
        rate_window_seconds: int,
    ) -> RecordOutcome:
        epoch = int(occurred_at.timestamp())
        bucket = epoch // bucket_seconds
        rate_bucket = epoch // rate_window_seconds
        actor_hash = hashlib.sha256(actor_id.encode()).hexdigest()[:24]
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:24]
        result = await _resolve(
            self._redis.eval(
                RECORD_SCRIPT,
                3,
                f"trends:dedup:{event_id}",
                f"trends:rate:{actor_hash}:{query_hash}:{rate_bucket}",
                f"trends:bucket:{bucket}",
                str(window_seconds * 2),
                str(rate_window_seconds * 2),
                str(max_events),
                query,
                str(window_seconds + bucket_seconds * 2),
            )
        )
        return (RecordOutcome.ACCEPTED, RecordOutcome.DUPLICATE, RecordOutcome.RATE_LIMITED)[
            int(result)
        ]

    async def top(
        self,
        *,
        limit: int,
        now: datetime,
        window_seconds: int,
        bucket_seconds: int,
        cache_seconds: int,
    ) -> list[tuple[str, int]]:
        now_epoch = int(now.timestamp())
        first = (now_epoch - window_seconds) // bucket_seconds + 1
        last = now_epoch // bucket_seconds
        keys = [f"trends:bucket:{bucket}" for bucket in range(first, last + 1)]
        destination = f"trends:top-cache:{now_epoch // cache_seconds}"
        if not await _resolve(self._redis.exists(destination)) and keys:
            await _resolve(self._redis.zunionstore(destination, keys, aggregate="SUM"))
            await _resolve(self._redis.expire(destination, cache_seconds + 1))

        stop_words = await self.stop_words()
        result: list[tuple[str, int]] = []
        offset = 0
        page_size = max(limit * 4, 100)
        while len(result) < limit:
            raw = await _resolve(
                self._redis.zrevrange(
                    destination,
                    offset,
                    offset + page_size - 1,
                    withscores=True,
                )
            )
            rows = cast(list[tuple[str, float]], raw)
            if not rows:
                break
            for query, score in rows:
                if not query_tokens(query) & stop_words:
                    result.append((query, math.floor(score)))
                    if len(result) == limit:
                        break
            offset += page_size
        return result

    async def stop_words(self) -> set[str]:
        values = await _resolve(self._redis.smembers("trends:stop-words"))
        return cast(set[str], values)

    async def add_stop_word(self, word: str) -> bool:
        normalized = normalize_query(word)
        if not normalized or len(query_tokens(normalized)) != 1:
            raise ValueError("stop word must contain exactly one token")
        return bool(await _resolve(self._redis.sadd("trends:stop-words", normalized)))

    async def remove_stop_word(self, word: str) -> bool:
        return bool(await _resolve(self._redis.srem("trends:stop-words", normalize_query(word))))


async def _resolve[T](value: Awaitable[T] | T) -> T:
    if inspect.isawaitable(value):
        return await cast(Awaitable[T], value)
    return value
