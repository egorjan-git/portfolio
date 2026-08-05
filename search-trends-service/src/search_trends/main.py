from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from search_trends.api.router import api_router
from search_trends.core.config import get_settings
from search_trends.core.logging import configure_logging
from search_trends.infrastructure.redis_store import RedisTrendStore
from search_trends.services.trends import TrendService

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    store = RedisTrendStore(redis)
    app.state.store = store
    app.state.trend_service = TrendService(
        store,
        window_seconds=settings.window_seconds,
        bucket_seconds=settings.bucket_seconds,
        cache_seconds=settings.top_cache_seconds,
        max_events_per_actor_query=settings.max_events_per_actor_query,
        rate_window_seconds=settings.rate_window_seconds,
    )
    yield
    await redis.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    application.include_router(api_router)

    @application.exception_handler(RedisConnectionError)
    @application.exception_handler(RedisTimeoutError)
    async def _redis_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
        await logger.awarning("redis_unavailable", path=request.url.path)
        return JSONResponse(status_code=503, content={"detail": "Redis is unavailable"})

    @application.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return application


app = create_app()
