"""Demo data (idempotent) - Backend A.

Run:  python -m app.seed
Existing rows are left untouched, so it is safe to run on every container start.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.db.session import get_engine
from app.models.item import Item
from app.models.user import User

logger = logging.getLogger("borrowbetter.seed")

DEMO_PASSWORD = "Demo1234!"

USERS = [
    {"email": "sana@demo.ir", "full_name": "Sana", "phone": "09120000001"},
    {"email": "asra@demo.ir", "full_name": "Asra", "phone": "09120000002"},
    {"email": "shaghayegh@demo.ir", "full_name": "Shaghayegh", "phone": "09120000003"},
    {"email": "demo@demo.ir", "full_name": "Demo User", "phone": "09120000004"},
]

# 12 items across 5 categories - matches section 18.1 of the team spec.
ITEMS = [
    {
        "title": "Bosch electric drill",
        "owner": "sana@demo.ir",
        "category": "tools",
        "condition": "good",
        "price_per_day": 50000,
        "description": "750W hammer drill with a full bit set and carry case.",
        "image_url": "https://picsum.photos/seed/drill/600/400",
    },
    {
        "title": "Cordless screwdriver",
        "owner": "sana@demo.ir",
        "category": "tools",
        "condition": "good",
        "price_per_day": 30000,
        "description": "Cordless screwdriver with two batteries and a charger.",
        "image_url": "https://picsum.photos/seed/screwdriver/600/400",
    },
    {
        "title": "Aluminum ladder 4m",
        "owner": "sana@demo.ir",
        "category": "tools",
        "condition": "fair",
        "price_per_day": 40000,
        "description": "Folding aluminum ladder, suitable for light renovation work.",
        "image_url": "https://picsum.photos/seed/ladder/600/400",
    },
    {
        "title": "Complete tool box",
        "owner": "asra@demo.ir",
        "category": "tools",
        "condition": "new",
        "price_per_day": 25000,
        "description": "108-piece hand tool set in a metal case.",
        "image_url": "https://picsum.photos/seed/toolbox/600/400",
    },
    {
        "title": "Home projector",
        "owner": "sana@demo.ir",
        "category": "electronics",
        "condition": "good",
        "price_per_day": 90000,
        "description": "Full HD projector with HDMI cable, great for movie nights.",
        "image_url": "https://picsum.photos/seed/projector/600/400",
    },
    {
        "title": "Canon DSLR camera",
        "owner": "shaghayegh@demo.ir",
        "category": "electronics",
        "condition": "new",
        "price_per_day": 250000,
        "description": "DSLR camera with an 18-55mm lens and carrying bag.",
        "image_url": "https://picsum.photos/seed/camera/600/400",
    },
    {
        "title": "Bluetooth speaker",
        "owner": "asra@demo.ir",
        "category": "electronics",
        "condition": "good",
        "price_per_day": 20000,
        "description": "Portable speaker with 12 hours of battery life.",
        "image_url": "https://picsum.photos/seed/speaker/600/400",
    },
    {
        "title": "4-person camping tent",
        "owner": "sana@demo.ir",
        "category": "outdoor",
        "condition": "good",
        "price_per_day": 70000,
        "description": "Waterproof 4-person tent with fiberglass poles.",
        "image_url": "https://picsum.photos/seed/tent/600/400",
    },
    {
        "title": "Hiking backpack 60L",
        "owner": "asra@demo.ir",
        "category": "outdoor",
        "condition": "fair",
        "price_per_day": 35000,
        "description": "60L backpack with rain cover and waist belt.",
        "image_url": "https://picsum.photos/seed/backpack/600/400",
    },
    {
        "title": "Camping flashlight",
        "owner": "sana@demo.ir",
        "category": "outdoor",
        "condition": "new",
        "price_per_day": 10000,
        "description": "Rechargeable waterproof flashlight with a bright beam.",
        "image_url": "https://picsum.photos/seed/flashlight/600/400",
    },
    {
        "title": "Washing machine",
        "owner": "shaghayegh@demo.ir",
        "category": "household",
        "condition": "good",
        "price_per_day": 300000,
        "description": "7kg washing machine, handy during a move or renovation.",
        "image_url": "https://picsum.photos/seed/washer/600/400",
    },
    {
        "title": "Party dinnerware set",
        "owner": "asra@demo.ir",
        "category": "household",
        "condition": "good",
        "price_per_day": 15000,
        "description": "24-piece porcelain dinnerware set for six people.",
        "image_url": "https://picsum.photos/seed/dishes/600/400",
    },
]

# Sample reservations - only created when the reservation model/table exists.
DEMO_RESERVATIONS = [
    {
        "item_title": "Bosch electric drill",
        "borrower": "asra@demo.ir",
        "start_in_hours": 24,
        "duration_hours": 4,
        "status": "pending",
    },
    {
        "item_title": "4-person camping tent",
        "borrower": "asra@demo.ir",
        "start_in_hours": 48,
        "duration_hours": 24,
        "status": "approved",
    },
    {
        "item_title": "Party dinnerware set",
        "borrower": "asra@demo.ir",
        "start_in_hours": -120,
        "duration_hours": 24,
        "status": "returned",
    },
]


def _session() -> Session:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)()


def ensure_users(db: Session) -> dict[str, User]:
    users: dict[str, User] = {}
    created = 0
    for spec in USERS:
        user = db.scalar(select(User).where(User.email == spec["email"]))
        if user is None:
            user = User(
                email=spec["email"],
                full_name=spec["full_name"],
                phone=spec["phone"],
                password_hash=hash_password(DEMO_PASSWORD),
            )
            db.add(user)
            created += 1
        users[spec["email"]] = user
    db.commit()
    logger.info("Users: %s created, %s already present", created, len(USERS) - created)
    return users


def ensure_items(db: Session, users: dict[str, User]) -> dict[str, Item]:
    items: dict[str, Item] = {}
    created = 0
    for spec in ITEMS:
        owner = users[spec["owner"]]
        item = db.scalar(
            select(Item).where(Item.owner_id == owner.id, Item.title == spec["title"])
        )
        if item is None:
            item = Item(
                owner_id=owner.id,
                title=spec["title"],
                description=spec["description"],
                category=spec["category"],
                condition=spec["condition"],
                price_per_day=spec["price_per_day"],
                image_url=spec["image_url"],
                is_active=True,
            )
            db.add(item)
            created += 1
        items[spec["title"]] = item
    db.commit()
    logger.info("Items: %s created, %s already present", created, len(ITEMS) - created)
    return items


def ensure_demo_reservations(db: Session, users: dict[str, User], items: dict[str, Item]) -> None:
    """Optional: silently skipped until Backend B ships the reservation model."""
    try:
        from app.models.reservation import Reservation  # noqa: PLC0415
    except ImportError:
        logger.info("Reservation model not available yet; skipping demo reservations.")
        return

    if "reservations" not in inspect(db.get_bind()).get_table_names():
        logger.info("Reservations table missing; skipping demo reservations.")
        return

    now = datetime.now(timezone.utc)
    created = 0
    for spec in DEMO_RESERVATIONS:
        item = items.get(spec["item_title"])
        borrower = users.get(spec["borrower"])
        if item is None or borrower is None:
            continue
        start = now + timedelta(hours=spec["start_in_hours"])
        exists = db.scalar(
            select(Reservation).where(
                Reservation.item_id == item.id,
                Reservation.borrower_id == borrower.id,
                Reservation.start_at == start,
            )
        )
        if exists is not None:
            continue
        try:
            db.add(
                Reservation(
                    item_id=item.id,
                    borrower_id=borrower.id,
                    start_at=start,
                    end_at=start + timedelta(hours=spec["duration_hours"]),
                    status=spec["status"],
                    total_price=item.price_per_day,
                )
            )
            db.commit()
            created += 1
        except Exception as exc:  # noqa: BLE001 - seeding must never break startup
            db.rollback()
            logger.warning("Demo reservation skipped (%s): %s", spec["item_title"], exc)
    logger.info("Demo reservations: %s created", created)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
    with _session() as db:
        users = ensure_users(db)
        items = ensure_items(db, users)
        ensure_demo_reservations(db, users, items)
    logger.info("Seed complete. Demo login: sana@demo.ir / %s", DEMO_PASSWORD)


if __name__ == "__main__":
    main()
