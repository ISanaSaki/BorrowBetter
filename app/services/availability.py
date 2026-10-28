"""Availability — the ONE place the rest of the team touches reservation data.

Owner: Sana (B).

The three locked entry points (spec §18.2) are:
    free_item_ids()            — A filters the catalog with this
    assert_bookable()          — B's booking path
    has_active_reservations()  — A's soft-delete guard
`reservation_counts()` and `get_availability()` are the two extras the contract
needs (owner dashboard + calendar), nothing else is exported.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import BLOCKING_STATUSES
from app.core.errors import AppError, not_found
from app.schemas.common import serialize_utc

# Status tuple is a module constant, never user input — safe to inline in SQL.
_BLOCKING = "('pending','approved','active')"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def free_item_ids(
    db: Session,
    item_ids: list[int],
    start: datetime,
    end: datetime,
) -> set[int]:
    """Subset of `item_ids` that is completely free during [start, end)."""
    if not item_ids:
        return set()

    stmt = text(
        f"""
        SELECT i.id
          FROM items i
         WHERE i.id IN :ids
           AND i.is_active
           AND NOT EXISTS (
                 SELECT 1
                   FROM reservations r
                  WHERE r.item_id = i.id
                    AND r.status IN {_BLOCKING}
                    AND tstzrange(r.start_at, r.end_at, '[)')
                        && tstzrange(:start_at, :end_at, '[)')
               )
        """
    ).bindparams(bindparam("ids", expanding=True))

    rows = db.execute(
        stmt, {"ids": list(item_ids), "start_at": start, "end_at": end}
    ).scalars()
    return set(rows)


def assert_bookable(db: Session, item_id: int, start: datetime, end: datetime) -> None:
    """Raise SLOT_CONFLICT if the item is not free during [start, end)."""
    conflicts = busy_intervals(db, item_id, start, end)
    if conflicts:
        raise AppError(
            "SLOT_CONFLICT",
            409,
            "This time slot is already booked. Pick one of the suggested alternatives.",
            details={
                "item_id": item_id,
                "requested": {"start_at": serialize_utc(start), "end_at": serialize_utc(end)},
                "conflicts": [
                    {"start_at": serialize_utc(s), "end_at": serialize_utc(e)} for s, e in conflicts
                ],
            },
        )


def has_active_reservations(db: Session, item_id: int) -> bool:
    """True if the item has a pending/approved/active reservation (any time)."""
    value = db.execute(
        text(
            f"""
            SELECT EXISTS (
                SELECT 1 FROM reservations
                 WHERE item_id = :item_id AND status IN {_BLOCKING}
            )
            """
        ),
        {"item_id": item_id},
    ).scalar_one()
    return bool(value)


def reservation_counts(db: Session, item_ids: list[int]) -> dict[int, tuple[int, int]]:
    """{item_id: (active_count, pending_count)} in one round-trip."""
    if not item_ids:
        return {}

    stmt = text(
        """
        SELECT item_id,
               count(*) FILTER (WHERE status IN ('approved','active')) AS active_count,
               count(*) FILTER (WHERE status = 'pending')              AS pending_count
          FROM reservations
         WHERE item_id IN :ids
         GROUP BY item_id
        """
    ).bindparams(bindparam("ids", expanding=True))

    rows = db.execute(stmt, {"ids": list(item_ids)}).all()
    return {row.item_id: (int(row.active_count), int(row.pending_count)) for row in rows}


def busy_intervals(
    db: Session,
    item_id: int,
    frm: datetime,
    to: datetime,
    limit: int | None = None,
) -> list[tuple[datetime, datetime]]:
    """Blocking intervals intersecting [frm, to), ordered by start."""
    settings = get_settings()
    cap = limit if limit is not None else settings.availability_max_rows + 1

    rows = db.execute(
        text(
            f"""
            SELECT start_at, end_at
              FROM reservations
             WHERE item_id = :item_id
               AND status IN {_BLOCKING}
               AND tstzrange(start_at, end_at, '[)') && tstzrange(:frm, :to, '[)')
             ORDER BY start_at
             LIMIT :cap
            """
        ),
        {"item_id": item_id, "frm": frm, "to": to, "cap": cap},
    ).all()
    return [(row.start_at, row.end_at) for row in rows]


def get_availability(
    db: Session,
    item_id: int,
    frm: datetime | None,
    to: datetime | None,
) -> dict:
    """Calendar payload for GET /items/{item_id}/availability (spec §7.13)."""
    settings = get_settings()
    now = _utcnow()

    frm = frm or now
    to = to or now + timedelta(days=30)

    if frm.tzinfo is None or to.tzinfo is None:
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "Timestamps must include a timezone.",
            details={"fields": {"from": "Missing timezone."}},
        )
    frm = frm.astimezone(timezone.utc)
    to = to.astimezone(timezone.utc)

    if to <= frm:
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "The end of the range must be after its start.",
            details={"fields": {"to": "Must be after 'from'."}},
        )

    if to - frm > timedelta(days=settings.availability_max_range_days):
        raise AppError(
            "RANGE_TOO_WIDE",
            422,
            f"Availability can span at most {settings.availability_max_range_days} days.",
            details={"item_id": item_id, "max_days": settings.availability_max_range_days},
        )

    item = db.execute(
        text("SELECT id, is_active FROM items WHERE id = :item_id"),
        {"item_id": item_id},
    ).one_or_none()
    if item is None:
        raise not_found("Item not found.")
    if not item.is_active:
        raise AppError("ITEM_INACTIVE", 409, "This item is currently not available for booking.")

    # +1 row is the sentinel that tells us the range has too many bookings.
    busy = busy_intervals(db, item_id, frm, to, limit=settings.availability_max_rows + 1)
    if len(busy) > settings.availability_max_rows:
        raise AppError(
            "RANGE_TOO_WIDE",
            422,
            "This range has too many bookings; choose a shorter range.",
            details={"item_id": item_id, "max_rows": settings.availability_max_rows},
        )

    return {
        "item_id": item_id,
        "from": frm,
        "to": to,
        "is_available": not busy,
        "min_duration_hours": settings.min_duration_hours,
        "max_duration_days": settings.max_duration_days,
        "busy": [{"start_at": s, "end_at": e} for s, e in busy],
        "server_time": now,
    }
