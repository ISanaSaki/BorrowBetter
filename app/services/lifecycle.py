"""State machine, time rules and lazy expiry.

Owner: Sana (B).  Rules are locked in spec §6.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import STATUS_LABELS_FA, ReservationStatus
from app.core.errors import AppError

ACTION_LABELS_FA: dict[str, str] = {
    "approve": "تأیید",
    "reject": "رد",
    "cancel": "لغو",
    "handover": "ثبت تحویل",
    "return": "ثبت بازگشت",
}

#: (action, current status) -> next status
TRANSITIONS: dict[tuple[str, str], str] = {
    ("approve", ReservationStatus.PENDING.value): ReservationStatus.APPROVED.value,
    ("reject", ReservationStatus.PENDING.value): ReservationStatus.REJECTED.value,
    ("cancel", ReservationStatus.PENDING.value): ReservationStatus.CANCELLED.value,
    ("cancel", ReservationStatus.APPROVED.value): ReservationStatus.CANCELLED.value,
    ("handover", ReservationStatus.APPROVED.value): ReservationStatus.ACTIVE.value,
    ("return", ReservationStatus.ACTIVE.value): ReservationStatus.RETURNED.value,
}

#: Actions only the item owner may perform.
LENDER_ONLY_ACTIONS = frozenset({"approve", "reject", "handover"})


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_window(start: datetime, end: datetime) -> None:
    """Enforce §6.2: ordering, min/max duration, past tolerance, horizon."""
    settings = get_settings()
    now = utcnow()

    if end <= start:
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "پایان بازه باید بعد از شروع آن باشد.",
            details={"fields": {"end_at": "باید بعد از start_at باشد."}},
        )

    duration = end - start
    if duration < timedelta(hours=settings.min_duration_hours):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            f"حداقل مدت رزرو {settings.min_duration_hours} ساعت است.",
            details={"fields": {"end_at": "مدت رزرو کوتاه‌تر از حد مجاز است."}},
        )
    if duration > timedelta(days=settings.max_duration_days):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            f"حداکثر مدت رزرو {settings.max_duration_days} روز است.",
            details={"fields": {"end_at": "مدت رزرو بیشتر از حد مجاز است."}},
        )

    if start < now - timedelta(minutes=settings.clock_skew_tolerance_minutes):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "زمان شروع نمی‌تواند در گذشته باشد.",
            details={"fields": {"start_at": "زمان شروع در گذشته است."}},
        )

    horizon = now + timedelta(days=settings.booking_horizon_days)
    if start > horizon:
        raise AppError(
            "VALIDATION_ERROR",
            422,
            f"رزرو حداکثر تا {settings.booking_horizon_days} روز آینده ممکن است.",
            details={"fields": {"start_at": "زمان شروع بیش از حد دور است."}},
        )


def calc_price(price_per_day: int, start: datetime, end: datetime) -> int:
    """price_per_day × ceil(hours/24), minimum one day (§6.2)."""
    if price_per_day <= 0:
        return 0
    hours = (end - start).total_seconds() / 3600
    days = max(1, math.ceil(hours / 24))
    return int(price_per_day) * days


def expire_stale_pending(db: Session) -> int:
    """Lazy expiry — no cron, no Redis (§6.3). Returns the number of rows closed."""
    settings = get_settings()
    result = db.execute(
        text(
            """
            UPDATE reservations
               SET status = 'expired', closed_at = now(), updated_at = now()
             WHERE status = 'pending'
               AND created_at < now() - make_interval(hours => :hours)
            """
        ),
        {"hours": settings.pending_expire_hours},
    )
    return result.rowcount or 0


def transition_target(action: str, current_status: str) -> str:
    """Next status for (action, current) or 409 INVALID_TRANSITION with a Persian message."""
    target = TRANSITIONS.get((action, current_status))
    if target is None:
        label = STATUS_LABELS_FA.get(current_status, current_status)
        verb = ACTION_LABELS_FA.get(action, action)
        raise AppError(
            "INVALID_TRANSITION",
            409,
            f"این درخواست در وضعیت «{label}» است و قابل {verb} نیست.",
            details={
                "current_status": current_status,
                "attempted_action": action,
            },
        )
    return target
