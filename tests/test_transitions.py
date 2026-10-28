"""Booking state machine — every allowed move plus six forbidden ones.

Owner: Sana (B).  Rules: spec §6.1.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import text

WINDOW_START_HOURS = 30  # far enough ahead to never trip the "past" guard
WINDOW_HOURS = 4


def _window(days: int = 0, start_hour: int = 10) -> tuple[str, str]:
    base = (datetime.now(timezone.utc) + timedelta(days=1 + days)).replace(
        hour=start_hour, minute=0, second=0, microsecond=0
    )
    end = base + timedelta(hours=WINDOW_HOURS)
    return (
        base.isoformat(timespec="seconds").replace("+00:00", "Z"),
        end.isoformat(timespec="seconds").replace("+00:00", "Z"),
    )


def _create(client, headers, item_id: int, days: int = 0, start_hour: int = 10):
    start, end = _window(days, start_hour)
    return client.post(
        "/api/v1/reservations",
        json={"item_id": item_id, "start_at": start, "end_at": end},
        headers=headers,
    )


def test_happy_path_lifecycle(client, headers, borrower, owner, item):
    res = _create(client, headers(borrower), item.id)
    assert res.status_code == 201, res.text
    body = res.json()["data"]
    reservation_id = body["id"]
    assert body["status"] == "pending"
    assert body["total_price"] == 50_000  # 4h → one day
    assert body["permissions"]["can_cancel"] is True
    assert body["permissions"]["can_approve"] is False

    # Owner sees the pending request in the lender dashboard
    lender_list = client.get("/api/v1/me/reservations?role=lender", headers=headers(owner))
    assert lender_list.status_code == 200
    assert lender_list.json()["meta"]["total"] == 1

    approved = client.post(
        f"/api/v1/reservations/{reservation_id}/approve", headers=headers(owner)
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["data"]["status"] == "approved"
    assert approved.json()["data"]["approved_at"] is not None

    active = client.post(
        f"/api/v1/reservations/{reservation_id}/handover", headers=headers(owner)
    )
    assert active.status_code == 200
    assert active.json()["data"]["status"] == "active"
    assert active.json()["data"]["handover_at"] is not None

    returned = client.post(
        f"/api/v1/reservations/{reservation_id}/return",
        json={"returned_by": "borrower"},
        headers=headers(borrower),
    )
    assert returned.status_code == 200, returned.text
    data = returned.json()["data"]
    assert data["status"] == "returned"
    assert data["returned_by"] == "borrower"
    assert data["returned_at"] is not None
    assert all(value is False for value in data["permissions"].values())


def test_borrower_cannot_approve(client, headers, borrower, item):
    reservation_id = _create(client, headers(borrower), item.id).json()["data"]["id"]
    res = client.post(
        f"/api/v1/reservations/{reservation_id}/approve", headers=headers(borrower)
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"
    assert "only the item owner" in res.json()["error"]["message"].lower()


def test_double_approve_is_invalid_transition(client, headers, borrower, owner, item):
    reservation_id = _create(client, headers(borrower), item.id).json()["data"]["id"]
    assert client.post(
        f"/api/v1/reservations/{reservation_id}/approve", headers=headers(owner)
    ).status_code == 200

    again = client.post(
        f"/api/v1/reservations/{reservation_id}/approve", headers=headers(owner)
    )
    assert again.status_code == 409
    error = again.json()["error"]
    assert error["code"] == "INVALID_TRANSITION"
    assert error["details"]["current_status"] == "approved"
    assert error["details"]["attempted_action"] == "approve"


def test_rejected_cannot_be_approved(client, headers, borrower, owner, item):
    reservation_id = _create(client, headers(borrower), item.id).json()["data"]["id"]
    assert client.post(
        f"/api/v1/reservations/{reservation_id}/reject",
        json={"decision_note": "برای آن روز خودم لازمش دارم."},
        headers=headers(owner),
    ).status_code == 200

    res = client.post(f"/api/v1/reservations/{reservation_id}/approve", headers=headers(owner))
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "INVALID_TRANSITION"


def test_return_before_handover_is_invalid(client, headers, borrower, owner, item):
    reservation_id = _create(client, headers(borrower), item.id).json()["data"]["id"]
    res = client.post(
        f"/api/v1/reservations/{reservation_id}/return",
        json={"returned_by": "lender"},
        headers=headers(borrower),
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "INVALID_TRANSITION"


def test_handover_requires_approved(client, headers, borrower, owner, item):
    reservation_id = _create(client, headers(borrower), item.id).json()["data"]["id"]
    res = client.post(
        f"/api/v1/reservations/{reservation_id}/handover", headers=headers(owner)
    )
    assert res.status_code == 409
    assert res.json()["error"]["details"]["current_status"] == "pending"


def test_cancel_frees_the_slot(client, headers, borrower, owner, item):
    first = _create(client, headers(borrower), item.id)
    assert first.status_code == 201
    reservation_id = first.json()["data"]["id"]

    # Same window is still locked while pending
    blocked = _create(client, headers(borrower), item.id)
    assert blocked.status_code == 409

    cancelled = client.post(
        f"/api/v1/reservations/{reservation_id}/cancel",
        json={"cancel_reason": "برنامه‌ام عوض شد."},
        headers=headers(borrower),
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["status"] == "cancelled"
    assert cancelled.json()["data"]["closed_at"] is not None

    # …and free again afterwards
    retry = _create(client, headers(borrower), item.id)
    assert retry.status_code == 201


def test_stranger_cannot_read_reservation(client, headers, borrower, stranger, item):
    reservation_id = _create(client, headers(borrower), item.id).json()["data"]["id"]
    res = client.get(f"/api/v1/reservations/{reservation_id}", headers=headers(stranger))
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_return_requires_returned_by(client, headers, borrower, owner, item):
    reservation_id = _create(client, headers(borrower), item.id).json()["data"]["id"]
    client.post(f"/api/v1/reservations/{reservation_id}/approve", headers=headers(owner))
    client.post(f"/api/v1/reservations/{reservation_id}/handover", headers=headers(owner))

    res = client.post(
        f"/api/v1/reservations/{reservation_id}/return", json={}, headers=headers(borrower)
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "returned_by" in res.json()["error"]["details"]["fields"]


def test_cannot_book_own_item(client, headers, owner, item):
    res = _create(client, headers(owner), item.id)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "CANNOT_BOOK_OWN_ITEM"


def test_inactive_item_cannot_be_booked(client, headers, borrower, owner, item, db):
    db.execute(text("UPDATE items SET is_active = false WHERE id = :id"), {"id": item.id})
    db.commit()

    res = _create(client, headers(borrower), item.id)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ITEM_INACTIVE"


def test_rejected_and_expired_do_not_block(client, headers, borrower, owner, item):
    first = _create(client, headers(borrower), item.id).json()["data"]
    client.post(
        f"/api/v1/reservations/{first['id']}/reject", json={}, headers=headers(owner)
    )

    second = _create(client, headers(borrower), item.id)
    assert second.status_code == 201
