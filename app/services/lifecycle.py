"""State machine, time rules and lazy expiry.

Owner: Sana (B).  Rules are locked in spec §6.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import ReservationStatus
from app.core.errors import AppError

ACTION_LABELS_FA: dict[str, str] = {
    "approve": "approve",
    "reject": "reject",
    "cancel": "cancel",
    "handover": "hand over",
    "return": "return",
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
            "The end of the range must be after its start.",
            details={"fields": {"end_at": "Must be after start_at."}},
        )

    duration = end - start
    if duration < timedelta(hours=settings.min_duration_hours):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            f"Minimum booking duration is {settings.min_duration_hours} hour(s).",
            details={"fields": {"end_at": "Duration is shorter than allowed."}},
        )
    if duration > timedelta(days=settings.max_duration_days):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            f"Maximum booking duration is {settings.max_duration_days} day(s).",
            details={"fields": {"end_at": "Duration is longer than allowed."}},
        )

    if start < now - timedelta(minutes=settings.clock_skew_tolerance_minutes):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "Start time cannot be in the past.",
            details={"fields": {"start_at": "Start time is in the past."}},
        )

    horizon = now + timedelta(days=settings.booking_horizon_days)
    if start > horizon:
        raise AppError(
            "VALIDATION_ERROR",
            422,
            f"Bookings are limited to {settings.booking_horizon_days} days ahead.",
            details={"fields": {"start_at": "Start time is too far in the future."}},
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
    """Next status for (action, current) or 409 INVALID_TRANSITION."""
    target = TRANSITIONS.get((action, current_status))
    if target is None:
        verb = ACTION_LABELS_FA.get(action, action)
        raise AppError(
            "INVALID_TRANSITION",
            409,
            f"Cannot {verb} a request in status '{current_status}'.",
            details={
                "current_status": current_status,
                "attempted_action": action,
            },
        )
    return target
