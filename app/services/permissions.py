"""`permissions` block — the frontend renders buttons ONLY from this.

Owner: Sana (B).  Logic locked in spec §6.5.
"""

from __future__ import annotations

from app.core.constants import ReservationStatus
from app.core.errors import AppError
from app.models.reservation import Reservation
from app.models.user import User


def is_lender(res: Reservation, user: User, owner_id: int | None = None) -> bool:
    owner = owner_id if owner_id is not None else res.item.owner_id
    return owner == user.id


def is_borrower(res: Reservation, user: User) -> bool:
    return res.borrower_id == user.id


def build_permissions(
    res: Reservation,
    user: User,
    owner_id: int | None = None,
) -> dict[str, bool]:
    """`owner_id` lets the caller skip a lazy load on the item relation."""
    lender = is_lender(res, user, owner_id)
    borrower = is_borrower(res, user)
    status = res.status.value if isinstance(res.status, ReservationStatus) else str(res.status)

    return {
        "can_approve": lender and status == ReservationStatus.PENDING.value,
        "can_reject": lender and status == ReservationStatus.PENDING.value,
        "can_cancel": (lender or borrower)
        and status in (ReservationStatus.PENDING.value, ReservationStatus.APPROVED.value),
        "can_handover": lender and status == ReservationStatus.APPROVED.value,
        "can_return": (lender or borrower) and status == ReservationStatus.ACTIVE.value,
    }


def require_party(res: Reservation, user: User, owner_id: int | None = None) -> None:
    """Only the borrower or the item owner may see/touch a reservation."""
    if not (is_borrower(res, user) or is_lender(res, user, owner_id)):
        raise AppError("FORBIDDEN", 403, "شما به این رزرو دسترسی ندارید.")


def require_lender(res: Reservation, user: User, action_label: str, owner_id: int | None = None) -> None:
    if not is_lender(res, user, owner_id):
        raise AppError(
            "FORBIDDEN",
            403,
            f"فقط صاحب وسیله می‌تواند این درخواست را {action_label} کند.",
        )
