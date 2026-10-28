"""Central application settings (single source of truth for env values)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-in-production-please-32chars"


class Settings(BaseSettings):
    """Values come from `.env` or process environment (names are case-insensitive)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "BorrowBetter"
    app_env: str = "dev"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # --- Auth ---
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=1440, ge=1, le=60 * 24 * 30)
    # Lower rounds speed up tests dramatically; keep 12+ outside development.
    bcrypt_rounds: int = Field(default=12, ge=4, le=16)

    # --- Database ---
    database_url: str = (
        "postgresql+psycopg://borrowbetter:borrowbetter@localhost:5432/borrowbetter"
    )
    db_echo: bool = False
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=40, ge=0, le=200)
    db_pool_timeout: int = Field(default=30, ge=1, le=300)
    db_pool_recycle: int = Field(default=1800, ge=-1)

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Booking rules (owned by Backend B) ---
    min_duration_hours: int = 1
    max_duration_days: int = 30
    pending_expire_hours: int = 24
    suggestion_count: int = 3
    clock_skew_tolerance_minutes: int = Field(default=5, ge=0, le=60)
    booking_horizon_days: int = Field(default=180, ge=1, le=3650)
    availability_max_rows: int = Field(default=100, ge=1, le=1000)
    availability_max_range_days: int = Field(default=90, ge=1, le=3650)

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, value: str) -> str:
        return value.upper()

    @field_validator("api_v1_prefix")
    @classmethod
    def _normalize_prefix(cls, value: str) -> str:
        value = "/" + value.strip("/")
        return "" if value == "/" else value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"prod", "production"}

    @property
    def is_testing(self) -> bool:
        return self.app_env.lower() in {"test", "testing"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
