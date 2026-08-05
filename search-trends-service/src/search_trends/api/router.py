from fastapi import APIRouter

from search_trends.api.routes.health import router as health_router
from search_trends.api.routes.stop_words import router as stop_words_router
from search_trends.api.routes.trends import router as trends_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(trends_router)
api_router.include_router(stop_words_router)
api_router.include_router(health_router)
