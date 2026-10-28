"""Item catalog tests. Owner: Asra (scaffold), reviewed by Sana."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _new_item(**overrides) -> dict:
    payload = {
        "title": "Bosch electric drill",
        "description": "750W hammer drill",
        "category": "tools",
        "condition": "good",
        "price_per_day": 50_000,
        "image_url": "https://example.com/drill.jpg",
    }
    payload.update(overrides)
    return payload


def test_create_item_uses_token_owner(client, headers, borrower):
    res = client.post("/api/v1/items", json=_new_item(), headers=headers(borrower))
    assert res.status_code == 201, res.text
    data = res.json()["data"]
    assert data["owner_id"] == borrower.id
    assert data["owner"]["full_name"] == borrower.full_name
    assert data["is_active"] is True


def test_create_item_ignores_body_owner_id(client, headers, borrower):
    res = client.post(
        "/api/v1/items", json={**_new_item(), "owner_id": 999}, headers=headers(borrower)
    )
    assert res.status_code == 422  # extra="forbid" — a forged owner_id never lands


def test_list_and_filters(client, headers, owner):
    for payload in (
        _new_item(title="Bosch electric drill"),
        _new_item(title="Camping tent", category="outdoor", price_per_day=70_000),
        _new_item(title="Home projector", category="electronics", price_per_day=90_000),
    ):
        assert client.post("/api/v1/items", json=payload, headers=headers(owner)).status_code == 201

    all_items = client.get("/api/v1/items").json()
    assert all_items["meta"]["total"] == 3

    tools = client.get("/api/v1/items?category=tools").json()
    assert tools["meta"]["total"] == 1

    cheap = client.get("/api/v1/items?price_max=60000").json()
    assert cheap["meta"]["total"] == 1

    # "Bosch" appears only in the drill's title, so the search must match one row.
    search = client.get("/api/v1/items?q=Bosch").json()
    assert search["meta"]["total"] == 1
    assert search["data"][0]["title"] == "Bosch electric drill"

    sorted_items = client.get("/api/v1/items?sort=price_desc").json()
    assert sorted_items["data"][0]["price_per_day"] == 90_000


def test_only_owner_can_patch(client, headers, owner, borrower, item):
    forbidden = client.patch(
        f"/api/v1/items/{item.id}", json={"title": "New title"}, headers=headers(borrower)
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"

    ok = client.patch(
        f"/api/v1/items/{item.id}", json={"price_per_day": 60_000}, headers=headers(owner)
    )
    assert ok.status_code == 200
    assert ok.json()["data"]["price_per_day"] == 60_000


def test_delete_blocked_by_active_reservation(client, headers, owner, borrower, item):
    start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    created = client.post(
        "/api/v1/reservations",
        json={
            "item_id": item.id,
            "start_at": _iso(start),
            "end_at": _iso(start + timedelta(hours=2)),
        },
        headers=headers(borrower),
    )
    assert created.status_code == 201, created.text

    res = client.delete(f"/api/v1/items/{item.id}", headers=headers(owner))
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "ITEM_HAS_ACTIVE_RESERVATIONS"

    # Cancel → soft delete is allowed
    reservation_id = created.json()["data"]["id"]
    client.post(
        f"/api/v1/reservations/{reservation_id}/cancel", json={}, headers=headers(borrower)
    )
    assert client.delete(f"/api/v1/items/{item.id}", headers=headers(owner)).status_code == 200


def test_date_filter_returns_only_free_items(client, headers, owner, borrower, item):
    busy_item = item  # booked below
    free_item = client.post(
        "/api/v1/items", json=_new_item(title="Aluminum ladder"), headers=headers(owner)
    ).json()["data"]

    start = (datetime.now(timezone.utc) + timedelta(days=5)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    end = start + timedelta(hours=4)
    assert client.post(
        "/api/v1/reservations",
        json={"item_id": busy_item.id, "start_at": _iso(start), "end_at": _iso(end)},
        headers=headers(borrower),
    ).status_code == 201

    res = client.get(
        f"/api/v1/items?available_from={_iso(start)}&available_to={_iso(end)}"
    )
    assert res.status_code == 200, res.text
    ids = [row["id"] for row in res.json()["data"]]
    assert ids == [free_item["id"]]


def test_me_items_counters(client, headers, owner, borrower, item):
    start = (datetime.now(timezone.utc) + timedelta(days=6)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    reservation = client.post(
        "/api/v1/reservations",
        json={
            "item_id": item.id,
            "start_at": _iso(start),
            "end_at": _iso(start + timedelta(hours=2)),
        },
        headers=headers(borrower),
    ).json()["data"]
    client.post(f"/api/v1/reservations/{reservation['id']}/approve", headers=headers(owner))

    res = client.get("/api/v1/me/items", headers=headers(owner))
    assert res.status_code == 200
    row = res.json()["data"][0]
    assert row["active_reservations_count"] == 1
    assert row["pending_requests_count"] == 0


def test_categories_endpoint(client, headers, owner):
    client.post("/api/v1/items", json=_new_item(), headers=headers(owner))
    client.post(
        "/api/v1/items", json=_new_item(title="Camping tent", category="outdoor"), headers=headers(owner)
    )

    res = client.get("/api/v1/categories")
    assert res.status_code == 200
    counts = {row["value"]: row["count"] for row in res.json()["data"]}
    assert counts["tools"] == 1
    assert counts["outdoor"] == 1
    assert counts["electronics"] == 0
