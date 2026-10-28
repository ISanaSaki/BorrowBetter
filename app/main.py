"""ASGI application — wiring, middleware, error envelopes.

Owner: Asra (scaffold).  Contract: spec §7.0 and §7.24.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.deps import get_db
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("%s v%s started (env=%s)", settings.app_name, settings.version, settings.app_env)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="BorrowBetter - a community tool-lending library.",
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.include_router(api_router, prefix=settings.api_v1_prefix)


# --------------------------------------------------------------------------- #
# Error handling — one envelope for everything (spec §0.7)
# --------------------------------------------------------------------------- #
_FIELD_MESSAGES: dict[str, str] = {
    "missing": "این فیلد الزامی است.",
    "extra_forbidden": "این فیلد در قرارداد وجود ندارد.",
    "string_too_short": "مقدار کوتاه‌تر از حد مجاز است.",
    "string_too_long": "مقدار بلندتر از حد مجاز است.",
    "greater_than": "باید بزرگ‌تر از حد مجاز باشد.",
    "greater_than_equal": "باید بزرگ‌تر یا مساوی حد مجاز باشد.",
    "less_than": "باید کوچک‌تر از حد مجاز باشد.",
    "less_than_equal": "باید کوچک‌تر یا مساوی حد مجاز باشد.",
    "int_parsing": "باید عدد صحیح باشد.",
    "int_type": "باید عدد صحیح باشد.",
    "bool_parsing": "باید مقدار درست/نادرست باشد.",
    "enum": "مقدار مجاز نیست.",
    "datetime_parsing": "قالب تاریخ نامعتبر است.",
    "datetime_from_date_parsing": "قالب تاریخ نامعتبر است.",
    "datetime_type": "قالب تاریخ نامعتبر است.",
    "date_parsing": "قالب تاریخ نامعتبر است.",
    "string_type": "باید متن باشد.",
    "json_invalid": "بدنهٔ درخواست JSON معتبر نیست.",
    "model_attributes_type": "بدنهٔ درخواست معتبر نیست.",
}


def _field_name(loc: tuple[Any, ...]) -> str:
    parts = [str(part) for part in loc]
    if parts and parts[0] in ("body", "query", "path", "header", "cookie"):
        parts = parts[1:]
    return ".".join(parts) or "body"


def _message_for(err: dict[str, Any]) -> str:
    err_type = err.get("type", "")
    if err_type == "value_error":
        raw = err.get("msg", "")
        return raw.split("Value error, ", 1)[-1] if "Value error, " in raw else "مقدار نامعتبر است."
    return _FIELD_MESSAGES.get(err_type, "مقدار نامعتبر است.")


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: dict[str, str] = {}
    for err in exc.errors():
        name = _field_name(tuple(err.get("loc", ())))
        fields.setdefault(name, _message_for(err))
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "ورودی نامعتبر است.",
                "details": {"fields": fields},
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
    }.get(exc.status_code, "HTTP_ERROR")
    message = {
        401: "برای این کار باید وارد حساب کاربری شوید.",
        403: "شما مجاز به انجام این کار نیستید.",
        404: "مسیر مورد نظر پیدا نشد.",
        405: "این متد برای این مسیر مجاز نیست.",
    }.get(exc.status_code, "درخواست قابل انجام نیست.")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message, "details": None}},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "خطای غیرمنتظره‌ای رخ داد؛ لطفاً دوباره تلاش کنید.",
                "details": None,
            }
        },
    )


# --------------------------------------------------------------------------- #
# Health (outside /api/v1 — spec §7.0)
# --------------------------------------------------------------------------- #
@app.get("/health", tags=["health"], summary="Service and database health")
def health(db: Session = Depends(get_db)) -> dict:
    db_status = "up"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - only when the DB is really down
        logger.warning("health check: database is unreachable", exc_info=True)
        db_status = "down"

    return {
        "status": "ok" if db_status == "up" else "degraded",
        "db": db_status,
        "version": settings.version,
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }

