from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Search Trends Service"
    log_level: str = "INFO"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "search.events.v1"
    kafka_consumer_group: str = "search-trends-v1"
    worker_metrics_port: int = Field(default=9000, ge=1024, le=65535)
    window_seconds: int = Field(default=300, ge=60, le=3600)
    bucket_seconds: int = Field(default=10, ge=1, le=60)
    top_cache_seconds: int = Field(default=1, ge=1, le=10)
    max_top_limit: int = Field(default=100, ge=1, le=1000)
    max_events_per_actor_query: int = Field(default=30, ge=1)
    rate_window_seconds: int = Field(default=10, ge=1, le=300)
    admin_token: str = Field(min_length=16)
    redis_retry_initial_seconds: float = Field(default=0.5, gt=0)
    redis_retry_max_seconds: float = Field(default=30.0, gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
