"""Shared enums — source of truth for DB types, API values and the frontend.

Owner: Asra. Change requires a contract change (spec §4.3) + 2 approvals.
"""

from __future__ import annotations

from enum import Enum


class ReservationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    RETURNED = "returned"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ItemCategory(str, Enum):
    TOOLS = "tools"
    ELECTRONICS = "electronics"
    OUTDOOR = "outdoor"
    HOUSEHOLD = "household"
    OTHER = "other"


class ItemCondition(str, Enum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    WORN = "worn"


class ReturnedBy(str, Enum):
    LENDER = "lender"
    BORROWER = "borrower"


# Statuses that occupy a slot in the calendar (spec §5.5 / §6.1).
BLOCKING_STATUSES: tuple[str, ...] = (
    ReservationStatus.PENDING.value,
    ReservationStatus.APPROVED.value,
    ReservationStatus.ACTIVE.value,
)

# Statuses that are final; no transition leaves them.
TERMINAL_STATUSES: tuple[str, ...] = (
    ReservationStatus.RETURNED.value,
    ReservationStatus.REJECTED.value,
    ReservationStatus.CANCELLED.value,
    ReservationStatus.EXPIRED.value,
)

STATUS_LABELS_FA: dict[str, str] = {
    ReservationStatus.PENDING.value: "در انتظار تأیید",
    ReservationStatus.APPROVED.value: "تأیید شده",
    ReservationStatus.ACTIVE.value: "در حال امانت",
    ReservationStatus.RETURNED.value: "بازگشت داده شده",
    ReservationStatus.REJECTED.value: "رد شده",
    ReservationStatus.CANCELLED.value: "لغو شده",
    ReservationStatus.EXPIRED.value: "منقضی شده",
}
