"""Application settings.

Owner: Asra (scaffold). Read once, cached — env lookups are not free.
Booking tunables (bottom block) belong to B.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "BorrowBetter"
    app_env: str = "dev"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    # --- Database ---
    database_url: str = "postgresql+psycopg://borrowbetter:borrowbetter@127.0.0.1:5432/borrowbetter"
    db_pool_size: int = 10
    db_max_overflow: int = 40
    db_pool_timeout: int = 30
    db_echo: bool = False

    # --- Auth ---
    secret_key: str = "change-me-in-production-please-32chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # --- CORS (comma separated, kept as str so `.env` stays human friendly) ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Booking rules (B) ---
    min_duration_hours: int = 1
    max_duration_days: int = 30
    pending_expire_hours: int = 24
    suggestion_count: int = 3
    availability_max_rows: int = 100
    availability_max_range_days: int = 90
    clock_skew_tolerance_minutes: int = 5
    booking_horizon_days: int = 180

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
