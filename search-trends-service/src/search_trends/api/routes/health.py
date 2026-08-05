from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from search_trends.api.dependencies import get_store
from search_trends.infrastructure.redis_store import RedisTrendStore

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    return HealthResponse()


@router.get("/ready", response_model=HealthResponse)
async def readiness(
    store: Annotated[RedisTrendStore, Depends(get_store)],
) -> HealthResponse:
    try:
        await store.ping()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis is unavailable",
        ) from exc
    return HealthResponse()
