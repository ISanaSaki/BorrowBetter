"""Shared enumerations and status metadata.

Changing any value here requires: PR + 2 approvals + updating
`docs/TEAM_SPEC.md` (section 3.6) and `frontend/src/constants.js`.
"""

from __future__ import annotations

from enum import Enum


class ItemCategory(str, Enum):
    TOOLS = "tools"
    ELECTRONICS = "electronics"
    OUTDOOR = "outdoor"
    HOUSEHOLD = "household"
    OTHER = "other"

    def __str__(self) -> str:  # pragma: no cover - human readable form
        return self.value


class ItemCondition(str, Enum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    WORN = "worn"

    def __str__(self) -> str:  # pragma: no cover
        return self.value


class SortOrder(str, Enum):
    NEWEST = "newest"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    RETURNED = "returned"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ReturnedBy(str, Enum):
    LENDER = "lender"
    BORROWER = "borrower"


# Display order for the frontend category chips.
CATEGORY_ORDER: tuple[ItemCategory, ...] = (
    ItemCategory.TOOLS,
    ItemCategory.ELECTRONICS,
    ItemCategory.OUTDOOR,
    ItemCategory.HOUSEHOLD,
    ItemCategory.OTHER,
)

# Statuses that occupy a slot in the calendar (spec 5.5 / 6.1).
BLOCKING_STATUSES: tuple[str, ...] = (
    ReservationStatus.PENDING.value,
    ReservationStatus.APPROVED.value,
    ReservationStatus.ACTIVE.value,
)

# Final states: no transition leaves them.
TERMINAL_STATUSES: tuple[str, ...] = (
    ReservationStatus.RETURNED.value,
    ReservationStatus.REJECTED.value,
    ReservationStatus.CANCELLED.value,
    ReservationStatus.EXPIRED.value,
)

# Human readable labels. The historical name is kept so booking and lifecycle
# messages stay consistent with the rest of the API surface.
STATUS_LABELS_FA: dict[str, str] = {
    ReservationStatus.PENDING.value: "Pending approval",
    ReservationStatus.APPROVED.value: "Approved",
    ReservationStatus.ACTIVE.value: "On loan",
    ReservationStatus.RETURNED.value: "Returned",
    ReservationStatus.REJECTED.value: "Rejected",
    ReservationStatus.CANCELLED.value: "Cancelled",
    ReservationStatus.EXPIRED.value: "Expired",
}


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    SLOT_CONFLICT = "SLOT_CONFLICT"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    CANNOT_BOOK_OWN_ITEM = "CANNOT_BOOK_OWN_ITEM"
    ITEM_INACTIVE = "ITEM_INACTIVE"
    ITEM_HAS_ACTIVE_RESERVATIONS = "ITEM_HAS_ACTIVE_RESERVATIONS"
    RANGE_TOO_WIDE = "RANGE_TOO_WIDE"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    def __str__(self) -> str:  # pragma: no cover
        return self.value
