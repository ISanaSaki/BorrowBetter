"""Concurrency — the heart of the demo (spec §10.2).

Owner: Sana (B).  Fifty different borrowers hit the same item and the same slot
at the same instant: PostgreSQL must approve exactly one and give the other 49 a
readable 409 with real alternatives.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.services import booking

BLOCKING = "('pending','approved','active')"


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _window(days: int = 1, hour: int = 10, hours: int = 4) -> tuple[datetime, datetime]:
    start = (datetime.now(timezone.utc) + timedelta(days=days)).replace(
        hour=hour, minute=0, second=0, microsecond=0
    )
    return start, start + timedelta(hours=hours)


def _post(client, headers, item_id: int, start: datetime, end: datetime):
    return client.post(
        "/api/v1/reservations",
        json={"item_id": item_id, "start_at": _iso(start), "end_at": _iso(end)},
        headers=headers,
    )


def _overlap_count(db, item_id: int, start: datetime, end: datetime) -> int:
    return db.execute(
        text(
            f"""
            SELECT count(*) FROM reservations
             WHERE item_id = :item_id
               AND status IN {BLOCKING}
               AND tstzrange(start_at, end_at, '[)') && tstzrange(:s, :e, '[)')
            """
        ),
        {"item_id": item_id, "s": start, "e": end},
    ).scalar_one()


def test_only_one_of_fifty_wins(client, headers, item, borrower_factory, db):
    borrowers = borrower_factory(50)
    start, end = _window()

    def fire(user):
        return _post(client, headers(user), item.id, start, end)

    with ThreadPoolExecutor(max_workers=50) as pool:
        responses = list(pool.map(fire, borrowers))

    codes = [response.status_code for response in responses]
    assert codes.count(201) == 1, f"expected exactly one winner, got {codes.count(201)}"
    assert codes.count(409) == 49, f"expected 49 conflicts, got {codes.count(409)}: {sorted(set(codes))}"

    conflict = next(r for r in responses if r.status_code == 409).json()["error"]
    assert conflict["code"] == "SLOT_CONFLICT"
    assert "already booked" in conflict["message"].lower()

    details = conflict["details"]
    assert details["item_id"] == item.id
    assert details["requested"]["start_at"] == _iso(start)
    assert len(details["conflicts"]) >= 1

    # The suggestions must be real: nothing may overlap them.
    suggestions = details["suggestions"]
    assert 1 <= len(suggestions) <= 3
    for slot in suggestions:
        s = datetime.fromisoformat(slot["start_at"].replace("Z", "+00:00"))
        e = datetime.fromisoformat(slot["end_at"].replace("Z", "+00:00"))
        assert e > s
        assert _overlap_count(db, item.id, s, e) == 0, f"unsafe suggestion {slot}"

    # Exactly one row exists for that window.
    assert _overlap_count(db, item.id, start, end) == 1


def test_adjacent_slots_are_both_allowed(client, headers, item, borrower_factory):
    first, second = borrower_factory(2)
    day_start = (datetime.now(timezone.utc) + timedelta(days=2)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )

    morning = _post(client, headers(first), item.id, day_start, day_start + timedelta(hours=2))
    afternoon = _post(
        client,
        headers(second),
        item.id,
        day_start + timedelta(hours=2),
        day_start + timedelta(hours=4),
    )

    assert morning.status_code == 201, morning.text
    assert afternoon.status_code == 201, afternoon.text


def test_overlapping_slot_is_rejected(client, headers, item, borrower_factory):
    first, second = borrower_factory(2)
    day_start = (datetime.now(timezone.utc) + timedelta(days=3)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )

    assert _post(client, headers(first), item.id, day_start, day_start + timedelta(hours=2)).status_code == 201
    overlap = _post(
        client, headers(second), item.id, day_start + timedelta(hours=1), day_start + timedelta(hours=3)
    )

    assert overlap.status_code == 409
    assert overlap.json()["error"]["code"] == "SLOT_CONFLICT"


def test_expired_pending_does_not_block(client, headers, item, borrower, db):
    start, end = _window(days=4)
    stale_created = datetime.now(timezone.utc) - timedelta(hours=25)

    db.execute(
        text(
            """
            INSERT INTO reservations
                (item_id, borrower_id, start_at, end_at, status, total_price, created_at)
            VALUES (:item_id, :borrower_id, :s, :e, 'pending', 0, :created_at)
            """
        ),
        {
            "item_id": item.id,
            "borrower_id": borrower.id,
            "s": start,
            "e": end,
            "created_at": stale_created,
        },
    )
    db.commit()

    res = _post(client, headers(borrower), item.id, start, end)
    assert res.status_code == 201, res.text

    statuses = db.execute(
        text("SELECT status::text FROM reservations ORDER BY id")
    ).scalars().all()
    assert "expired" in statuses


# --------------------------------------------------------------------------- #
# Layer 3 — the database itself (spec §1.2)
# --------------------------------------------------------------------------- #
def test_database_itself_rejects_overlap(db, item, borrower):
    """Even with no application code at all, PostgreSQL must refuse the overlap."""
    start, end = _window(days=5)

    def insert(s: datetime, e: datetime) -> None:
        db.execute(
            text(
                """
                INSERT INTO reservations
                    (item_id, borrower_id, start_at, end_at, status, total_price)
                VALUES (:item_id, :borrower_id, :s, :e, 'pending', 0)
                """
            ),
            {"item_id": item.id, "borrower_id": borrower.id, "s": s, "e": e},
        )
        db.commit()

    insert(start, end)

    with pytest.raises(IntegrityError) as excinfo:
        insert(start + timedelta(hours=1), end + timedelta(hours=1))

    assert booking.sqlstate(excinfo.value) == "23P01"
    db.rollback()


def test_23p01_is_translated_into_a_readable_409(client, headers, item, borrower_factory, monkeypatch):
    """Kill the pre-check and the exclusion constraint alone must still yield 409.

    This simulates the "even if the code has a bug" claim we make in the demo:
    layer 3 is what actually protects us, the check is only for a nice message.
    """
    first, second = borrower_factory(2)
    start, end = _window(days=6)

    assert _post(client, headers(first), item.id, start, end).status_code == 201

    # Blind the application-level check so the INSERT reaches the constraint.
    monkeypatch.setattr(
        "app.services.availability.busy_intervals", lambda *args, **kwargs: []
    )

    res = _post(
        client, headers(second), item.id, start + timedelta(hours=1), end + timedelta(hours=1)
    )
    assert res.status_code == 409, res.text
    error = res.json()["error"]
    assert error["code"] == "SLOT_CONFLICT"
    assert "just taken" in error["message"]

