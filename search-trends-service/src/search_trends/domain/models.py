from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SearchEvent(BaseModel):
    event_id: UUID
    query: str = Field(min_length=1, max_length=256)
    occurred_at: datetime
    actor_id: str = Field(min_length=1, max_length=128)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        return value.astimezone(UTC)


class TrendItem(BaseModel):
    query: str
    count: int = Field(ge=1)


class TrendResponse(BaseModel):
    window_seconds: int
    generated_at: datetime
    items: list[TrendItem]


class StopWordRequest(BaseModel):
    word: str = Field(min_length=1, max_length=64)


class StopWordResponse(BaseModel):
    words: list[str]
