"""Item catalog endpoints.

Owner: Asra (scaffold).  Contract: spec §7.3, §7.7 – §7.12.

The availability endpoint (`GET /items/{id}/availability`) is Sana's and lives in
`app/routers/reservations.py` because it reads reservation data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.constants import ItemCategory, ItemCondition
from app.core.errors import AppError
from app.models.user import User
from app.schemas.common import Envelope, Meta, PageEnvelope, UtcDatetime
from app.schemas.item import CategoryCount, ItemCreate, ItemDashboardOut, ItemOut, ItemUpdate
from app.services import items as items_service

router = APIRouter()


def _meta(page: int, limit: int, total: int) -> Meta:
    total_pages = (total + limit - 1) // limit if total else 0
    return Meta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
        has_next=page * limit < total,
    )


@router.get("/categories", response_model=Envelope[list[CategoryCount]], summary="Categories with item counts")
def categories(db: Session = Depends(get_db)) -> dict:
    return {"data": items_service.category_counts(db)}


@router.get("/items", response_model=PageEnvelope[ItemOut], summary="Browse the catalog")
def list_items(
    q: str | None = Query(default=None, max_length=100),
    category: ItemCategory | None = Query(default=None),
    condition: ItemCondition | None = Query(default=None),
    price_max: int | None = Query(default=None, ge=0),
    owner_id: int | None = Query(default=None, gt=0),
    available_from: UtcDatetime | None = Query(default=None),
    available_to: UtcDatetime | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(newest|price_asc|price_desc)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    if (available_from is None) != (available_to is None):
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "برای فیلتر تاریخ باید هر دو بازهٔ شروع و پایان ارسال شوند.",
            details={"fields": {"available_from": "باید همراه available_to باشد."}},
        )
    if available_from and available_to and available_to <= available_from:
        raise AppError(
            "VALIDATION_ERROR",
            422,
            "پایان بازه باید بعد از شروع آن باشد.",
            details={"fields": {"available_to": "باید بعد از available_from باشد."}},
        )

    rows, total = items_service.list_items(
        db,
        q=q,
        category=category,
        condition=condition,
        price_max=price_max,
        owner_id=owner_id,
        available_from=available_from,
        available_to=available_to,
        sort=sort,
        page=page,
        limit=limit,
    )
    return {"data": [items_service.serialize(item) for item in rows], "meta": _meta(page, limit, total)}


@router.post("/items", response_model=Envelope[ItemOut], status_code=201, summary="Create an item")
def create_item(
    payload: ItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    item = items_service.create_item(db, user, payload)
    return {"data": items_service.serialize(item)}


@router.get("/me/items", response_model=PageEnvelope[ItemDashboardOut], summary="Owner dashboard")
def my_items(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows, total = items_service.list_my_items(db, user, page=page, limit=limit)
    return {"data": rows, "meta": _meta(page, limit, total)}


@router.get("/items/{item_id}", response_model=Envelope[ItemOut], summary="Item details")
def get_item(item_id: int = Path(gt=0), db: Session = Depends(get_db)) -> dict:
    item = items_service.get_item(db, item_id)
    return {"data": items_service.serialize(item)}


@router.patch("/items/{item_id}", response_model=Envelope[ItemOut], summary="Update item (owner)")
def update_item(
    payload: ItemUpdate,
    item_id: int = Path(gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    item = items_service.update_item(db, item_id, user, payload)
    return {"data": items_service.serialize(item)}


@router.delete("/items/{item_id}", response_model=Envelope[dict], summary="Delete item (owner, soft delete)")
def delete_item(
    item_id: int = Path(gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return {"data": items_service.soft_delete_item(db, item_id, user)}
