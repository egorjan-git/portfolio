from typing import Annotated

from fastapi import APIRouter, Depends, Query

from search_trends.api.dependencies import get_trend_service
from search_trends.core.config import Settings, get_settings
from search_trends.domain.models import TrendResponse
from search_trends.services.trends import TrendService

router = APIRouter(prefix="/trends", tags=["trends"])


@router.get("", response_model=TrendResponse)
async def get_trends(
    service: Annotated[TrendService, Depends(get_trend_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    limit: Annotated[int, Query(ge=1)] = 10,
) -> TrendResponse:
    bounded_limit = min(limit, settings.max_top_limit)
    return await service.top(bounded_limit)
