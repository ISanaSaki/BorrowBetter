"""Application entry point (Backend A)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import DEFAULT_SECRET_KEY, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import RequestContextMiddleware, configure_logging
from app.db.session import dispose_engine, get_engine
from app.schemas.common import HealthOut

logger = logging.getLogger("borrowbetter")

DESCRIPTION = """
**BorrowBetter** - a neighborhood library for borrowing things.

- Every route lives under `/api/v1` (except `/health`).
- Success: `{"data": ...}` · Failure: `{"error": {"code", "message", "details"}}`.
- Auth: `Authorization: Bearer <access_token>` from `POST /api/v1/auth/login`.
- All timestamps are ISO-8601 in UTC with a `Z` suffix.

Module ownership: platform & catalog (Backend A) · booking engine (Backend B) · AI (Frontend).
"""

TAGS_METADATA = [
    {"name": "system", "description": "Service health"},
    {"name": "auth", "description": "Registration and login"},
    {"name": "me", "description": "Current user profile and dashboard"},
    {"name": "catalog", "description": "Item categories"},
    {"name": "items", "description": "Item catalog and management"},
    {"name": "reservations", "description": "Booking engine (Backend B)"},
    {"name": "ai", "description": "Semantic search (Frontend)"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("%s v%s starting (env=%s)", settings.app_name, settings.app_version, settings.app_env)
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection established.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database not reachable at startup: %s", exc)
    yield
    dispose_engine()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    if settings.is_production and settings.secret_key == DEFAULT_SECRET_KEY:
        raise RuntimeError("The default SECRET_KEY is not allowed in production.")

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description=DESCRIPTION,
        lifespan=lifespan,
        openapi_tags=TAGS_METADATA,
        contact={"name": "BorrowBetter Team"},
        license_info={"name": "MIT"},
    )

    # Order matters: the last middleware added runs first.
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", response_model=HealthOut, tags=["system"], summary="Service and DB health")
    def health() -> HealthOut:
        db_status = "up"
        try:
            with get_engine().connect() as connection:
                connection.execute(text("SELECT 1"))
        except Exception:  # noqa: BLE001
            db_status = "down"
        return HealthOut(
            status="ok" if db_status == "up" else "degraded",
            db=db_status,
            version=settings.app_version,
            time=datetime.now(timezone.utc),
        )

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/health",
            "api": settings.api_v1_prefix,
        }

    return app


app = create_app()
