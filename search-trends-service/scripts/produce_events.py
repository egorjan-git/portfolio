import asyncio
import os
import random
from datetime import UTC, datetime
from uuid import uuid4

import orjson
from aiokafka import AIOKafkaProducer

QUERIES = [
    "iphone 15",
    "кроссовки женские",
    "платье",
    "ноутбук",
    "наушники",
    "умные часы",
]


async def main() -> None:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
    topic = os.getenv("KAFKA_TOPIC", "search.events.v1")
    count = int(os.getenv("EVENT_COUNT", "10000"))
    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap,
        value_serializer=orjson.dumps,
        compression_type="gzip",
    )
    await producer.start()
    try:
        for index in range(count):
            query = random.choices(QUERIES, weights=[35, 25, 15, 10, 8, 7], k=1)[0]
            payload = {
                "event_id": str(uuid4()),
                "query": query,
                "occurred_at": datetime.now(UTC).isoformat(),
                "actor_id": f"demo-{index % 1000}",
            }
            await producer.send(topic, payload, key=query.encode())
        await producer.flush()
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
