"""Item catalog: list/filter/sort, CRUD, dashboards.

Owner: Asra (scaffold).

Date filtering goes through `availability.free_item_ids()` — this module never
writes a query against `reservations` (spec §2.3).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import ItemCategory, ItemCondition
from app.core.errors import AppError, forbidden, not_found
from app.models.item import Item
from app.models.user import User
from app.schemas.item import CategoryCount, ItemCreate, ItemDashboardOut, ItemOut, ItemUpdate, OwnerBrief
from app.services import availability


def serialize(item: Item) -> ItemOut:
    return ItemOut(
        id=item.id,
        owner_id=item.owner_id,
        title=item.title,
        description=item.description,
        category=item.category,
        condition=item.condition,
        price_per_day=item.price_per_day,
        image_url=item.image_url,
        is_active=item.is_active,
        owner=OwnerBrief(id=item.owner.id, full_name=item.owner.full_name),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _filters(
    *,
    q: str | None = None,
    category: ItemCategory | None = None,
    condition: ItemCondition | None = None,
    price_max: int | None = None,
    owner_id: int | None = None,
    active_only: bool = True,
) -> list:
    conds: list = []
    if active_only:
        conds.append(Item.is_active.is_(True))
    if q:
        pattern = f"%{q.strip()}%"
        conds.append(or_(Item.title.ilike(pattern), Item.description.ilike(pattern)))
    if category is not None:
        conds.append(Item.category == category)
    if condition is not None:
        conds.append(Item.condition == condition)
    if price_max is not None:
        conds.append(Item.price_per_day <= price_max)
    if owner_id is not None:
        conds.append(Item.owner_id == owner_id)
    return conds


def list_items(
    db: Session,
    *,
    q: str | None = None,
    category: ItemCategory | None = None,
    condition: ItemCondition | None = None,
    price_max: int | None = None,
    owner_id: int | None = None,
    available_from: datetime | None = None,
    available_to: datetime | None = None,
    sort: str = "newest",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Item], int]:
    conds = _filters(
        q=q,
        category=category,
        condition=condition,
        price_max=price_max,
        owner_id=owner_id,
    )

    if available_from is not None and available_to is not None:
        candidate_ids = db.scalars(select(Item.id).where(*conds)).all()
        free = availability.free_item_ids(db, list(candidate_ids), available_from, available_to)
        if not free:
            return [], 0
        conds.append(Item.id.in_(free))

    total = db.scalar(select(func.count()).select_from(Item).where(*conds)) or 0

    order = {
        "price_asc": (Item.price_per_day.asc(), Item.id.asc()),
        "price_desc": (Item.price_per_day.desc(), Item.id.desc()),
    }.get(sort, (Item.created_at.desc(), Item.id.desc()))

    rows = (
        db.execute(
            select(Item)
            .options(joinedload(Item.owner))
            .where(*conds)
            .order_by(*order)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        .unique()
        .scalars()
        .all()
    )
    return list(rows), int(total)


def get_item(db: Session, item_id: int) -> Item:
    item = db.execute(
        select(Item).options(joinedload(Item.owner)).where(Item.id == item_id)
    ).unique().scalar_one_or_none()
    if item is None or not item.is_active:
        raise not_found("وسیله پیدا نشد.")
    return item


def create_item(db: Session, owner: User, payload: ItemCreate) -> Item:
    item = Item(
        owner_id=owner.id,
        title=payload.title.strip(),
        description=payload.description or "",
        category=payload.category,
        condition=payload.condition,
        price_per_day=payload.price_per_day,
        image_url=payload.image_url,
    )
    db.add(item)
    db.commit()
    return get_item(db, item.id)


def _owned_item(db: Session, item_id: int, user: User) -> Item:
    item = db.execute(
        select(Item).options(joinedload(Item.owner)).where(Item.id == item_id)
    ).unique().scalar_one_or_none()
    if item is None:
        raise not_found("وسیله پیدا نشد.")
    if item.owner_id != user.id:
        raise forbidden("فقط صاحب وسیله می‌تواند آن را تغییر دهد.")
    return item


def update_item(db: Session, item_id: int, user: User, payload: ItemUpdate) -> Item:
    item = _owned_item(db, item_id, user)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    db.commit()
    # Re-read without the `is_active` filter: deactivating an item is a valid
    # PATCH and must not turn into a 404 for the owner.
    refreshed = db.execute(
        select(Item).options(joinedload(Item.owner)).where(Item.id == item_id)
    ).unique().scalar_one()
    return refreshed


def soft_delete_item(db: Session, item_id: int, user: User) -> dict:
    item = _owned_item(db, item_id, user)
    if availability.has_active_reservations(db, item_id):
        raise AppError(
            "ITEM_HAS_ACTIVE_RESERVATIONS",
            409,
            "ابتدا رزروهای فعال این وسیله را تعیین تکلیف کنید.",
        )
    item.is_active = False
    db.commit()
    return {"id": item.id, "is_active": False}


def list_my_items(db: Session, user: User, *, page: int = 1, limit: int = 20) -> tuple[list[ItemDashboardOut], int]:
    conds = [Item.owner_id == user.id]
    total = db.scalar(select(func.count()).select_from(Item).where(*conds)) or 0

    rows = (
        db.execute(
            select(Item)
            .options(joinedload(Item.owner))
            .where(*conds)
            .order_by(Item.created_at.desc(), Item.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        .unique()
        .scalars()
        .all()
    )
    counts = availability.reservation_counts(db, [item.id for item in rows])

    out: list[ItemDashboardOut] = []
    for item in rows:
        base = serialize(item).model_dump()
        active_count, pending_count = counts.get(item.id, (0, 0))
        out.append(
            ItemDashboardOut(
                **base,
                active_reservations_count=active_count,
                pending_requests_count=pending_count,
            )
        )
    return out, int(total)


def category_counts(db: Session) -> list[CategoryCount]:
    rows = db.execute(
        select(Item.category, func.count())
        .where(Item.is_active.is_(True))
        .group_by(Item.category)
    ).all()
    counts = {category: count for category, count in rows}
    return [
        CategoryCount(value=category, count=int(counts.get(category, 0)))
        for category in ItemCategory
    ]
