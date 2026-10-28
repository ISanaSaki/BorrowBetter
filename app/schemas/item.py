"""Item schemas.

Owner: Asra (scaffold).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ItemCategory, ItemCondition
from app.schemas.common import UtcDatetime


class OwnerBrief(BaseModel):
    id: int
    full_name: str


class ItemOut(BaseModel):
    id: int
    owner_id: int
    title: str
    description: str
    category: ItemCategory
    condition: ItemCondition
    price_per_day: int
    image_url: str | None
    is_active: bool
    owner: OwnerBrief
    created_at: UtcDatetime
    updated_at: UtcDatetime


class ItemDashboardOut(ItemOut):
    active_reservations_count: int = 0
    pending_requests_count: int = 0


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2000)
    category: ItemCategory
    condition: ItemCondition = ItemCondition.GOOD
    price_per_day: int = Field(default=0, ge=0, le=100_000_000)
    image_url: str | None = Field(default=None, max_length=500)


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    category: ItemCategory | None = None
    condition: ItemCondition | None = None
    price_per_day: int | None = Field(default=None, ge=0, le=100_000_000)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class CategoryCount(BaseModel):
    value: ItemCategory
    count: int
