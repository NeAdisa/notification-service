from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/notifications_db"
)


class Settings(BaseSettings):
    database_url: str = Field(
        default=DEFAULT_DATABASE_URL,
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    rate_limit_max: int = Field(default=10, alias="RATE_LIMIT_MAX")
    sender_interval_seconds: int = Field(default=5, alias="SENDER_INTERVAL_SECONDS")
    sender_batch_size: int = Field(default=10, alias="SENDER_BATCH_SIZE")
    notification_max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="NOTIFICATION_MAX_ATTEMPTS",
    )
    env: str = Field(default="local", alias="ENV")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
