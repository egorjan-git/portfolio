from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import orjson
import pytest
from aiokafka import TopicPartition
from aiokafka.structs import ConsumerRecord, OffsetAndMetadata
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from search_trends import worker
from search_trends.infrastructure.redis_store import RecordOutcome, RedisTrendStore

TOPIC = "search.events.v1"
PARTITION = TopicPartition(TOPIC, 0)


class _StopConsuming(Exception):
    """Raised by the fake consumer to end the run() loop after one batch (tests only)."""


def _message(offset: int, value: bytes) -> ConsumerRecord:
    return ConsumerRecord(
        topic=TOPIC,
        partition=PARTITION.partition,
        offset=offset,
        timestamp=0,
        timestamp_type=0,
        key=None,
        value=value,
        checksum=None,
        serialized_key_size=-1,
        serialized_value_size=len(value),
        headers=(),
    )


def _valid_payload() -> bytes:
    return orjson.dumps(
        {
            "event_id": str(uuid4()),
            "query": "iPhone",
            "occurred_at": datetime.now(UTC).isoformat(),
            "actor_id": "actor-1",
        }
    )


@pytest.fixture
def fake_store() -> AsyncMock:
    store = AsyncMock(spec=RedisTrendStore)
    store.stop_words.return_value = set()
    store.record.return_value = RecordOutcome.ACCEPTED
    return store


@pytest.fixture
def fake_consumer() -> MagicMock:
    consumer = MagicMock()
    consumer.start = AsyncMock()
    consumer.stop = AsyncMock()
    consumer.commit = AsyncMock()
    consumer.end_offsets = AsyncMock(side_effect=lambda partitions: dict.fromkeys(partitions, 0))
    consumer.position = AsyncMock(return_value=0)
    return consumer


@pytest.fixture(autouse=True)
def _patch_worker_infra(
    monkeypatch: pytest.MonkeyPatch, fake_store: AsyncMock, fake_consumer: MagicMock
) -> None:
    monkeypatch.setattr(worker, "start_http_server", MagicMock())
    fake_redis = MagicMock()
    fake_redis.aclose = AsyncMock()
    monkeypatch.setattr(Redis, "from_url", MagicMock(return_value=fake_redis))
    monkeypatch.setattr(worker, "RedisTrendStore", MagicMock(return_value=fake_store))
    monkeypatch.setattr(worker, "AIOKafkaConsumer", MagicMock(return_value=fake_consumer))


async def _run_with_batch(
    fake_consumer: MagicMock, batch: dict[TopicPartition, list[ConsumerRecord]]
) -> None:
    fake_consumer.getmany = AsyncMock(side_effect=[batch, _StopConsuming])
    with pytest.raises(_StopConsuming):
        await worker.run()


async def test_valid_json_and_schema_is_recorded(
    fake_consumer: MagicMock, fake_store: AsyncMock
) -> None:
    batch = {PARTITION: [_message(1, _valid_payload())]}

    await _run_with_batch(fake_consumer, batch)

    fake_store.record.assert_awaited_once()
    fake_consumer.commit.assert_awaited_once_with({PARTITION: OffsetAndMetadata(2, "")})


async def test_syntactically_invalid_json_is_skipped_without_payload_logged(
    fake_consumer: MagicMock, fake_store: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_logger = MagicMock()
    fake_logger.ainfo = AsyncMock()
    fake_logger.awarning = AsyncMock()
    monkeypatch.setattr(worker, "logger", fake_logger)
    malformed = b"{not valid json"
    batch = {PARTITION: [_message(5, malformed)]}

    await _run_with_batch(fake_consumer, batch)

    fake_store.record.assert_not_awaited()
    fake_logger.awarning.assert_awaited_once_with(
        "malformed_event", partition=PARTITION.partition, offset=5
    )
    logged_kwargs = fake_logger.awarning.await_args.kwargs
    assert malformed not in logged_kwargs.values()
    assert set(logged_kwargs) == {"partition", "offset"}


async def test_valid_json_with_invalid_schema_is_skipped_without_payload_logged(
    fake_consumer: MagicMock, fake_store: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_logger = MagicMock()
    fake_logger.ainfo = AsyncMock()
    fake_logger.awarning = AsyncMock()
    monkeypatch.setattr(worker, "logger", fake_logger)
    bad_schema = orjson.dumps({"query": "iPhone"})  # missing required fields
    batch = {PARTITION: [_message(7, bad_schema)]}

    await _run_with_batch(fake_consumer, batch)

    fake_store.record.assert_not_awaited()
    fake_logger.awarning.assert_awaited_once()
    args, kwargs = fake_logger.awarning.await_args
    assert args == ("invalid_event",)
    assert kwargs["partition"] == PARTITION.partition
    assert kwargs["offset"] == 7
    assert set(kwargs) == {"partition", "offset", "errors"}
    assert bad_schema not in kwargs.values()


async def test_offset_commits_past_poison_message(
    fake_consumer: MagicMock, fake_store: AsyncMock
) -> None:
    poison = _message(10, b"not json at all")
    valid = _message(11, _valid_payload())
    batch = {PARTITION: [poison, valid]}

    await _run_with_batch(fake_consumer, batch)

    fake_store.record.assert_awaited_once()
    fake_consumer.commit.assert_awaited_once_with({PARTITION: OffsetAndMetadata(12, "")})


async def test_transient_redis_error_is_retried_and_recovers(
    fake_consumer: MagicMock, fake_store: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_store.record.side_effect = [
        RedisConnectionError("connection refused"),
        RecordOutcome.ACCEPTED,
    ]
    sleep_mock = AsyncMock(return_value=False)
    monkeypatch.setattr(worker, "_sleep_unless_stopping", sleep_mock)
    fake_logger = MagicMock()
    fake_logger.ainfo = AsyncMock()
    fake_logger.awarning = AsyncMock()
    monkeypatch.setattr(worker, "logger", fake_logger)
    batch = {PARTITION: [_message(30, _valid_payload())]}

    await _run_with_batch(fake_consumer, batch)

    assert fake_store.record.await_count == 2
    sleep_mock.assert_awaited_once()
    fake_consumer.commit.assert_awaited_once_with({PARTITION: OffsetAndMetadata(31, "")})

    unavailable_calls = [
        call for call in fake_logger.awarning.await_args_list if call.args[0] == "redis_unavailable"
    ]
    assert len(unavailable_calls) == 1
    assert set(unavailable_calls[0].kwargs) == {"partition", "offset", "error"}

    recovered_calls = [
        call for call in fake_logger.ainfo.await_args_list if call.args[0] == "redis_recovered"
    ]
    assert len(recovered_calls) == 1
    assert set(recovered_calls[0].kwargs) == {"partition", "offset"}


async def test_redis_outage_is_not_committed_and_stops_on_shutdown(
    fake_consumer: MagicMock, fake_store: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_store.record.side_effect = RedisConnectionError("connection refused")
    monkeypatch.setattr(worker, "_sleep_unless_stopping", AsyncMock(return_value=True))
    batch = {PARTITION: [_message(40, _valid_payload())]}

    await _run_with_batch(fake_consumer, batch)

    fake_store.record.assert_awaited_once()
    fake_consumer.commit.assert_not_awaited()
