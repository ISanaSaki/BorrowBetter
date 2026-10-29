"""Frontend <-> backend contract check.

Replays exactly the calls the SPA makes (`frontend/src/api/endpoints.js`) and
asserts every field the UI reads, so a backend refactor cannot silently break
the UI:

    docker compose up -d            # or: python run.py
    python scripts/contract_check.py

Exit code 0 = the API still speaks the frontend's language.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import httpx

BASE = os.getenv("CONTRACT_BASE_URL", "http://127.0.0.1:8000/api/v1")
PASSWORD = "Demo1234!"
PERMISSION_KEYS = {"can_approve", "can_reject", "can_cancel", "can_handover", "can_return"}
META_KEYS = {"page", "limit", "total", "total_pages", "has_next"}

_failures: list[str] = []
_steps = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global _steps
    _steps += 1
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  FAIL {label}  {detail}")
        _failures.append(label)


def login(client: httpx.Client, email: str) -> str:
    response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    response.raise_for_status()
    return response.json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    unique = f"Contract check {datetime.now(timezone.utc):%H%M%S}"
    # trust_env=False: a system-wide HTTP proxy (VPN clients set one) must never
    # be used for 127.0.0.1 — otherwise the proxy answers 503.
    with httpx.Client(base_url=BASE, timeout=20, trust_env=False) as client:
        print("\n1) auth envelope")
        asra = login(client, "asra@demo.ir")
        sana = login(client, "sana@demo.ir")
        me = client.get("/me", headers=auth(asra)).json()["data"]
        check("user has the fields the header renders", {"id", "full_name", "email"} <= set(me), str(me))

        print("\n2) catalog contract")
        created = client.post(
            "/items",
            json={
                "title": unique,
                "description": "Temporary item created by scripts/contract_check.py",
                "category": "tools",
                "condition": "good",
                "price_per_day": 12345,
            },
            headers=auth(sana),
        )
        check("POST /items -> 201", created.status_code == 201, created.text)
        item = created.json()["data"]
        check(
            "item payload keys",
            {"id", "title", "category", "condition", "price_per_day", "is_active", "owner", "created_at", "updated_at"}
            <= set(item),
            str(sorted(item)),
        )
        check("item.owner = {id, full_name}", {"id", "full_name"} <= set(item["owner"]), str(item["owner"]))
        item_id = item["id"]

        listing = client.get(
            "/items",
            params={"q": unique, "category": "tools", "price_max": 50000, "sort": "price_asc", "page": 1, "limit": 9},
        ).json()
        check("GET /items -> list + meta", META_KEYS <= set(listing["meta"]), str(listing.get("meta")))
        check("query echo finds the new item", [row["id"] for row in listing["data"]] == [item_id])

        categories = client.get("/categories").json()["data"]
        check(
            "GET /categories -> [{value,count}]",
            all({"value", "count"} <= set(row) for row in categories),
            str(categories[:1]),
        )

        print("\n3) availability contract")
        start = (datetime.now(timezone.utc) + timedelta(days=60)).replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=4)
        availability = client.get(
            f"/items/{item_id}/availability", params={"from": iso(start), "to": iso(end)}
        ).json()["data"]
        check(
            "availability keys",
            {"item_id", "from", "to", "is_available", "min_duration_hours", "max_duration_days", "busy", "server_time"}
            <= set(availability),
            str(sorted(availability)),
        )
        check("availability is free", availability["is_available"] is True, str(availability["busy"]))

        print("\n4) booking + 409 contract")
        booking = client.post(
            "/reservations",
            json={"item_id": item_id, "start_at": iso(start), "end_at": iso(end), "message": "contract check"},
            headers=auth(asra),
        )
        check("POST /reservations -> 201", booking.status_code == 201, booking.text)
        reservation = booking.json()["data"]
        check(
            "reservation has permissions",
            PERMISSION_KEYS <= set(reservation["permissions"]),
            str(reservation.get("permissions")),
        )
        check("permission values are booleans", all(isinstance(v, bool) for v in reservation["permissions"].values()))
        check(
            "reservation has item/borrower/lender",
            {"item", "borrower", "lender"} <= set(reservation)
            and {"id", "title", "price_per_day", "image_url"} <= set(reservation["item"])
            and {"id", "full_name", "email"} <= set(reservation["borrower"]),
            str(sorted(reservation)),
        )
        reservation_id = reservation["id"]

        conflict = client.post(
            "/reservations",
            json={
                "item_id": item_id,
                "start_at": iso(start + timedelta(hours=1)),
                "end_at": iso(end + timedelta(hours=1)),
            },
            headers=auth(asra),
        )
        check("overlap -> 409", conflict.status_code == 409, conflict.text)
        details = conflict.json()["error"]["details"]
        check(
            "409 details: item_id / requested / conflicts / suggestions",
            {"item_id", "requested", "conflicts", "suggestions"} <= set(details),
            str(sorted(details)),
        )
        check(
            "requested uses start_at/end_at",
            {"start_at", "end_at"} <= set(details["requested"]),
            str(details["requested"]),
        )
        check("suggestions are snake_case slots", all({"start_at", "end_at"} == set(slot) for slot in details["suggestions"]))
        check("1..3 suggestions", 1 <= len(details["suggestions"]) <= 3, str(len(details["suggestions"])))

        print("\n5) dashboards + transitions")
        mine = client.get(
            "/me/reservations",
            params={"role": "borrower", "status": "pending", "page": 1, "limit": 9},
            headers=auth(asra),
        ).json()
        check("GET /me/reservations -> data + meta", "data" in mine and META_KEYS <= set(mine["meta"]), str(mine.get("meta")))
        check("the new request is listed", any(row["id"] == reservation_id for row in mine["data"]))

        approve = client.post(f"/reservations/{reservation_id}/approve", json={}, headers=auth(sana))
        check(
            "approve with {} body -> approved",
            approve.status_code == 200 and approve.json()["data"]["status"] == "approved",
            approve.text,
        )

        handover = client.post(f"/reservations/{reservation_id}/handover", json={}, headers=auth(sana))
        check(
            "handover with {} body -> active",
            handover.status_code == 200 and handover.json()["data"]["status"] == "active",
            handover.text,
        )

        missing = client.post(f"/reservations/{reservation_id}/return", json={}, headers=auth(asra))
        check(
            "return without returned_by -> 422 + details.fields",
            missing.status_code == 422 and "returned_by" in missing.json()["error"]["details"]["fields"],
            missing.text,
        )

        returned = client.post(
            f"/reservations/{reservation_id}/return", json={"returned_by": "borrower"}, headers=auth(asra)
        )
        check(
            "return -> returned",
            returned.status_code == 200 and returned.json()["data"]["status"] == "returned",
            returned.text,
        )

        dashboard = client.get("/me/items", headers=auth(sana)).json()
        row = next((entry for entry in dashboard["data"] if entry["id"] == item_id), None)
        check(
            "GET /me/items -> counters",
            row is not None
            and isinstance(row.get("active_reservations_count"), int)
            and isinstance(row.get("pending_requests_count"), int),
            str(row),
        )

        print("\n6) error envelope")
        anonymous = client.get("/me")
        check(
            "no token -> 401 UNAUTHORIZED",
            anonymous.status_code == 401 and anonymous.json()["error"]["code"] == "UNAUTHORIZED",
            anonymous.text,
        )

        readonly = client.patch(f"/items/{item_id}", json={"title": "nope"}, headers=auth(asra))
        check(
            "non-owner PATCH -> 403 FORBIDDEN",
            readonly.status_code == 403 and readonly.json()["error"]["code"] == "FORBIDDEN",
            readonly.text,
        )

        missing_item = client.get("/items/99999999")
        check(
            "unknown item -> 404 NOT_FOUND",
            missing_item.status_code == 404 and missing_item.json()["error"]["code"] == "NOT_FOUND",
            missing_item.text,
        )

        deleted = client.delete(f"/items/{item_id}", headers=auth(sana))
        check("cleanup: DELETE /items/{id} -> 200", deleted.status_code == 200, deleted.text)

    print(f"\n{'all good' if not _failures else 'failures: ' + ', '.join(_failures)}")
    print(f"   {_steps - len(_failures)}/{_steps} checks passed")
    return 0 if not _failures else 1


if __name__ == "__main__":
    sys.exit(main())
