"""Reservation schemas — request bodies and the exact response shape.

Owner: Sana (B).  Contract: spec §4.2 (`reservation`) and §7.14.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import ItemCategory, ItemCondition, ReservationStatus, ReturnedBy
from app.schemas.common import UtcDatetime


class ReservationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: int = Field(gt=0)
    start_at: UtcDatetime
    end_at: UtcDatetime
    message: str | None = Field(default=None, max_length=500)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_note: str | None = Field(default=None, max_length=500)


class CancelRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cancel_reason: str | None = Field(default=None, max_length=500)


class ReturnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    returned_by: ReturnedBy


class ItemBrief(BaseModel):
    id: int
    title: str
    image_url: str | None
    price_per_day: int
    owner_id: int
    category: ItemCategory
    condition: ItemCondition


class UserBrief(BaseModel):
    id: int
    full_name: str
    email: str


class Permissions(BaseModel):
    can_approve: bool
    can_reject: bool
    can_cancel: bool
    can_handover: bool
    can_return: bool


class ReservationOut(BaseModel):
    id: int
    item_id: int
    borrower_id: int

    start_at: UtcDatetime
    end_at: UtcDatetime

    status: ReservationStatus
    total_price: int

    message: str | None
    decision_note: str | None
    cancel_reason: str | None
    returned_by: ReturnedBy | None

    created_at: UtcDatetime
    updated_at: UtcDatetime
    approved_at: UtcDatetime | None
    handover_at: UtcDatetime | None
    returned_at: UtcDatetime | None
    closed_at: UtcDatetime | None

    item: ItemBrief
    borrower: UserBrief
    lender: UserBrief
    permissions: Permissions


class BusySlot(BaseModel):
    start_at: UtcDatetime
    end_at: UtcDatetime


class AvailabilityOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    item_id: int
    from_: UtcDatetime = Field(alias="from")
    to: UtcDatetime
    is_available: bool
    min_duration_hours: int
    max_duration_days: int
    busy: list[BusySlot]
    server_time: UtcDatetime
