from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import ItemCategory, ItemCondition
from app.schemas.common import UtcDateTime
from app.schemas.user import UserBrief

MAX_DESCRIPTION = 2000


class ItemBase(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=120, examples=["Bosch electric drill"])
    description: str = Field(default="", max_length=MAX_DESCRIPTION)
    category: ItemCategory = Field(examples=["tools"])
    condition: ItemCondition = ItemCondition.GOOD
    price_per_day: int = Field(default=0, ge=0, le=100_000_000, examples=[50000])
    image_url: str | None = Field(
        default=None, max_length=500, examples=["https://picsum.photos/seed/drill/600/400"]
    )

    @field_validator("image_url")
    @classmethod
    def _valid_image_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.startswith(("http://", "https://")):
            raise ValueError("Image URL must start with http:// or https://.")
        return value


class ItemCreate(ItemBase):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "title": "Bosch electric drill",
                "description": "750W hammer drill with a full bit set.",
                "category": "tools",
                "condition": "good",
                "price_per_day": 50000,
                "image_url": "https://picsum.photos/seed/drill/600/400",
            }
        },
    )


class ItemUpdate(BaseModel):
    """All fields optional; omitted fields stay unchanged."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=MAX_DESCRIPTION)
    category: ItemCategory | None = None
    condition: ItemCondition | None = None
    price_per_day: int | None = Field(default=None, ge=0, le=100_000_000)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None

    @field_validator("image_url")
    @classmethod
    def _valid_image_url(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if not value.startswith(("http://", "https://")):
            raise ValueError("Image URL must start with http:// or https://.")
        return value

    @model_validator(mode="after")
    def _at_least_one_field(self) -> "ItemUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        return self


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    title: str
    description: str
    category: ItemCategory
    condition: ItemCondition
    price_per_day: int
    image_url: str | None
    is_active: bool
    owner: UserBrief
    created_at: UtcDateTime
    updated_at: UtcDateTime


class MyItemOut(ItemOut):
    """Only for `GET /me/items`; counters come from Backend B functions."""

    active_reservations_count: int = Field(default=0, ge=0)
    pending_requests_count: int = Field(default=0, ge=0)


class CategoryOut(BaseModel):
    value: ItemCategory
    count: int = Field(ge=0)
