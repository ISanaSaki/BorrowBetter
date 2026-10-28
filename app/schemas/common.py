"""Envelopes, pagination and the shared UTC datetime type.

Owner: Asra (scaffold). Contract: spec §4.2 (پاکت‌های پاسخ).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator, PlainSerializer

T = TypeVar("T")


def ensure_utc(value: Any) -> datetime:
    """Accept ISO-8601 strings, reject naive datetimes (spec §0.8)."""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("قالب تاریخ نامعتبر است.") from exc
    if not isinstance(value, datetime):
        raise ValueError("تاریخ نامعتبر است.")
    if value.tzinfo is None:
        raise ValueError("زمان باید با منطقهٔ زمانی ارسال شود (مثلاً 2026-11-01T10:00:00Z).")
    return value.astimezone(timezone.utc)


def serialize_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


UtcDatetime = Annotated[
    datetime,
    BeforeValidator(ensure_utc),
    PlainSerializer(serialize_utc, return_type=str),
]


class Meta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool


class Envelope(BaseModel, Generic[T]):
    data: T


class PageEnvelope(BaseModel, Generic[T]):
    data: list[T]
    meta: Meta


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody
