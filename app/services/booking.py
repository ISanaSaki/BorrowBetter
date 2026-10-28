"""Booking engine — the whole reservation lifecycle.

Owner: Sana (B).

Concurrency model (spec §6.4), three layers:
  1. `SELECT ... FROM items WHERE id = :id FOR UPDATE` serialises requests for
     one item, so suggestions can be computed without a race.
  2. A cheap `NOT EXISTS` overlap check (via availability.busy_intervals) gives
     the user a fast, readable 409.
  3. `EXCLUDE no_overlap` in PostgreSQL is the final guarantee: if the first two
     ever miss something, the insert fails with SQLSTATE 23P01 and we translate
     it into the same 409.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.constants import ReservationStatus
from app.core.errors import AppError, not_found
from app.models.item import Item
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.common import serialize_utc
from app.schemas.reservation import (
    ItemBrief,
    Permissions,
    ReservationCreate,
    ReservationOut,
    UserBrief,
)
from app.services import availability, lifecycle
from app.services.permissions import build_permissions, require_lender, require_party

logger = logging.getLogger(__name__)

MAX_SUGGESTION_SCAN = 200


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def sqlstate(exc: IntegrityError) -> str | None:
    """psycopg3 → .sqlstate ; psycopg2 → .pgcode (never parse the message)."""
    orig = exc.orig
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


def _full_query():
    """Reservation with everything the response needs, in one round-trip."""
    return select(Reservation).options(
        joinedload(Reservation.item).joinedload(Item.owner),
        joinedload(Reservation.borrower),
    )


def _fetch_full(db: Session, reservation_id: int) -> Reservation:
    res = db.execute(_full_query().where(Reservation.id == reservation_id)).unique().scalar_one_or_none()
    if res is None:  # pragma: no cover - row vanished between statements
        raise not_found("رزرو پیدا نشد.")
    return res


def serialize(res: Reservation, viewer: User) -> ReservationOut:
    """ORM → exact API shape (spec §4.2 / §7.14)."""
    item = res.item
    return ReservationOut(
        id=res.id,
        item_id=res.item_id,
        borrower_id=res.borrower_id,
        start_at=res.start_at,
        end_at=res.end_at,
        status=res.status,
        total_price=res.total_price,
        message=res.message,
        decision_note=res.decision_note,
        cancel_reason=res.cancel_reason,
        returned_by=res.returned_by,
        created_at=res.created_at,
        updated_at=res.updated_at,
        approved_at=res.approved_at,
        handover_at=res.handover_at,
        returned_at=res.returned_at,
        closed_at=res.closed_at,
        item=ItemBrief(
            id=item.id,
            title=item.title,
            image_url=item.image_url,
            price_per_day=item.price_per_day,
            owner_id=item.owner_id,
            category=item.category,
            condition=item.condition,
        ),
        borrower=UserBrief(
            id=res.borrower.id,
            full_name=res.borrower.full_name,
            email=res.borrower.email,
        ),
        lender=UserBrief(
            id=item.owner.id,
            full_name=item.owner.full_name,
            email=item.owner.email,
        ),
        permissions=Permissions(**build_permissions(res, viewer, owner_id=item.owner_id)),
    )


def _conflict_error(
    db: Session,
    item_id: int,
    start: datetime,
    end: datetime,
    *,
    same_instant: bool,
) -> AppError:
    conflicts = availability.busy_intervals(db, item_id, start, end)
    suggestions = build_suggestions(db, item_id, start, end)
    message = (
        "این بازه همین لحظه توسط کاربر دیگری رزرو شد. یکی از بازه‌های پیشنهادی را انتخاب کنید."
        if same_instant
        else "این بازه قبلاً رزرو شده است. یکی از بازه‌های پیشنهادی را انتخاب کنید."
    )
    return AppError(
        "SLOT_CONFLICT",
        409,
        message,
        details={
            "item_id": item_id,
            "requested": {"start_at": serialize_utc(start), "end_at": serialize_utc(end)},
            "conflicts": [
                {"start_at": serialize_utc(s), "end_at": serialize_utc(e)} for s, e in conflicts
            ],
            "suggestions": suggestions,
        },
    )


# --------------------------------------------------------------------------- #
# Alternative slots (spec §6.4)
# --------------------------------------------------------------------------- #
def build_suggestions(
    db: Session,
    item_id: int,
    start: datetime,
    end: datetime,
    *,
    count: int | None = None,
) -> list[dict[str, str]]:
    """Up to N genuinely-free windows, closest to the requested one first.

    One query for the item's busy intervals, everything else is in-memory:
    no per-candidate round-trips.
    """
    settings = get_settings()
    want = count or settings.suggestion_count
    now = lifecycle.utcnow()
    duration = end - start
    horizon = now + timedelta(days=settings.booking_horizon_days)

    window_from = min(now, start) - timedelta(days=1)
    window_to = min(max(end, start) + timedelta(days=8), horizon)
    busy = availability.busy_intervals(db, item_id, window_from, window_to, limit=MAX_SUGGESTION_SCAN)
    busy = sorted(busy)

    candidates: list[tuple[datetime, datetime]] = []
    # 1) right after / right before each conflict
    for b_start, b_end in busy:
        candidates.append((b_end, b_end + duration))
        candidates.append((b_start - duration, b_start))
    # 2) same window, one day later / earlier
    candidates.append((start + timedelta(days=1), end + timedelta(days=1)))
    candidates.append((start - timedelta(days=1), end - timedelta(days=1)))
    # 3) the first free gap after "now" (covers "everything around is taken")
    cursor = now
    for b_start, b_end in busy:
        if b_start - cursor >= duration:
            candidates.append((cursor, cursor + duration))
        cursor = max(cursor, b_end)
        if len(candidates) >= want * 4:
            break
    candidates.append((cursor, cursor + duration))

    earliest = now - timedelta(minutes=settings.clock_skew_tolerance_minutes)
    picked: list[tuple[datetime, datetime]] = []
    seen: set[tuple[datetime, datetime]] = set()

    for cand_start, cand_end in candidates:
        if cand_end <= cand_start:
            continue
        if cand_start < earliest or cand_start > horizon:
            continue
        if (cand_start, cand_end) in seen:
            continue
        # Must not touch any blocking interval.
        if any(s < cand_end and cand_start < e for s, e in busy):
            continue
        seen.add((cand_start, cand_end))
        picked.append((cand_start, cand_end))

    picked.sort(key=lambda slot: abs((slot[0] - start).total_seconds()))
    return [
        {"start_at": serialize_utc(s), "end_at": serialize_utc(e)} for s, e in picked[:want]
    ]


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def create_reservation(db: Session, borrower: User, payload: ReservationCreate) -> Reservation:
    lifecycle.validate_window(payload.start_at, payload.end_at)

    # Layer 1: serialise every booking attempt of this item.
    item = db.execute(
        select(Item).where(Item.id == payload.item_id).with_for_update()
    ).scalar_one_or_none()

    if item is None:
        raise not_found("وسیله پیدا نشد.")
    if not item.is_active:
        raise AppError("ITEM_INACTIVE", 409, "این وسیله در حال حاضر قابل رزرو نیست.")
    if item.owner_id == borrower.id:
        raise AppError("CANNOT_BOOK_OWN_ITEM", 403, "نمی‌توانید وسیلهٔ خودتان را رزرو کنید.")

    # Free abandoned pending requests BEFORE judging availability.
    lifecycle.expire_stale_pending(db)

    # Layer 2: fast, readable check (a fresh statement → fresh snapshot).
    if availability.busy_intervals(db, item.id, payload.start_at, payload.end_at):
        raise _conflict_error(
            db, item.id, payload.start_at, payload.end_at, same_instant=False
        )

    item_id = item.id
    price = lifecycle.calc_price(item.price_per_day, payload.start_at, payload.end_at)

    res = Reservation(
        item_id=item_id,
        borrower_id=borrower.id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        status=ReservationStatus.PENDING,
        total_price=price,
        message=payload.message,
    )
    db.add(res)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()  # session is usable again after this
        if sqlstate(exc) != "23P01":  # not an exclusion violation
            logger.exception("reservation insert failed with an unexpected integrity error")
            raise
        # Layer 3 caught a race the check above could not see.
        raise _conflict_error(
            db, item_id, payload.start_at, payload.end_at, same_instant=True
        ) from exc

    return _fetch_full(db, res.id)


def transition(
    db: Session,
    reservation_id: int,
    user: User,
    action: str,
    *,
    decision_note: str | None = None,
    cancel_reason: str | None = None,
    returned_by: str | None = None,
) -> Reservation:
    """Apply one allowed state transition, atomically (spec §6.1)."""
    lifecycle.expire_stale_pending(db)

    row = db.execute(
        select(Reservation, Item.owner_id)
        .join(Item, Item.id == Reservation.item_id)
        .where(Reservation.id == reservation_id)
        .with_for_update(of=Reservation)
    ).one_or_none()

    if row is None:
        raise not_found("رزرو پیدا نشد.")
    res, owner_id = row

    require_party(res, user, owner_id)
    if action in lifecycle.LENDER_ONLY_ACTIONS:
        require_lender(res, user, lifecycle.ACTION_LABELS_FA.get(action, action), owner_id)

    current = res.status.value if isinstance(res.status, ReservationStatus) else str(res.status)
    target = lifecycle.transition_target(action, current)
    now = lifecycle.utcnow()

    res.status = ReservationStatus(target)
    if action == "approve":
        res.approved_at = now
        if decision_note is not None:
            res.decision_note = decision_note
    elif action == "reject":
        res.closed_at = now
        res.decision_note = decision_note
    elif action == "cancel":
        res.closed_at = now
        res.cancel_reason = cancel_reason
    elif action == "handover":
        res.handover_at = now
    elif action == "return":
        res.returned_at = now
        res.returned_by = returned_by

    db.commit()
    return _fetch_full(db, reservation_id)


# --------------------------------------------------------------------------- #
# Queries
# --------------------------------------------------------------------------- #
def get_reservation(db: Session, reservation_id: int, user: User) -> Reservation:
    res = db.execute(_full_query().where(Reservation.id == reservation_id)).unique().scalar_one_or_none()
    if res is None:
        raise not_found("رزرو پیدا نشد.")
    require_party(res, user)
    return res


def list_my_reservations(
    db: Session,
    user: User,
    *,
    role: str = "all",
    status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Reservation], int]:
    lifecycle.expire_stale_pending(db)

    owned_item_ids = select(Item.id).where(Item.owner_id == user.id)
    if role == "borrower":
        where = [Reservation.borrower_id == user.id]
    elif role == "lender":
        where = [Reservation.item_id.in_(owned_item_ids)]
    else:
        where = [
            or_(
                Reservation.borrower_id == user.id,
                Reservation.item_id.in_(owned_item_ids),
            )
        ]
    if status:
        where.append(Reservation.status == ReservationStatus(status))

    total = db.scalar(select(func.count()).select_from(Reservation).where(*where)) or 0

    rows = (
        db.execute(
            _full_query()
            .where(*where)
            .order_by(Reservation.created_at.desc(), Reservation.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        .unique()
        .scalars()
        .all()
    )
    return list(rows), int(total)
