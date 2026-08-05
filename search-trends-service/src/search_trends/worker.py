import asyncio
import signal

import orjson
import structlog
from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.structs import ConsumerRecord, OffsetAndMetadata
from prometheus_client import start_http_server
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from search_trends.core.config import Settings, get_settings
from search_trends.core.logging import configure_logging
from search_trends.core.metrics import CONSUMER_LAG, EVENTS_TOTAL
from search_trends.domain.models import SearchEvent
from search_trends.infrastructure.redis_store import RedisTrendStore
from search_trends.services.trends import TrendService

logger = structlog.get_logger()

REDIS_TRANSIENT_ERRORS: tuple[type[Exception], ...] = (RedisConnectionError, RedisTimeoutError)


async def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    start_http_server(settings.worker_metrics_port)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    store = RedisTrendStore(redis)
    service = TrendService(
        store,
        window_seconds=settings.window_seconds,
        bucket_seconds=settings.bucket_seconds,
        cache_seconds=settings.top_cache_seconds,
        max_events_per_actor_query=settings.max_events_per_actor_query,
        rate_window_seconds=settings.rate_window_seconds,
    )
    consumer = AIOKafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    stopping = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stopping.set)

    await consumer.start()
    await logger.ainfo("consumer_started", topic=settings.kafka_topic)
    try:
        while not stopping.is_set():
            batch = await consumer.getmany(timeout_ms=1000, max_records=1000)
            for topic_partition, messages in batch.items():
                last_processed = await _process_messages(messages, service, settings, stopping)
                if last_processed is not None:
                    await consumer.commit(
                        {
                            topic_partition: OffsetAndMetadata(
                                last_processed + 1,
                                "",
                            )
                        }
                    )
                await _update_lag(consumer, topic_partition)
                if stopping.is_set():
                    break
    finally:
        await consumer.stop()
        await redis.aclose()
        await logger.ainfo("consumer_stopped")


async def _process_messages(
    messages: list[ConsumerRecord],
    service: TrendService,
    settings: Settings,
    stopping: asyncio.Event,
) -> int | None:
    """Process messages of a single partition in order.

    Returns the highest offset that was fully handled, or None if none were.
    Stops at the first message that could not be handled because shutdown was
    requested while waiting out a Redis outage, so that message is retried
    (not skipped) after restart.
    """
    last_processed: int | None = None
    for message in messages:
        if not await _process_message(message, service, settings, stopping):
            break
        last_processed = message.offset
    return last_processed


async def _process_message(
    message: ConsumerRecord,
    service: TrendService,
    settings: Settings,
    stopping: asyncio.Event,
) -> bool:
    """Handle a single message: parse, validate, and record it.

    Returns True once the message has been handled, whether recorded or
    safely skipped as malformed/invalid. Returns False only when a shutdown
    was requested while waiting out a transient Redis outage; the caller must
    not advance the committed offset past this message in that case.
    """
    try:
        payload = orjson.loads(message.value)
        event = SearchEvent.model_validate(payload)
    except orjson.JSONDecodeError:
        EVENTS_TOTAL.labels(outcome="invalid").inc()
        await logger.awarning(
            "malformed_event",
            partition=message.partition,
            offset=message.offset,
        )
        return True
    except ValidationError as exc:
        EVENTS_TOTAL.labels(outcome="invalid").inc()
        await logger.awarning(
            "invalid_event",
            partition=message.partition,
            offset=message.offset,
            errors=exc.error_count(),
        )
        return True

    delay = settings.redis_retry_initial_seconds
    redis_was_unavailable = False
    while True:
        try:
            await service.record(event)
        except REDIS_TRANSIENT_ERRORS as exc:
            if not redis_was_unavailable:
                redis_was_unavailable = True
                await logger.awarning(
                    "redis_unavailable",
                    partition=message.partition,
                    offset=message.offset,
                    error=type(exc).__name__,
                )
            if await _sleep_unless_stopping(stopping, delay):
                return False
            delay = min(delay * 2, settings.redis_retry_max_seconds)
            continue
        if redis_was_unavailable:
            await logger.ainfo(
                "redis_recovered",
                partition=message.partition,
                offset=message.offset,
            )
        return True


async def _sleep_unless_stopping(stopping: asyncio.Event, delay: float) -> bool:
    """Wait for `delay` seconds, waking early if shutdown is requested.

    Returns True if shutdown was requested before the delay elapsed.
    """
    stop_wait = asyncio.ensure_future(stopping.wait())
    try:
        done, _ = await asyncio.wait({stop_wait}, timeout=delay)
        return stop_wait in done
    finally:
        if not stop_wait.done():
            stop_wait.cancel()


async def _update_lag(consumer: AIOKafkaConsumer, partition: TopicPartition) -> None:
    end_offsets = await consumer.end_offsets([partition])
    position = await consumer.position(partition)
    CONSUMER_LAG.labels(topic=partition.topic, partition=str(partition.partition)).set(
        max(0, end_offsets[partition] - position)
    )


if __name__ == "__main__":
    asyncio.run(run())
