"""Demo seed — idempotent (spec §18.1). Owner: Asra (scaffold).

Run: `python -m app.seed`
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import ItemCategory, ItemCondition, ReservationStatus
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.item import Item
from app.models.reservation import Reservation
from app.models.user import User

logger = logging.getLogger(__name__)

DEMO_PASSWORD = "Demo1234!"

USERS = [
    ("sana@demo.ir", "ثنا", "09120000001"),
    ("asra@demo.ir", "اسرا", "09120000002"),
    ("shaghayegh@demo.ir", "شقایق", "09120000003"),
    ("demo@demo.ir", "کاربر دمو", None),
]

# (title, category, condition, price, owner_email, image seed)
ITEMS = [
    ("دریل برقی بوش", ItemCategory.TOOLS, ItemCondition.GOOD, 50_000, "sana@demo.ir", "drill"),
    ("پیچ‌گوشتی برقی", ItemCategory.TOOLS, ItemCondition.GOOD, 30_000, "sana@demo.ir", "screwdriver"),
    ("نردبان آلومینیومی ۴ متری", ItemCategory.TOOLS, ItemCondition.FAIR, 40_000, "sana@demo.ir", "ladder"),
    ("جعبه‌ابزار کامل", ItemCategory.TOOLS, ItemCondition.NEW, 25_000, "asra@demo.ir", "toolbox"),
    ("پروژکتور خانگی", ItemCategory.ELECTRONICS, ItemCondition.GOOD, 90_000, "sana@demo.ir", "projector"),
    ("دوربین عکاسی کانن", ItemCategory.ELECTRONICS, ItemCondition.NEW, 250_000, "shaghayegh@demo.ir", "camera"),
    ("بلندگوی بلوتوثی", ItemCategory.ELECTRONICS, ItemCondition.GOOD, 20_000, "asra@demo.ir", "speaker"),
    ("چادر مسافرتی ۴ نفره", ItemCategory.OUTDOOR, ItemCondition.GOOD, 70_000, "sana@demo.ir", "tent"),
    ("کوله‌پشتی کوهنوردی", ItemCategory.OUTDOOR, ItemCondition.FAIR, 35_000, "asra@demo.ir", "backpack"),
    ("چراغ‌قوهٔ کمپینگ", ItemCategory.OUTDOOR, ItemCondition.NEW, 10_000, "sana@demo.ir", "flashlight"),
    ("ماشین لباسشویی (امانتی!)", ItemCategory.HOUSEHOLD, ItemCondition.GOOD, 300_000, "shaghayegh@demo.ir", "washer"),
    ("ست ظروف مهمانی", ItemCategory.HOUSEHOLD, ItemCondition.GOOD, 15_000, "asra@demo.ir", "dishes"),
]

DESCRIPTIONS = {
    "drill": "دریل چکشی ۷۵۰ وات، همراه با بیت‌ست کامل و سه مته.",
    "screwdriver": "پیچ‌گوشتی شارژی با دو باتری؛ مناسب کارهای خانه.",
    "ladder": "نردبان تاشو آلومینیومی، مناسب رنگ‌آمیزی و تعمیرات سقف.",
    "toolbox": "جعبه‌ابزار کامل شامل آچار، پیچ‌گوشتی و انبردست.",
    "projector": "پروژکتور ۳۰۰۰ لومن مناسب فیلم و ارائه.",
    "camera": "دوربین DSLR با لنز ۱۸-۵۵ و کیف حمل.",
    "speaker": "بلندگوی قابل حمل با باتری ۱۰ ساعته.",
    "tent": "چادر چهار نفره ضدآب، مناسب کمپینگ خانوادگی.",
    "backpack": "کوله ۶۰ لیتری با باران‌پوش.",
    "flashlight": "چراغ‌قوهٔ شارژی ضدآب با نور قوی.",
    "washer": "ماشین لباسشویی ۷ کیلویی؛ برای امانت کوتاه‌مدت.",
    "dishes": "ست ۱۲ نفرهٔ ظروف پذیرایی.",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def seed(db: Session) -> bool:
    """Return True if data was created, False if it already existed."""
    if db.scalar(select(User.id).where(User.email == "sana@demo.ir")) is not None:
        logger.info("seed skipped: demo data already present")
        return False

    password_hash = hash_password(DEMO_PASSWORD)
    users: dict[str, User] = {}
    for email, full_name, phone in USERS:
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
        )
        db.add(user)
        users[email] = user
    db.flush()

    items: dict[str, Item] = {}
    for title, category, condition, price, owner_email, slug in ITEMS:
        item = Item(
            owner_id=users[owner_email].id,
            title=title,
            description=DESCRIPTIONS[slug],
            category=category,
            condition=condition,
            price_per_day=price,
            image_url=f"https://picsum.photos/seed/{slug}/600/400",
        )
        db.add(item)
        items[slug] = item
    db.flush()

    now = _utcnow()

    # 1) approved for tomorrow — projector (owner: sana, borrower: asra)
    db.add(
        Reservation(
            item_id=items["projector"].id,
            borrower_id=users["asra@demo.ir"].id,
            start_at=(now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0),
            end_at=(now + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0),
            status=ReservationStatus.APPROVED,
            total_price=90_000,
            message="برای ارائهٔ کلاسی لازمش دارم.",
            approved_at=now,
        )
    )

    # 2) returned last week — tent (keeps the timeline realistic)
    db.add(
        Reservation(
            item_id=items["tent"].id,
            borrower_id=users["asra@demo.ir"].id,
            start_at=now - timedelta(days=8),
            end_at=now - timedelta(days=6),
            status=ReservationStatus.RETURNED,
            total_price=140_000,
            message="کمپینگ آخر هفته.",
            approved_at=now - timedelta(days=9),
            handover_at=now - timedelta(days=8),
            returned_at=now - timedelta(days=6),
            returned_by="borrower",
        )
    )

    # 3) a pending request waiting for Sana — ladder.
    #    Deliberately NOT on the drill: the demo books the drill live.
    db.add(
        Reservation(
            item_id=items["ladder"].id,
            borrower_id=users["shaghayegh@demo.ir"].id,
            start_at=(now + timedelta(days=3)).replace(hour=9, minute=0, second=0, microsecond=0),
            end_at=(now + timedelta(days=3)).replace(hour=12, minute=0, second=0, microsecond=0),
            status=ReservationStatus.PENDING,
            total_price=40_000,
            message="برای رنگ‌آمیزی دیوار پذیرایی.",
        )
    )

    db.commit()
    logger.info("seed complete: %d users, %d items, 3 reservations", len(USERS), len(ITEMS))
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    main()
