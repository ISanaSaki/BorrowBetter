"""Reservation endpoints — the booking engine's HTTP surface.

Owner: Sana (B).  Contract: spec §7.14 – §7.21, plus the availability endpoint
(§7.13), which lives here because `app/routers/items.py` belongs to Asra.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.constants import ReservationStatus
from app.models.user import User
from app.schemas.common import Envelope, Meta, PageEnvelope
from app.schemas.reservation import (
    AvailabilityOut,
    CancelRequest,
    DecisionRequest,
    ReservationCreate,
    ReservationOut,
    ReturnRequest,
)
from app.services import availability as availability_service
from app.services import booking

router = APIRouter(tags=["booking"])


@router.get(
    "/items/{item_id}/availability",
    response_model=Envelope[AvailabilityOut],
    summary="Busy slots for an item",
)
def get_item_availability(
    item_id: int = Path(gt=0),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    data = availability_service.get_availability(db, item_id, from_, to)
    return {"data": data}


@router.post(
    "/reservations",
    response_model=Envelope[ReservationOut],
    status_code=201,
    summary="Request a reservation",
)
def create_reservation(
    payload: ReservationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    res = booking.create_reservation(db, user, payload)
    return {"data": booking.serialize(res, user)}


@router.get(
    "/me/reservations",
    response_model=PageEnvelope[ReservationOut],
    summary="My reservations (borrower or lender)",
)
def list_my_reservations(
    role: str = Query(default="all", pattern="^(borrower|lender|all)$"),
    status: ReservationStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows, total = booking.list_my_reservations(
        db,
        user,
        role=role,
        status=status.value if status else None,
        page=page,
        limit=limit,
    )
    total_pages = (total + limit - 1) // limit if total else 0
    return {
        "data": [booking.serialize(res, user) for res in rows],
        "meta": Meta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
            has_next=page * limit < total,
        ),
    }


@router.get(
    "/reservations/{reservation_id}",
    response_model=Envelope[ReservationOut],
    summary="Reservation details",
)
def get_reservation(
    reservation_id: int = Path(gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    res = booking.get_reservation(db, reservation_id, user)
    return {"data": booking.serialize(res, user)}


@router.post(
    "/reservations/{reservation_id}/approve",
    response_model=Envelope[ReservationOut],
    summary="Approve request (lender)",
)
def approve(
    payload: DecisionRequest | None = Body(default=None),
    reservation_id: int = Path(gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    res = booking.transition(
        db,
        reservation_id,
        user,
        "approve",
        decision_note=payload.decision_note if payload else None,
    )
    return {"data": booking.serialize(res, user)}


@router.post(
    "/reservations/{reservation_id}/reject",
    response_model=Envelope[ReservationOut],
    summary="Reject request (lender)",
)
def reject(
    payload: DecisionRequest | None = Body(default=None),
    reservation_id: int = Path(gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    res = booking.transition(
        db,
        reservation_id,
        user,
        "reject",
        decision_note=payload.decision_note if payload else None,
    )
    return {"data": booking.serialize(res, user)}


@router.post(
    "/reservations/{reservation_id}/cancel",
    response_model=Envelope[ReservationOut],
    summary="Cancel reservation (both parties)",
)
def cancel(
    payload: CancelRequest | None = Body(default=None),
    reservation_id: int = Path(gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    res = booking.transition(
        db,
        reservation_id,
        user,
        "cancel",
        cancel_reason=payload.cancel_reason if payload else None,
    )
    return {"data": booking.serialize(res, user)}


@router.post(
    "/reservations/{reservation_id}/handover",
    response_model=Envelope[ReservationOut],
    summary="Mark as handed over (lender)",
)
def handover(
    reservation_id: int = Path(gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    res = booking.transition(db, reservation_id, user, "handover")
    return {"data": booking.serialize(res, user)}


@router.post(
    "/reservations/{reservation_id}/return",
    response_model=Envelope[ReservationOut],
    summary="Mark as returned (both parties)",
)
def return_item(
    payload: ReturnRequest,
    reservation_id: int = Path(gt=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    res = booking.transition(
        db,
        reservation_id,
        user,
        "return",
        returned_by=payload.returned_by.value,
    )
    return {"data": booking.serialize(res, user)}
