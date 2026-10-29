"""End-to-end smoke test of the demo scenario (spec §1.5).

Runs against a *live* server, so it validates the HTTP layer, the seed data and
the whole booking state machine in one go.

    uvicorn app.main:app --port 8000
    python scripts/demo_smoke.py

Exit code 0 = the demo will work.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import httpx

BASE = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000/api/v1")
PASSWORD = "Demo1234!"

_failures: list[str] = []
_steps = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global _steps
    _steps += 1
    if condition:
        print(f"  ✅ {label}")
    else:
        print(f"  ❌ {label}  {detail}")
        _failures.append(label)


def login(client: httpx.Client, email: str) -> str:
    res = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    res.raise_for_status()
    return res.json()["data"]["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    # trust_env=False: a system-wide HTTP proxy (VPN clients often set one) must
    # never be used for 127.0.0.1 — otherwise the proxy answers 503.
    with httpx.Client(base_url=BASE, timeout=20, trust_env=False) as client:
        print("\n1) health & catalog")
        health = httpx.get(BASE.replace("/api/v1", "") + "/health", timeout=10, trust_env=False).json()
        check("health is ok", health.get("status") == "ok", str(health))

        catalog = client.get("/items", params={"q": "drill"}).json()
        check("catalog search works", catalog["meta"]["total"] >= 1, str(catalog["meta"]))
        drill = next(
            (row for row in catalog["data"] if row["title"] == "Bosch electric drill"), None
        )
        check("demo drill exists", drill is not None)
        if drill is None:
            return 1

        asra = login(client, "asra@demo.ir")
        sana = login(client, "sana@demo.ir")
        shaghayegh = login(client, "shaghayegh@demo.ir")

        # The seed keeps a pending request on the drill at "now + 24h", so the demo
        # books two days ahead — a window that is guaranteed to be free.
        day = (datetime.now(timezone.utc) + timedelta(days=2)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        start, end = day, day + timedelta(hours=4)

        print("\n2) borrower requests a free window (day after tomorrow, 10:00–14:00)")
        created = client.post(
            "/reservations",
            json={"item_id": drill["id"], "start_at": iso(start), "end_at": iso(end)},
            headers=auth(asra),
        )
        check("201 created", created.status_code == 201, created.text)
        reservation = created.json()["data"]
        check("status is pending", reservation["status"] == "pending")
        check("price computed", reservation["total_price"] == drill["price_per_day"])
        reservation_id = reservation["id"]

        print("\n3) second borrower hits the overlapping window")
        conflict = client.post(
            "/reservations",
            json={
                "item_id": drill["id"],
                "start_at": iso(start + timedelta(hours=2)),
                "end_at": iso(end + timedelta(hours=2)),
            },
            headers=auth(shaghayegh),
        )
        check("409 conflict", conflict.status_code == 409, conflict.text)
        error = conflict.json()["error"]
        check("code is SLOT_CONFLICT", error["code"] == "SLOT_CONFLICT")
        check(
            "conflicts reported", len(error["details"]["conflicts"]) >= 1, str(error["details"])
        )
        suggestions = error["details"]["suggestions"]
        check("1–3 suggestions", 1 <= len(suggestions) <= 3, str(suggestions))

        print("\n4) owner approves, hands over; borrower returns")
        approved = client.post(f"/reservations/{reservation_id}/approve", headers=auth(sana))
        check("approved", approved.status_code == 200 and approved.json()["data"]["status"] == "approved", approved.text)

        forbidden = client.post(f"/reservations/{reservation_id}/approve", headers=auth(asra))
        check("borrower cannot approve (403)", forbidden.status_code == 403, forbidden.text)

        active = client.post(f"/reservations/{reservation_id}/handover", headers=auth(sana))
        check("active", active.status_code == 200 and active.json()["data"]["status"] == "active", active.text)

        returned = client.post(
            f"/reservations/{reservation_id}/return",
            json={"returned_by": "borrower"},
            headers=auth(asra),
        )
        check("returned", returned.status_code == 200 and returned.json()["data"]["status"] == "returned", returned.text)

        print("\n5) the window is free again")
        again = client.post(
            "/reservations",
            json={"item_id": drill["id"], "start_at": iso(start), "end_at": iso(end)},
            headers=auth(shaghayegh),
        )
        check("slot released", again.status_code == 201, again.text)

        calendar = client.get(f"/items/{drill['id']}/availability").json()["data"]
        check("availability endpoint", calendar["item_id"] == drill["id"])
        check("busy list has no borrower data", all(set(slot) == {"start_at", "end_at"} for slot in calendar["busy"]))

        dashboard = client.get("/me/items", headers=auth(sana)).json()
        drill_row = next(row for row in dashboard["data"] if row["id"] == drill["id"])
        check("owner dashboard counters", "active_reservations_count" in drill_row, str(drill_row))

    print(f"\n{'✅ all good' if not _failures else '❌ failures: ' + ', '.join(_failures)}")
    print(f"   {_steps - len(_failures)}/{_steps} checks passed")
    return 0 if not _failures else 1


if __name__ == "__main__":
    sys.exit(main())
