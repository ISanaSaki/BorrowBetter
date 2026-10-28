"""Item catalog (Backend A)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, DbSession, get_owned_item
from app.core.constants import ItemCategory, ItemCondition, SortOrder
from app.models.item import Item
from app.schemas.common import DataResponse, DeactivateOut, ErrorResponse, Page, PageMeta
from app.schemas.item import CategoryOut, ItemCreate, ItemOut, ItemUpdate, MyItemOut
from app.services import items as items_service

catalog_router = APIRouter(tags=["catalog"])
router = APIRouter(prefix="/items", tags=["items"])
me_router = APIRouter(prefix="/me", tags=["me"])


# --------------------------------------------------------------------------- #
# Catalog
# --------------------------------------------------------------------------- #
@catalog_router.get(
    "/categories",
    response_model=DataResponse[list[CategoryOut]],
    summary="Categories with active item counts",
)
def list_categories(db: DbSession) -> DataResponse[list[CategoryOut]]:
    return DataResponse[list[CategoryOut]](
        data=[
            CategoryOut(value=value, count=count)
            for value, count in items_service.category_counts(db)
        ]
    )


@router.get(
    "",
    response_model=Page[ItemOut],
    summary="List items with search, filters and pagination",
    description=(
        "Only active items are returned. When `available_from` and `available_to` are "
        "provided, only items free for the **entire** range are returned."
    ),
    responses={422: {"model": ErrorResponse, "description": "Invalid query parameters"}},
)
def list_items(
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100, description="Match title or description")] = None,
    category: Annotated[ItemCategory | None, Query(description="Item category")] = None,
    condition: Annotated[ItemCondition | None, Query(description="Item condition")] = None,
    price_max: Annotated[int | None, Query(ge=0, description="Maximum daily price")] = None,
    owner_id: Annotated[int | None, Query(ge=1, description="Items of a specific owner")] = None,
    sort: Annotated[SortOrder, Query(description="Result ordering")] = SortOrder.NEWEST,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    available_from: Annotated[datetime | None, Query(description="Range start (ISO-8601 UTC)")] = None,
    available_to: Annotated[datetime | None, Query(description="Range end (ISO-8601 UTC)")] = None,
) -> Page[ItemOut]:
    found, total = items_service.list_items(
        db,
        q=q,
        category=category,
        condition=condition,
        price_max=price_max,
        owner_id=owner_id,
        sort=sort,
        page=page,
        limit=limit,
        available_from=available_from,
        available_to=available_to,
    )
    return Page[ItemOut](
        data=[ItemOut.model_validate(item) for item in found],
        meta=PageMeta.build(page, limit, total),
    )


@router.post(
    "",
    response_model=DataResponse[ItemOut],
    status_code=status.HTTP_201_CREATED,
    summary="Create an item",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid token"},
        422: {"model": ErrorResponse, "description": "Invalid input"},
    },
)
def create_item(payload: ItemCreate, db: DbSession, user: CurrentUser) -> DataResponse[ItemOut]:
    item = items_service.create_item(db, user, payload)
    return DataResponse[ItemOut](data=ItemOut.model_validate(item))


@router.get(
    "/{item_id}",
    response_model=DataResponse[ItemOut],
    summary="Get a single item",
    responses={404: {"model": ErrorResponse, "description": "Item not found"}},
)
def get_item(item_id: int, db: DbSession) -> DataResponse[ItemOut]:
    item = items_service.get_item(db, item_id, only_active=True)
    return DataResponse[ItemOut](data=ItemOut.model_validate(item))


@router.patch(
    "/{item_id}",
    response_model=DataResponse[ItemOut],
    summary="Update an item (owner only)",
    responses={
        403: {"model": ErrorResponse, "description": "Not the owner"},
        404: {"model": ErrorResponse, "description": "Item not found"},
        422: {"model": ErrorResponse, "description": "Invalid input"},
    },
)
def update_item(
    payload: ItemUpdate,
    item: Annotated[Item, Depends(get_owned_item)],
    db: DbSession,
) -> DataResponse[ItemOut]:
    updated = items_service.update_item(db, item, payload)
    return DataResponse[ItemOut](data=ItemOut.model_validate(updated))


@router.delete(
    "/{item_id}",
    response_model=DataResponse[DeactivateOut],
    summary="Soft delete an item (owner only)",
    responses={
        403: {"model": ErrorResponse, "description": "Not the owner"},
        404: {"model": ErrorResponse, "description": "Item not found"},
        409: {"model": ErrorResponse, "description": "Item has active reservations"},
    },
)
def delete_item(
    item: Annotated[Item, Depends(get_owned_item)],
    db: DbSession,
) -> DataResponse[DeactivateOut]:
    deleted = items_service.deactivate_item(db, item)
    return DataResponse[DeactivateOut](data=DeactivateOut(id=deleted.id, is_active=deleted.is_active))


# --------------------------------------------------------------------------- #
# Owner dashboard
# --------------------------------------------------------------------------- #
@me_router.get(
    "/items",
    response_model=Page[MyItemOut],
    summary="My items with reservation counters",
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)
def my_items(
    db: DbSession,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> Page[MyItemOut]:
    rows = items_service.list_owner_items(db, user)
    start = (page - 1) * limit
    window = rows[start : start + limit]

    data = []
    for item, active_count, pending_count in window:
        payload = MyItemOut.model_validate(item)
        data.append(
            payload.model_copy(
                update={
                    "active_reservations_count": active_count,
                    "pending_requests_count": pending_count,
                }
            )
        )
    return Page[MyItemOut](data=data, meta=PageMeta.build(page, limit, len(rows)))
