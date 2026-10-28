"""Catalog service (Backend A).

Hard rule: this module never queries the `reservations` table. Anything related
to bookings is provided by `app/services/availability.py` (owned by Backend B).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.core.constants import CATEGORY_ORDER, ItemCategory, ItemCondition, SortOrder
from app.core.errors import AppError, NotFound
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate
from app.services.availability import (
    free_item_ids,
    has_active_reservations,
    reservation_counts,
)
from app.services.search import text_filter

MAX_FILTER_CANDIDATES = 5000


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _apply_sort(stmt: Select, sort: SortOrder) -> Select:
    if sort is SortOrder.PRICE_ASC:
        return stmt.order_by(Item.price_per_day.asc(), Item.id.asc())
    if sort is SortOrder.PRICE_DESC:
        return stmt.order_by(Item.price_per_day.desc(), Item.id.desc())
    return stmt.order_by(Item.created_at.desc(), Item.id.desc())


def get_item(db: Session, item_id: int, *, only_active: bool = True) -> Item:
    stmt = select(Item).where(Item.id == item_id)
    if only_active:
        stmt = stmt.where(Item.is_active.is_(True))
    item = db.execute(stmt).unique().scalar_one_or_none()
    if item is None:
        raise NotFound("Item not found or no longer available.")
    return item


def list_items(
    db: Session,
    *,
    q: str | None = None,
    category: ItemCategory | None = None,
    condition: ItemCondition | None = None,
    price_max: int | None = None,
    owner_id: int | None = None,
    sort: SortOrder = SortOrder.NEWEST,
    page: int = 1,
    limit: int = 20,
    available_from: datetime | None = None,
    available_to: datetime | None = None,
) -> tuple[list[Item], int]:
    conditions = [Item.is_active.is_(True)]

    if category is not None:
        conditions.append(Item.category == category)
    if condition is not None:
        conditions.append(Item.condition == condition)
    if price_max is not None:
        conditions.append(Item.price_per_day <= price_max)
    if owner_id is not None:
        conditions.append(Item.owner_id == owner_id)

    clause = text_filter(q)
    if clause is not None:
        conditions.append(clause)

    start, end = _as_utc(available_from), _as_utc(available_to)
    if (start is None) != (end is None):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "Both available_from and available_to are required for a date filter.",
            {"fields": {"available_from": "Must be sent together with available_to."}},
        )
    if start is not None and end is not None:
        if start >= end:
            raise AppError(
                "VALIDATION_ERROR",
                422,
                "Invalid time range: start must be before end.",
                {"fields": {"available_to": "Must be after available_from."}},
            )
        # Backend A does not query reservations directly; it calls Backend B.
        candidate_ids = list(
            db.scalars(select(Item.id).where(*conditions).limit(MAX_FILTER_CANDIDATES)).all()
        )
        free_ids = free_item_ids(db, candidate_ids, start, end)
        if not free_ids:
            return [], 0
        conditions.append(Item.id.in_(free_ids))

    total = db.scalar(select(func.count(Item.id)).where(*conditions)) or 0

    stmt = _apply_sort(select(Item).where(*conditions), sort)
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    items = list(db.execute(stmt).unique().scalars().all())
    return items, int(total)


def create_item(db: Session, owner: User, payload: ItemCreate) -> Item:
    item = Item(owner_id=owner.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item: Item, payload: ItemUpdate) -> Item:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def deactivate_item(db: Session, item: Item) -> Item:
    if has_active_reservations(db, item.id):
        raise AppError(
            "ITEM_HAS_ACTIVE_RESERVATIONS",
            409,
            "This item has active reservations. Resolve them before deleting it.",
            {"item_id": item.id},
        )
    item.is_active = False
    db.commit()
    db.refresh(item)
    return item


def list_owner_items(db: Session, owner: User) -> list[tuple[Item, int, int]]:
    """Owner items plus (active reservations, pending requests) from Backend B."""
    items = list(
        db.execute(
            select(Item)
            .where(Item.owner_id == owner.id)
            .order_by(Item.is_active.desc(), Item.created_at.desc(), Item.id.desc())
        )
        .unique()
        .scalars()
        .all()
    )
    counts = reservation_counts(db, [item.id for item in items])
    return [(item, *counts.get(item.id, (0, 0))) for item in items]


def category_counts(db: Session) -> list[tuple[ItemCategory, int]]:
    """All categories are returned (even empty ones) so UI chips stay stable."""
    rows = db.execute(
        select(Item.category, func.count(Item.id))
        .where(Item.is_active.is_(True))
        .group_by(Item.category)
    ).all()
    found = {category: int(count) for category, count in rows}
    return [(category, found.get(category, 0)) for category in CATEGORY_ORDER]
