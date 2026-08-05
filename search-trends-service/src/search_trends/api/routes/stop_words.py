from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from search_trends.api.dependencies import get_store, require_admin
from search_trends.domain.models import StopWordRequest, StopWordResponse
from search_trends.infrastructure.redis_store import RedisTrendStore

router = APIRouter(
    prefix="/stop-words",
    tags=["stop-words"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=StopWordResponse)
async def list_stop_words(
    store: Annotated[RedisTrendStore, Depends(get_store)],
) -> StopWordResponse:
    return StopWordResponse(words=sorted(await store.stop_words()))


@router.post("", response_model=StopWordResponse, status_code=status.HTTP_201_CREATED)
async def add_stop_word(
    payload: StopWordRequest,
    store: Annotated[RedisTrendStore, Depends(get_store)],
) -> StopWordResponse:
    try:
        await store.add_stop_word(payload.word)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return StopWordResponse(words=sorted(await store.stop_words()))


@router.delete("/{word}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stop_word(
    word: str,
    store: Annotated[RedisTrendStore, Depends(get_store)],
) -> Response:
    removed = await store.remove_stop_word(word)
    if not removed:
        raise HTTPException(status_code=404, detail="Stop word not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
