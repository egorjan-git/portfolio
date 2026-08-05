import secrets
from typing import Annotated, cast

from fastapi import Depends, Header, HTTPException, Request, status

from search_trends.core.config import Settings, get_settings
from search_trends.infrastructure.redis_store import RedisTrendStore
from search_trends.services.trends import TrendService


def get_store(request: Request) -> RedisTrendStore:
    return cast(RedisTrendStore, request.app.state.store)


def get_trend_service(request: Request) -> TrendService:
    return cast(TrendService, request.app.state.trend_service)


def require_admin(
    settings: Annotated[Settings, Depends(get_settings)],
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    if x_admin_token is None or not secrets.compare_digest(x_admin_token, settings.admin_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
