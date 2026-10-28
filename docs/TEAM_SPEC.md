# BorrowBetter — سند واحد تیم (Single Source of Truth)

> **این فایل تنها مرجع حقیقت تیم است.** هر تصمیمی که اینجا نوشته نشده، تصمیم نگرفته‌ایم.
> هر چیزی که اینجا نوشته شده، **قفل** است تا پایان روز مسابقه.

| نسخه | تاریخ | وضعیت | تأییدکنندگان |
|---|---|---|---|
| **v1.0** | 1405/08/06 | 🔒 قفل‌شده (Frozen) | اسرا · ثنا · شقایق |

**قاعدهٔ تغییر این فایل:** فقط با PR + تأیید ۲ نفر + بالا بردن نسخه (v1.1، v1.2 …) و اعلام در گروه.
تا ساعت **T+01:30** هیچ تغییری مجاز نیست. بعد از آن فقط تغییرات «اضطراری» با تأیید ثنا.

---

## فهرست

| # | بخش | برای چه کسی |
|---|---|---|
| ۰ | قوانین طلایی | همه |
| ۱ | محصول، محدوده، سناریوی دمو | همه |
| ۲ | نقش‌ها و مالکیت | همه |
| ۳ | معماری، ریپو، داکر، اجرا | همه |
| ۴ | **قرارداد نام‌ها (نام فیلدها)** | همه — مهم‌ترین بخش |
| ۵ | مدل داده و SQL | اسرا + ثنا |
| ۶ | ماشین وضعیت و قواعد امانت | ثنا + شقایق |
| ۷ | قرارداد API (تمام اندپوینت‌ها) | همه |
| ۸ | فرانت‌اند | شقایق |
| ۹ | هوش مصنوعی (جست‌وجوی معنایی) | شقایق |
| ۱۰ | تست و CI | ثنا + اسرا |
| ۱۱ | گیت و همکاری | همه |
| ۱۲ | خط زمانی ۶ ساعته + تکالیف قبل از مسابقه | همه |
| ۱۳ | ترتیب حذف در صورت کمبود وقت | ثنا |
| ۱۴ | Definition of Done هر نفر | همه |
| ۱۵ | چک‌لیست یکپارچه‌سازی نهایی | همه |
| ۱۶ | ریسک‌ها و راه‌حل‌ها | همه |
| ۱۷ | پروتکل ارتباط تیم | همه |
| ۱۸ | ضمیمه‌ها: seed، تست همزمانی، Q&A داور، واژه‌نامه | همه |

### در ۶۰ ثانیه، هر نفر چه می‌کند؟

- **اسرا (بک‌اند A — پلتفرم):** زیرساخت داکر، `users`، `items`، احراز هویت، CRUD وسایل، فیلتر، seed دمو.
- **ثنا (بک‌اند B — موتور رزرو):** `reservations`، قید عدم‌همپوشانی، رزرو اتمیک، گذارهای وضعیت، availability، تست همزمانی، CI. **تصمیم نهایی فنی با اوست.**
- **شقایق (فرانت + AI):** کل UI با HTML/CSS/JS خالص (RTL)، اتصال به API، UX خطای ۴۰۹، و `POST /ai/search` با TF-IDF محلی.

**نقطهٔ اتصال واحد تیم:** تابع `free_item_ids()` در `app/services/availability.py` (مالک: ثنا). هر کس نیاز به «آیا این وسیله در این بازه آزاد است؟» دارد، فقط همین تابع را صدا می‌زند. هیچ‌کس دیگری روی `reservations` کوئری نمی‌نویسد.

---

## ۰) قوانین طلایی (۱۲ خط، حفظ کن)

1. **این فایل > کد.** اگر کد با این فایل اختلاف داشت، کد غلط است.
2. **نام‌ها قفل‌اند.** همه‌جا `snake_case`. فرانت **هیچ** تبدیلی به camelCase انجام نمی‌دهد. `item.price_per_day` همان چیزی است که در دیتابیس است.
3. **هر فایل یک مالک.** فایل دیگری را «کمی درست نکن»؛ به مالک بگو.
4. **هر مایگریشن یک مالک.** دو نفر همزمان روی `alembic/versions/` کار نمی‌کنند.
5. **قرارداد قبل از کد.** تا T+01:30 شکل پاسخ‌ها قفل می‌شود؛ بعد از آن تغییر = PR + ۲ تأیید.
6. **۱۵ دقیقه گیر کردی؟ اعلام کن.** سکوت = تأخیر تیم.
7. **هر پاسخ موفق در `data` است، هر خطا در `error`.** استثنا وجود ندارد.
8. **همه‌ی تاریخ‌ها UTC و ISO-8601 با `Z`.** نمایش شمسی فقط در فرانت.
9. **هرگز `print` نزن؛ `logging` بزن.** لاگ بدون ایمیل/پسورد.
10. **یک دموی کارکرده > ده فیچر نصفه.** اول مسیر خوشحال، بعد استثناها، بعد زیبایی.
11. **تا T+04:30 هیچ refactor ای مجاز نیست.** فقط باگ‌فیکس.
12. **`main` همیشه سبز است.** اگر CI قرمز شد، همان لحظه یا فیکس کن یا revert کن.

---

## ۱) محصول، محدوده و دمو

### ۱.۱ در یک جمله

**BorrowBetter** یک کتابخانهٔ امانت وسایل محلی است: آدم‌ها وسایل کم‌استفادهٔ خود (دریل، چادر، پروژکتور…) را ثبت می‌کنند، همسایه‌ها در یک بازهٔ زمانی مشخص درخواست رزرو می‌دهند، صاحب وسیله تأیید/رد می‌کند، تحویل و بازگشت ثبت می‌شود.

### ۱.۲ چرا این پروژه برنده است (دغدغهٔ اصلی)

مسئلهٔ سخت، CRUD نیست؛ **همزمانی** است:
دو نفر در یک ثانیه یک بازه از یک وسیله را رزرو می‌کنند. سیستم باید **دقیقاً یکی** را بپذیرد و به دیگری **پیام قابل‌فهم + ۳ بازهٔ جایگزین** بدهد.

ما این را در سه لایه تضمین می‌کنیم و **در دمو نشان می‌دهیم**:

1. **قید Exclusion دیتابیس** (`no_overlap`) — ضامن نهایی، حتی اگر کد باگ داشته باشد.
2. **قفل ردیف وسیله** (`SELECT … FOR UPDATE`) — سریال‌سازی منطقی + محاسبهٔ جایگزین‌ها.
3. **ماشین وضعیت صریح** — `pending → approved → active → returned` با جدول گذار مجاز.

### ۱.۳ داخل محدوده (MVP — باید تا پایان روز کار کند)

- ثبت‌نام / ورود با JWT
- CRUD وسایل + آپلود‌نشدن عکس (فقط `image_url` متنی)
- کاتالوگ با جست‌وجوی متنی، فیلتر دسته/قیمت، فیلتر تاریخ
- صفحهٔ جزئیات وسیله + تقویم دسترسی
- ثبت درخواست رزرو، تأیید، رد، لغو، تحویل، بازگشت
- داشبورد صاحب وسیله و داشبورد متقاضی
- خطای ۴۰۹ با ۳ پیشنهاد جایگزین
- تست همزمانی ۵۰ درخواست + CI
- UI کامل RTL، ریسپانسیو، بدون بیلد سنگین

### ۱.۴ خارج از محدوده (عمداً حذف شد — در ارائه هم بگویید)

| حذف‌شده | دلیل |
|---|---|
| Redis / Celery | برای ۶ ساعت ارزش دمو صفر، ریسک بالا. انقضا با lazy-expire حل می‌شود. |
| آپلود فایل تصویر | `image_url` متنی کافی است. |
| نظرات و امتیازدهی | فیچر «خوب بودن»، نه «برنده شدن». |
| پرداخت واقعی | `total_price` فقط محاسبه و نمایش. |
| چت، نوتیفیکیشن، ایمیل | خارج از زمان. |
| رزرو موقت (hold) با انقضا | خودِ `pending` نقش قفل را دارد. |
| بازهٔ آماده‌سازی بین دو امانت | پیچیدگی زیاد، ارزش کم. |
| میکروسرویس جدا برای AI | همان اپ، یک ماژول ایزوله. |

### ۱.۵ سناریوی دمو (۴ دقیقه — این را حفظ کنید)

| # | چه کسی | چه کاری | چه چیزی باید دیده شود |
|---|---|---|---|
| 1 | شقایق | باز کردن کاتالوگ، جست‌وجوی «دریل» | کارت‌ها، فیلترها، RTL، تصاویر |
| 2 | شقایق | کلیک روی «دریل برقی بوش» | جزئیات، قیمت روزانه، تقویم بازه‌های اشغال |
| 3 | اسرا | لاگین به‌عنوان متقاضی، انتخاب ۱۰:۰۰–۱۴:۰۰، ثبت درخواست | Toast موفقیت، وضعیت `pending` در داشبورد |
| 4 | ثنا | لاگین به‌عنوان صاحب وسیله، دیدن درخواست، تأیید | وضعیت `approved` |
| 5 | شقایق | **تب دوم:** همان وسیله، بازهٔ ۱۲:۰۰–۱۶:۰۰ | **۴۰۹ با پیام فارسی + ۳ بازهٔ جایگزین کلیک‌پذیر** |
| 6 | ثنا | تحویل (`handover`) در تب اول | `active` |
| 7 | اسرا | بازگشت (`return`) | `returned` + آزاد شدن بازه |
| 8 | شقایق | `POST /ai/search` با «چیزی برای کمپینگ» | نتایج مرتبط بدون تطابق کلمه‌به‌کلمه |

**جملهٔ پایانی دمو:** «ما همزمانی را در سطح دیتابیس قفل کردیم، نه در سطح کد؛ و به کاربری که شکست خورد، راه حل دادیم نه خطا.»

### ۱.۶ پنج سؤال داور و پاسخ آماده

1. **«اگر دو درخواست همزمان برسند چه می‌شود؟»** → قید `EXCLUDE USING gist` در پستگرس؛ دومی `23P01` می‌گیرد، تراکنش rollback و ۴۰۹ با پیشنهاد جایگزین. تست ۵۰-درخواستی در CI.
2. **«چرا Redis/Celery ندارید؟»** → آگاهانه حذف شد؛ انقضای ۲۴ ساعته با lazy-expire در همان تراکنش خواندن حل می‌شود و پیچیدگی عملیاتی صفر است.
3. **«چرا وضعیت `pending` بازه را قفل می‌کند؟»** → جلوگیری از رزرو دوباره در حین تصمیم صاحب وسیله؛ با انقضای ۲۴ ساعته از بن‌بست جلوگیری می‌کنیم.
4. **«چرا فرانت و بک دقیقاً یک نام دارند؟»** → یک قرارداد، صفر لایهٔ تبدیل، صفر باگ `undefined`. جدول بخش ۴ منبع مشترک است.
5. **«مقیاس‌پذیری؟»** → افزودن worker/کش؛ ولی گلوگاه واقعی، قید دیتابیس است که در هر مقیاسی درست کار می‌کند.

---

## ۲) تیم، نقش‌ها و مالکیت

### ۲.۱ نقش‌ها

| | **اسرا** | **ثنا** | **شقایق** |
|---|---|---|---|
| **نقش** | Backend A — پلتفرم و کاتالوگ | Backend B — موتور رزرو + Tech Lead | Frontend + AI |
| **جدول‌ها** | `users`, `items` | `reservations` | — (فقط مصرف‌کننده) |
| **مایگریشن** | `0001_init` | `0002_reservations` (وابسته به 0001) | — |
| **شاخهٔ گیت** | `feat/api-platform` | `feat/booking-engine` (و `chore/ci`) | `feat/frontend` (و `feat/ai-search`) |
| **ریسک اصلی** | یکدستی قرارداد، اعتبارسنجی | همزمانی، صحت گذارها | هم‌ترازی با API واقعی |
| **تصمیم نهایی در** | ساختار کاتالوگ و seed | **همه‌چیزِ فنی**، مایگریشن، مرج | UI/UX، توکن‌های طراحی |
| **نقطهٔ ضعف** | تجربهٔ کم → باید الگو بگیرد | بار زیاد → نباید همه‌چیز را خودش بزند | تنها فرانت‌کار → شلوغی |

### ۲.۲ چرا این تقسیم (نه «هرکس نصف تسک‌ها»)

- **همزمانی یک مالک واحد دارد.** اگر دو نفر روی منطق رزرو دست ببرند، باگ‌های race غیرقابل‌دیباگ می‌شوند.
- **ثنا عمیق‌ترین آدم در SQL/Alchemy است** → موتور رزرو و CI به او.
- **اسرا سطح مستقل و کامل می‌گیرد** (هویت + کاتالوگ + زیرساخت) که برای یادگیری و اعتمادبه‌نفس بهتر است و به موتور رزرو وابسته نیست.
- **شقایق مالک پیکسل و تجربه است** و مرز فرانت/بک دقیقاً «فقط JSON» است، پس می‌تواند از دقیقهٔ اول با mock جلو برود.
- **هیچ فایلی دو مالک ندارد.** این تنها قانونی است که شکستنش کل تیم را زمین می‌زند.

### ۲.۳ مالکیت فایل‌ها (قفل)

| مسیر | مالک | توضیح |
|---|---|---|
| `docker-compose.yml`, `Dockerfile`, `.env.example`, `Makefile` | اسرا | ثنا فقط ریویو |
| `app/main.py`, `app/core/*` | اسرا | خطا، تنظیمات، امنیت، لاگ |
| `app/api/deps.py` | اسرا | `get_db`, `current_user` |
| `app/models/user.py`, `app/models/item.py` | اسرا | |
| `app/routers/auth.py`, `users.py`, `items.py` | اسرا | |
| `app/services/auth.py`, `items.py`, `search.py` | اسرا | |
| `app/seed.py` | اسرا | |
| `app/models/reservation.py` | ثنا | |
| `app/routers/reservations.py` | ثنا | |
| `app/services/booking.py`, `availability.py`, `lifecycle.py` | ثنا | |
| `app/services/permissions.py` | ثنا | منبع `permissions` در پاسخ |
| `alembic/versions/0001_*` | اسرا | |
| `alembic/versions/0002_*` | ثنا | |
| `tests/test_concurrency.py`, `tests/test_transitions.py` | ثنا | |
| `tests/test_auth.py`, `tests/test_items.py` | اسرا | |
| `.github/workflows/ci.yml` | ثنا | |
| `app/routers/ai.py`, `app/services/ai_search.py` | شقایق | فقط از سرویس‌های A و B استفاده می‌کند |
| `frontend/**` | شقایق | هیچ‌کس دیگری کامیت نمی‌کند |
| `README.md` | اسرا | |
| `docs/TEAM_SPEC.md` (همین فایل) | همه | تغییر = PR + ۲ تأیید |

**قواعد سخت:**

- اسرا **هرگز** روی `reservations` کوئری نمی‌نویسد (حتی `SELECT`). فقط `free_item_ids()`.
- ثنا **هرگز** `items.py` یا `auth.py` را ادیت نمی‌کند.
- شقایق **هرگز** به بک‌اند دست نمی‌زند جز `ai.py` / `ai_search.py`؛ اگر API کمبود داشت، درخواست می‌دهد نه پچ.
- ثنا روی `frontend/` کامیت نمی‌کند؛ اگر باگ UI دید، به شقایق می‌گوید.

### ۲.۴ کارهای مشترک (۲۰ دقیقهٔ اول، همه حاضر)

| کار | خروجی | مالک اجرا |
|---|---|---|
| خواندن همین فایل | همه بخش ۰–۴ را خوانده‌اند | همه |
| ساخت ریپو + شاخه‌ها + محافظت `main` | ریپوی آماده با ۳ شاخه | ثنا |
| ریختن `.env.example` و `docker-compose` | `docker compose up` سبز | اسرا |
| چک کردن قرارداد نام‌ها در بخش ۴ | «تأیید می‌کنم» در گروه | همه |

---

## ۳) معماری، ریپو، داکر و اجرا

### ۳.۱ نمودار

```
┌──────────────────────────────┐
│  Browser — SPA (Vanilla JS)  │   dir="rtl" · fa-IR
│  Vite dev server :5173       │
└──────────────┬───────────────┘
               │  JSON  ·  /api/v1/*  ·  Authorization: Bearer <jwt>
               ▼
┌──────────────────────────────┐
│  FastAPI (uvicorn) :8000     │
│  ┌────────────┬────────────┐ │
│  │ A: platform│ B: booking │ │
│  │ auth/items │ reserv.    │ │
│  └────────────┴────────────┘ │
│  + ai_search.py (tf-idf)     │
└──────────────┬───────────────┘
               │ SQLAlchemy 2.0 (sync) + psycopg3
               ▼
┌──────────────────────────────┐
│  PostgreSQL 16 :5432         │
│  btree_gist · EXCLUDE no_overlap
└──────────────────────────────┘
```

**تصمیم‌های فنی قفل‌شده:**

| موضوع | تصمیم | دلیل |
|---|---|---|
| نسخهٔ API | همهٔ مسیرها زیر `/api/v1` (به‌جز `/health`) | جلوگیری از شکستن فرانت |
| SQLAlchemy | **2.0، sync** (`Session`)، اندپوینت‌های `def` | تیم مبتدی؛ پایداری؛ قید دیتابیس مستقل از async کار می‌کند |
| درایور | `psycopg[binary]` (v3) | سریع و بدون کامپایل |
| JWT | `PyJWT` (HS256) | ساده، بدون وابستگی سنگین |
| هش پسورد | `passlib[bcrypt]` + **`bcrypt==4.0.1`** | سازگاری؛ نسخهٔ 4.1+ خطای «reading bcrypt version» می‌دهد |
| ولیدیشن | Pydantic v2، `extra="forbid"` | فیلد اضافی/غلط = ۴۲۲ فوری (باگ نام‌گذاری لو می‌رود) |
| فرانت | Vanilla JS (ESM) + Vite + CSS خالص | مهارت شقایق، بیلد سریع، بدون فریم‌ورک |
| AI | TF-IDF محلی (`scikit-learn`) + دیکشنری مترادف فارسی | آفلاین، قطعی، بدون کلید API و بدون ریسک شبکه |
| فونت | Vazirmatn (CDN یا لوکال) | خوانایی فارسی |

### ۳.۲ ساختار ریپو

```
borrowbetter/
├── docker-compose.yml              # A
├── Dockerfile                      # A
├── .env.example                    # A
├── Makefile                        # A
├── README.md                       # A
├── alembic.ini                     # A
├── requirements.txt                # A (ثنا فقط با PR)
├── pytest.ini                      # B
├── .github/workflows/ci.yml        # B
├── docs/
│   └── TEAM_SPEC.md                # همه (همین فایل)
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 0001_init.py            # A
│       └── 0002_reservations.py    # B
├── app/
│   ├── main.py                     # A
│   ├── seed.py                     # A
│   ├── core/
│   │   ├── config.py               # A
│   │   ├── security.py             # A (jwt, hash)
│   │   ├── errors.py               # A (AppError + handlers)
│   │   ├── logging.py              # A
│   │   └── constants.py            # A (enums مشترک) · تغییر = ۲ تأیید
│   ├── db/
│   │   ├── base.py                 # A
│   │   └── session.py              # A
│   ├── models/
│   │   ├── user.py                 # A
│   │   ├── item.py                 # A
│   │   └── reservation.py          # B
│   ├── schemas/
│   │   ├── auth.py                 # A
│   │   ├── user.py                 # A
│   │   ├── item.py                 # A
│   │   ├── common.py               # A (Page, Error, envelope)
│   │   ├── reservation.py          # B
│   │   └── ai.py                   # شقایق
│   ├── api/
│   │   ├── deps.py                 # A
│   │   └── v1.py                   # A (روتر اصلی، mount همه)
│   ├── routers/
│   │   ├── auth.py                 # A
│   │   ├── users.py                # A
│   │   ├── items.py                # A
│   │   ├── reservations.py         # B
│   │   └── ai.py                   # شقایق
│   └── services/
│       ├── auth.py                 # A
│       ├── items.py                # A
│       ├── search.py               # A
│       ├── booking.py              # B
│       ├── availability.py         # B  ← تنها نقطهٔ اتصال
│       ├── lifecycle.py            # B
│       ├── permissions.py          # B
│       └── ai_search.py            # شقایق
├── tests/
│   ├── conftest.py                 # B
│   ├── test_auth.py                # A
│   ├── test_items.py               # A
│   ├── test_transitions.py         # B
│   └── test_concurrency.py         # B
└── frontend/
    ├── package.json                # C
    ├── vite.config.js              # C
    ├── index.html                  # C
    └── src/
        ├── main.js                 # C
        ├── router.js               # C
        ├── constants.js            # C (کپی enumها + برچسب فارسی)
        ├── api/client.js           # C
        ├── api/endpoints.js        # C
        ├── api/mock/*.json         # C
        ├── store/auth.js           # C
        ├── store/ui.js             # C (toast, modal)
        ├── lib/format.js           # C (پول، تاریخ شمسی)
        ├── components/*.js         # C
        ├── pages/*.js              # C
        └── styles/{tokens,base,components}.css   # C
```

### ۳.۳ داکر و پورت‌ها

| سرویس | ایمیج | پورت | healthcheck |
|---|---|---|---|
| `db` | `postgres:16-alpine` | `5432` | `pg_isready -U borrowbetter` |
| `api` | build از `Dockerfile` | `8000` | `GET /health` |
| `web` | `node:20-alpine` (dev) — اختیاری | `5173` | — |

`docker-compose.yml` (مرجع، مالک اسرا):

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 3s
      timeout: 3s
      retries: 20

  api:
    build: .
    env_file: .env
    ports: ["8000:8000"]
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             python -m app.seed &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000"
    volumes: ["./app:/code/app", "./alembic:/code/alembic"]

volumes:
  pgdata:
```

> ⚠️ `seed` باید **idempotent** باشد: اگر داده هست، دوباره نسازد.

### ۳.۴ متغیرهای محیطی (`.env.example`)

```dotenv
# --- Database ---
POSTGRES_USER=borrowbetter
POSTGRES_PASSWORD=borrowbetter
POSTGRES_DB=borrowbetter
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://borrowbetter:borrowbetter@db:5432/borrowbetter

# --- App ---
APP_NAME=BorrowBetter
APP_ENV=dev
API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO

# --- Auth ---
SECRET_KEY=change-me-in-production-please-32chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# --- CORS ---
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# --- Booking rules (B) ---
MIN_DURATION_HOURS=1
MAX_DURATION_DAYS=30
PENDING_EXPIRE_HOURS=24
SUGGESTION_COUNT=3

# --- Frontend ---
VITE_API_BASE=http://localhost:8000/api/v1
```

### ۳.۵ اجرا — هر نفر روی سیستم خودش

**مسیر اصلی (داکر):**

```bash
cp .env.example .env
docker compose up --build -d
docker compose logs -f api          # باید "Application startup complete" ببینی
curl http://localhost:8000/health   # {"status":"ok", ...}
```

**فرانت (شقایق):**

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

**بدون داکر (fallback، اگر داکر روی ویندوز کند بود):**

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
# در .env مقدار POSTGRES_HOST=localhost بگذار
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

**دستورهای سریع (Makefile):**

| دستور | کار |
|---|---|
| `make up` | `docker compose up --build -d` |
| `make logs` | لاگ api |
| `make migrate` | `alembic upgrade head` |
| `make seed` | seed دمو |
| `make test` | `pytest -q` |
| `make reset` | drop + migrate + seed (فقط dev) |
| `make fmt` | `ruff format . && ruff check --fix .` |

---

## ۴) قرارداد نام‌ها — مهم‌ترین بخش این فایل

> **چرا این بخش حیاتی است؟** بیشترین باگ هماهنگی در تیم‌ها، باگ «نام» است نه باگ «منطق»: `startDate` vs `start_at`، `itemId` vs `item_id`، `pricePerDay` vs `price_per_day`. اینجا یک‌بار برای همیشه حل می‌شود.

### ۴.۱ قواعد

| قاعده | درست | غلط |
|---|---|---|
| همه‌ی کلیدهای JSON و ستون‌ها `snake_case` | `start_at` | `startAt`, `StartAt` |
| شناسه: `id` و `<entity>_id` | `item_id` | `itemID`, `itemId`, `ItemId` |
| زمان‌ها: پسوند `_at` + `TIMESTAMPTZ` + ISO-8601 UTC | `created_at: "2026-11-01T10:00:00Z"` | `created: 1698…` |
| بولین: پیشوند `is_` / `can_` | `is_active`, `can_approve` | `active`, `approve` |
| پول: عدد صحیح، واحد **تومان**، پسوند `_price` یا `price_` | `price_per_day: 50000` | `"50000"`, `50.0`, `pricePerDayToman` |
| شمارنده‌ها: `*_count` | `active_reservations_count` | `reservations` |
| متن‌های تصمیم: `*_note`, `*_reason` | `decision_note` | `comment`, `desc2` |
| مسیرها: جمع، `kebab` نیست | `/items`, `/reservations` | `/getItems` |
| پارامتر مسیر: `{item_id}` | `/items/{item_id}` | `/items/:id` در قرارداد |
| پارامتر کوئری: `snake_case` | `?price_max=100000` | `?priceMax=` |
| **بدون لایهٔ تبدیل در فرانت** | `res.data.data[0].price_per_day` | `item.pricePerDay` |
| **کلیدها همیشه حاضرند** (`null` می‌فرستیم، حذف نمی‌کنیم) | `"decision_note": null` | کلید غایب |

**قانون طلایی فرانت:** هرگز نام فیلد را در `api/endpoints.js` تغییر نده. اگر لازم شد نام عوض شود، ابتدا این فایل تغییر می‌کند، بعد بک، بعد فرانت — همه در یک PR.

### ۴.۲ جدول نام فیلدها (منبع واحد حقیقت)

#### `user`

| فیلد | نوع | در DB | در API | توضیح |
|---|---|---|---|---|
| `id` | int | ✅ | ✅ | |
| `email` | string | ✅ | ✅ | lowercase، یکتا |
| `password_hash` | string | ✅ | ❌ **هرگز** | فقط داخلی |
| `full_name` | string | ✅ | ✅ | ۲–۸۰ کاراکتر |
| `phone` | string \| null | ✅ | ✅ | اختیاری |
| `created_at` | datetime | ✅ | ✅ | |

#### `item`

| فیلد | نوع | در DB | در API | توضیح |
|---|---|---|---|---|
| `id` | int | ✅ | ✅ | |
| `owner_id` | int | ✅ | ✅ | FK → `users.id` |
| `title` | string | ✅ | ✅ | ۳–۱۲۰ |
| `description` | string | ✅ | ✅ | ≤ ۲۰۰۰ |
| `category` | enum | ✅ | ✅ | `tools\|electronics\|outdoor\|household\|other` |
| `condition` | enum | ✅ | ✅ | `new\|good\|fair\|worn` |
| `price_per_day` | int (تومان) | ✅ | ✅ | ≥ ۰ |
| `image_url` | string \| null | ✅ | ✅ | URL متنی |
| `is_active` | bool | ✅ | ✅ | حذف = `false` |
| `created_at` | datetime | ✅ | ✅ | |
| `updated_at` | datetime | ✅ | ✅ | |
| `owner` | object | ❌ | ✅ | `{id, full_name}` — join |
| `active_reservations_count` | int | ❌ | فقط `GET /me/items` | شمارندهٔ B |
| `pending_requests_count` | int | ❌ | فقط `GET /me/items` | شمارندهٔ B |

#### `reservation`

| فیلد | نوع | در DB | در API | توضیح |
|---|---|---|---|---|
| `id` | int | ✅ | ✅ | |
| `item_id` | int | ✅ | ✅ | |
| `borrower_id` | int | ✅ | ✅ | متقاضی |
| `start_at` | datetime | ✅ | ✅ | UTC، inclusive |
| `end_at` | datetime | ✅ | ✅ | UTC، **exclusive** |
| `status` | enum | ✅ | ✅ | بخش ۴.۳ |
| `total_price` | int | ✅ | ✅ | محاسبه‌شده در لحظهٔ ساخت |
| `message` | string \| null | ✅ | ✅ | ≤ ۵۰۰ |
| `decision_note` | string \| null | ✅ | ✅ | یادداشت تأیید/رد |
| `cancel_reason` | string \| null | ✅ | ✅ | |
| `returned_by` | `lender`\|`borrower`\|null | ✅ | ✅ | فقط پس از `returned` |
| `created_at` | datetime | ✅ | ✅ | |
| `updated_at` | datetime | ✅ | ✅ | |
| `approved_at` | datetime \| null | ✅ | ✅ | |
| `handover_at` | datetime \| null | ✅ | ✅ | |
| `returned_at` | datetime \| null | ✅ | ✅ | |
| `closed_at` | datetime \| null | ✅ | ✅ | رد/لغو/انقضا |
| `item` | object | ❌ | ✅ | خلاصهٔ وسیله |
| `borrower` | object | ❌ | ✅ | `{id, full_name, email}` |
| `lender` | object | ❌ | ✅ | `{id, full_name, email}` = owner وسیله |
| `permissions` | object | ❌ | ✅ | `{can_approve, can_reject, can_cancel, can_handover, can_return}` |

#### پاکت‌های پاسخ

| فیلد | نوع | معنی |
|---|---|---|
| `data` | object \| array | **همیشه** بدنهٔ موفق |
| `meta` | object | فقط برای لیست‌ها |
| `meta.page` | int | از ۱ |
| `meta.limit` | int | پیش‌فرض ۲۰، حداکثر ۱۰۰ |
| `meta.total` | int | کل نتایج |
| `meta.total_pages` | int | |
| `meta.has_next` | bool | |
| `error` | object | بدنهٔ خطا |
| `error.code` | string | مثل `SLOT_CONFLICT` |
| `error.message` | string | **فارسی، قابل نمایش به کاربر** |
| `error.details` | object \| null | ساختار مخصوص هر خطا |

#### احراز هویت

| فیلد | نوع | توضیح |
|---|---|---|
| `access_token` | string | JWT |
| `token_type` | string | همیشه `"bearer"` |
| `expires_in` | int | ثانیه |
| `user` | object | `UserOut` |

هدر: `Authorization: Bearer <access_token>`

#### دسترسی و درخواست رزرو

| فیلد | نوع | توضیح |
|---|---|---|
| `item_id` | int | |
| `start_at` / `end_at` | datetime | ISO با `Z` |
| `message` | string \| null | اختیاری |
| `is_available` | bool | |
| `min_duration_hours` | int | ۱ |
| `max_duration_days` | int | ۳۰ |
| `busy` | array | `[{start_at, end_at}]` — **بدون اطلاعات متقاضی** |
| `server_time` | datetime | برای هم‌ترازی ساعت کلاینت |
| `conflicts` | array | در `details` خطای ۴۰۹ |
| `requested` | object | `{start_at, end_at}` |
| `suggestions` | array | ۳ مورد `{start_at, end_at}` |

#### AI

| فیلد | نوع | توضیح |
|---|---|---|
| `query` | string | ورودی کاربر |
| `normalized_query` | string | پس از نرمال‌سازی فارسی |
| `interpreted_filters` | object | `{category, price_max}` استخراج‌شده یا `null` |
| `results` | array | `[{item, score, matched_terms}]` |
| `score` | float | ۰ تا ۱ |
| `matched_terms` | array[string] | برای شفافیت به داور |
| `meta.engine` | string | `"tfidf-v1"` |

### ۴.۳ Enumها (قفل)

```python
# app/core/constants.py  — مالک: اسرا · تغییر: PR + ۲ تأیید
class ReservationStatus(str, Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    ACTIVE    = "active"
    RETURNED  = "returned"
    REJECTED  = "rejected"
    CANCELLED = "cancelled"
    EXPIRED   = "expired"

class ItemCategory(str, Enum):
    TOOLS       = "tools"
    ELECTRONICS = "electronics"
    OUTDOOR     = "outdoor"
    HOUSEHOLD   = "household"
    OTHER       = "other"

class ItemCondition(str, Enum):
    NEW   = "new"
    GOOD  = "good"
    FAIR  = "fair"
    WORN  = "worn"

class ReturnedBy(str, Enum):
    LENDER   = "lender"
    BORROWER = "borrower"
```

**برچسب‌های فارسی UI** (شقایق، `frontend/src/constants.js` — همان مقادیر، عیناً):

```js
export const STATUS_LABEL = {
  pending:   "در انتظار تأیید",
  approved:  "تأیید شده",
  active:    "در حال امانت",
  returned:  "بازگشت داده شده",
  rejected:  "رد شده",
  cancelled: "لغو شده",
  expired:   "منقضی شده",
};

export const STATUS_COLOR = {
  pending:   "warning",
  approved:  "info",
  active:    "success",
  returned:  "neutral",
  rejected:  "danger",
  cancelled: "neutral",
  expired:   "neutral",
};

export const CATEGORY_LABEL = {
  tools:       "ابزار",
  electronics: "دیجیتال و برق",
  outdoor:     "کمپینگ و فضای باز",
  household:   "خانه و آشپزخانه",
  other:       "سایر",
};

export const CONDITION_LABEL = {
  new:  "نو",
  good: "در حد نو",
  fair: "کارکرده",
  worn: "فرسوده",
};

// قاعده: هیچ کلید انگلیسی در UI دیده نمی‌شود.
```

> ⚠️ **تست هم‌ترازی enum:** اگر ثنا یک وضعیت اضافه کرد و شقایق اضافه نکرد، تگ ناشناخته در UI ظاهر می‌شود. پس هر تغییر enum = یک PR شامل `constants.py` + `constants.js` + همین فایل.

---

## ۵) مدل داده و SQL

### ۵.۱ نمای کلی

```
users 1 ──< items 1 ──< reservations >── 1 users (borrower)
```

- یک کاربر چند وسیله دارد (`items.owner_id`).
- یک وسیله چند رزرو دارد (`reservations.item_id`).
- یک کاربر چند رزرو به‌عنوان متقاضی دارد (`reservations.borrower_id`).
- **صاحب وسیله نمی‌تواند وسیلهٔ خودش را رزرو کند** (`owner_id != borrower_id`).

### ۵.۲ جدول `users` (مالک: اسرا)

| ستون | نوع | قید |
|---|---|---|
| `id` | `BIGINT` identity | PK |
| `email` | `TEXT` | NOT NULL، UNIQUE، `CHECK (email = lower(email))` |
| `password_hash` | `TEXT` | NOT NULL |
| `full_name` | `TEXT` | NOT NULL، `CHECK (char_length(full_name) BETWEEN 2 AND 80)` |
| `phone` | `TEXT` | NULL |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `now()` |

### ۵.۳ جدول `items` (مالک: اسرا)

| ستون | نوع | قید |
|---|---|---|
| `id` | `BIGINT` identity | PK |
| `owner_id` | `BIGINT` | NOT NULL FK → `users(id)` ON DELETE CASCADE |
| `title` | `TEXT` | NOT NULL، `CHECK (char_length(title) BETWEEN 3 AND 120)` |
| `description` | `TEXT` | NOT NULL DEFAULT `''` |
| `category` | `item_category` | NOT NULL |
| `condition` | `item_condition` | NOT NULL DEFAULT `'good'` |
| `price_per_day` | `INTEGER` | NOT NULL DEFAULT 0، `CHECK (price_per_day >= 0)` |
| `image_url` | `TEXT` | NULL |
| `is_active` | `BOOLEAN` | NOT NULL DEFAULT `true` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `now()` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `now()` |

ایندکس‌ها: `(owner_id)`, `(category)`, `(is_active)`, `(price_per_day)`

### ۵.۴ جدول `reservations` (مالک: ثنا)

| ستون | نوع | قید |
|---|---|---|
| `id` | `BIGINT` identity | PK |
| `item_id` | `BIGINT` | NOT NULL FK → `items(id)` ON DELETE CASCADE |
| `borrower_id` | `BIGINT` | NOT NULL FK → `users(id)` ON DELETE CASCADE |
| `start_at` | `TIMESTAMPTZ` | NOT NULL |
| `end_at` | `TIMESTAMPTZ` | NOT NULL، `CHECK (end_at > start_at)` |
| `status` | `reservation_status` | NOT NULL DEFAULT `'pending'` |
| `total_price` | `INTEGER` | NOT NULL DEFAULT 0، `CHECK (total_price >= 0)` |
| `message` | `TEXT` | NULL، `CHECK (char_length(message) <= 500)` |
| `decision_note` | `TEXT` | NULL |
| `cancel_reason` | `TEXT` | NULL |
| `returned_by` | `TEXT` | NULL، `CHECK (returned_by IN ('lender','borrower'))` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `now()` |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL DEFAULT `now()` |
| `approved_at` | `TIMESTAMPTZ` | NULL |
| `handover_at` | `TIMESTAMPTZ` | NULL |
| `returned_at` | `TIMESTAMPTZ` | NULL |
| `closed_at` | `TIMESTAMPTZ` | NULL |

### ۵.۵ ویو `v_item_busy` (فقط ثنا — اسرا از آن استفاده نمی‌کند)

```sql
CREATE VIEW v_item_busy AS
SELECT item_id, id AS reservation_id, start_at, end_at, status
FROM reservations
WHERE status IN ('pending','approved','active');
```

### ۵.۶ SQL مرجع مایگریشن‌ها

#### `0001_init` — مالک: **اسرا** (تا T+00:40 باید روی `main` باشد)

```sql
-- ext برای قید exclusion در 0002 (ثنا به آن نیاز دارد)
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TYPE item_category  AS ENUM ('tools','electronics','outdoor','household','other');
CREATE TYPE item_condition AS ENUM ('new','good','fair','worn');

CREATE TABLE users (
    id            BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE CHECK (email = lower(email)),
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL CHECK (char_length(full_name) BETWEEN 2 AND 80),
    phone         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE items (
    id            BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    owner_id      BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title         TEXT NOT NULL CHECK (char_length(title) BETWEEN 3 AND 120),
    description   TEXT NOT NULL DEFAULT '',
    category      item_category  NOT NULL,
    condition     item_condition NOT NULL DEFAULT 'good',
    price_per_day INTEGER NOT NULL DEFAULT 0 CHECK (price_per_day >= 0),
    image_url     TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_items_owner    ON items(owner_id);
CREATE INDEX idx_items_category ON items(category);
CREATE INDEX idx_items_active   ON items(is_active);
CREATE INDEX idx_items_price    ON items(price_per_day);
```

#### `0002_reservations` — مالک: **ثنا** (وابسته به 0001)

```sql
CREATE TYPE reservation_status AS ENUM
    ('pending','approved','active','returned','rejected','cancelled','expired');

CREATE TABLE reservations (
    id            BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    item_id       BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    borrower_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    start_at      TIMESTAMPTZ NOT NULL,
    end_at        TIMESTAMPTZ NOT NULL,
    status        reservation_status NOT NULL DEFAULT 'pending',
    total_price   INTEGER NOT NULL DEFAULT 0 CHECK (total_price >= 0),
    message       TEXT CHECK (char_length(message) <= 500),
    decision_note TEXT,
    cancel_reason TEXT,
    returned_by   TEXT CHECK (returned_by IN ('lender','borrower')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at   TIMESTAMPTZ,
    handover_at   TIMESTAMPTZ,
    returned_at   TIMESTAMPTZ,
    closed_at     TIMESTAMPTZ,
    CONSTRAINT end_after_start CHECK (end_at > start_at)
);

-- 🔴 قلب پروژه: هیچ دو رزرو فعال/درانتظار روی یک وسیله هم‌پوشانی ندارند
ALTER TABLE reservations
  ADD CONSTRAINT no_overlap
  EXCLUDE USING gist (
    item_id WITH =,
    tstzrange(start_at, end_at, '[)') WITH &&
  )
  WHERE (status IN ('pending','approved','active'));

CREATE INDEX idx_res_item_time  ON reservations(item_id, start_at);
CREATE INDEX idx_res_borrower   ON reservations(borrower_id, created_at DESC);
CREATE INDEX idx_res_pending    ON reservations(created_at) WHERE status = 'pending';
CREATE INDEX idx_res_status     ON reservations(status);
```

**نکات اجرایی برای ثنا:**

- `op.execute()` برای `EXCLUDE` (Alembic آن را به‌صورت خودکار نمی‌شناسد) و در `downgrade` اول `DROP CONSTRAINT`.
- `CREATE TYPE` را در مایگریشن **صریح** بنویس؛ وگرنه `sa.Enum` ممکن است در downgrade خطا بدهد.
- بعد از نوشتن `0002`، `alembic downgrade base && alembic upgrade head` را دو بار تست کن. مایگریشن یک‌طرفه = دردسر دمو.

### ۵.۷ قراردادهای ORM

- `updated_at` با `onupdate=func.now()` در SQLAlchemy به‌روز می‌شود؛ **دستی ست نکن**.
- همهٔ `datetime`ها `timezone=True`.
- رابطه‌ها lazy: `item`, `borrower` با `joinedload` در کوئری‌های لیست (جلوگیری از N+1).
- حذف وسیله = **soft delete** (`is_active=false`)؛ چون `reservations` به آن ارجاع دارد.

---

## ۶) ماشین وضعیت و قواعد امانت

### ۶.۱ جدول گذارهای مجاز (قفل — حفظ کن)

| از | به | چه کسی | اندپوینت | شرط | در صورت تخلف |
|---|---|---|---|---|---|
| `pending` | `approved` | **صاحب وسیله** | `POST /reservations/{id}/approve` | هنوز منقضی نشده | 409 `INVALID_TRANSITION` |
| `pending` | `rejected` | **صاحب وسیله** | `POST /reservations/{id}/reject` | — | 409 `INVALID_TRANSITION` |
| `pending` | `cancelled` | صاحب وسیله **یا** متقاضی | `POST /reservations/{id}/cancel` | — | 409 `INVALID_TRANSITION` |
| `pending` | `expired` | **سیستم** | خودکار (lazy) | `created_at + 24h < now()` | — |
| `approved` | `active` | **صاحب وسیله** | `POST /reservations/{id}/handover` | — | 409 `INVALID_TRANSITION` |
| `approved` | `cancelled` | صاحب وسیله **یا** متقاضی | `POST /reservations/{id}/cancel` | — | 409 `INVALID_TRANSITION` |
| `active` | `returned` | صاحب وسیله **یا** متقاضی | `POST /reservations/{id}/return` | `returned_by` لازم | 409 `INVALID_TRANSITION` |
| `returned` / `rejected` / `cancelled` / `expired` | — | **هیچ‌کس** | — | وضعیت نهایی | 409 `INVALID_TRANSITION` |

هر گذار باید **اتمیک** باشد: قفل ردیف (`SELECT … FOR UPDATE`)، بررسی وضعیت فعلی، بررسی نقش، به‌روزرسانی وضعیت + مهر زمانی مربوطه، `commit`.

```
                approve
   pending ──────────────► approved ──handover──► active ──return──► returned
      │  │                     │
      │  └──cancel──► cancelled ◄┘
      ├──reject──► rejected
      └──(24h)───► expired
```

### ۶.۲ قواعد زمان و قیمت

| قاعده | مقدار |
|---|---|
| بازه | نیمه‌باز `[start_at, end_at)` — پایان **شامل نمی‌شود** |
| مجاورت | ۱۰–۱۲ و ۱۲–۱۴ **هر دو مجاز** (بدون هم‌پوشانی) |
| حداقل مدت | ۱ ساعت |
| حداکثر مدت | ۳۰ روز |
| گذشته | `start_at` باید ≥ `now() - 5min` (تحمل اختلاف ساعت) |
| افق آینده | `start_at` ≤ `now() + 180 روز` |
| منطقهٔ زمانی | همه‌چیز UTC؛ نمایش شمسی/تهران فقط در فرانت |
| قیمت | `total_price = price_per_day × max(1, ceil((end_at - start_at) / 24h))` |
| واحد پول | تومان، عدد صحیح (بدون اعشار) |

### ۶.۳ انقضای خودکار (lazy expire — بدون cron)

قبل از **هر** عملیات مربوط به رزرو (ساخت، لیست، گذار)، در همان تراکنش:

```sql
UPDATE reservations
   SET status = 'expired', closed_at = now(), updated_at = now()
 WHERE status = 'pending'
   AND created_at < now() - interval '24 hours';
```

سپس رزرو هدف دوباره خوانده می‌شود. این کار باعث می‌شود:
- بازهٔ رزروهای رهاشده آزاد شود،
- تأیید یک رزرو منقضی → `409 INVALID_TRANSITION` با پیام «این درخواست منقضی شده است».
- هیچ سرویس جانبی (Redis/Celery) لازم نباشد.

> این `UPDATE` را **ثنا** در `lifecycle.py` می‌نویسد و در سه نقطه صدا می‌زند: `create_reservation`, `list_my_reservations`, `get_reservation`, و ابتدای هر گذار.

### ۶.۴ قواعد همزمانی (سه لایه)

| لایه | ابزار | چه چیزی را تضمین می‌کند |
|---|---|---|
| ۱ | `SELECT id FROM items WHERE id=:id FOR UPDATE` | سریال‌سازی درخواست‌های یک وسیله؛ امکان محاسبهٔ پیشنهاد جایگزین بدون race |
| ۲ | بررسی `NOT EXISTS` هم‌پوشانی | پیام خطای سریع و قابل‌فهم |
| ۳ | قید `EXCLUDE no_overlap` | ضامن نهایی، حتی اگر کد باگ داشته باشد → `23P01` |

**الگوی تراکنش ثبت رزرو (اسکلت برای ثنا):**

```python
def create_reservation(db: Session, borrower: User, payload: ReservationCreate) -> Reservation:
    start, end = validate_window(payload.start_at, payload.end_at)   # min/max/past

    item = db.execute(
        select(Item).where(Item.id == payload.item_id).with_for_update()
    ).scalar_one_or_none()
    if item is None or not item.is_active:
        raise AppError("NOT_FOUND", 404, "وسیله پیدا نشد.")
    if item.owner_id == borrower.id:
        raise AppError("CANNOT_BOOK_OWN_ITEM", 403, "نمی‌توانید وسیلهٔ خودتان را رزرو کنید.")

    expire_stale_pending(db)

    conflicts = find_conflicts(db, item.id, start, end)
    if conflicts:
        suggestions = build_suggestions(db, item.id, start, end, conflicts)
        raise AppError(
            "SLOT_CONFLICT", 409,
            "این بازه قبلاً رزرو شده است. یکی از بازه‌های پیشنهادی را انتخاب کنید.",
            details={"item_id": item.id,
                     "requested": {"start_at": iso(start), "end_at": iso(end)},
                     "conflicts": conflicts,
                     "suggestions": suggestions},
        )

    res = Reservation(item_id=item.id, borrower_id=borrower.id,
                      start_at=start, end_at=end, status="pending",
                      total_price=calc_price(item.price_per_day, start, end),
                      message=payload.message)
    db.add(res)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()                                   # پس از rollback، session دوباره قابل استفاده است
        if sqlstate(exc) == "23P01":                    # exclusion_violation
            conflicts = find_conflicts(db, item.id, start, end)   # کوئری تازه، تراکنش تازه
            suggestions = build_suggestions(db, item.id, start, end, conflicts)
            raise AppError("SLOT_CONFLICT", 409, "این بازه همین لحظه توسط کاربر دیگری رزرو شد.",
                           details={"item_id": item.id,
                                    "requested": {"start_at": iso(start), "end_at": iso(end)},
                                    "conflicts": conflicts, "suggestions": suggestions})
        raise
    db.refresh(res)
    return res


def sqlstate(exc: IntegrityError) -> str | None:
    """psycopg3 → .sqlstate ؛ psycopg2 → .pgcode"""
    orig = exc.orig
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
```

**نکات حتمی:**
- کد خطا را از `exc.orig` بخوان (هرگز از متن پیام). psycopg3 صفت `sqlstate` دارد، psycopg2 صفت `pgcode` — تابع `sqlstate()` بالا هر دو را پوشش می‌دهد.
- پیشنهادها را **پس از** `rollback` با کوئری تازه بساز؛ استفاده از نتایج کوئریِ تراکنشِ شکست‌خورده ممنوع.
- ترتیب `commit` → `rollback` → کوئری تازه → `raise` را عوض نکن.
- `expire_stale_pending` را قبل از بررسی تداخل صدا بزن، وگرنه رزرو منقضی، بازه را الکی اشغال می‌کند.

**الگوریتم ۳ پیشنهاد جایگزین:**

1. برای هر تداخل: `suggest_1 = [end_at_conflict, end_at_conflict + duration)` و `suggest_2 = [start_conflict - duration, start_conflict)`.
2. `suggest_3 = [start + 24h, end + 24h)`.
3. هر کاندید باید: در آینده باشد، از `now` نگذرد، با هیچ بازهٔ مشغول دیگری تداخل نداشته باشد (`free_item_ids` یا `assert_bookable`).
4. حداکثر ۳ مورد، مرتب‌شده بر اساس نزدیکی به بازهٔ درخواستی. اگر کمتر از ۳ شد، اشکالی ندارد.

### ۶.۵ `permissions` — منطق مشترک (ثنا می‌سازد، شقایق مصرف می‌کند)

```python
def build_permissions(res: Reservation, user: User) -> dict[str, bool]:
    is_lender   = res.item.owner_id == user.id
    is_borrower = res.borrower_id == user.id
    return {
        "can_approve":  is_lender   and res.status == "pending",
        "can_reject":   is_lender   and res.status == "pending",
        "can_cancel":   (is_lender or is_borrower) and res.status in ("pending", "approved"),
        "can_handover": is_lender   and res.status == "approved",
        "can_return":   (is_lender or is_borrower) and res.status == "active",
    }
```

**قانون فرانت:** دکمه‌ها **فقط** از `permissions` ساخته می‌شوند. شقایق هیچ‌جا `status === "pending" && owner_id === me` نمی‌نویسد. این کار جلوی دکمه‌های اشتباه و ناسازگاری دو منطق را می‌گیرد.

---

## ۷) قرارداد API

### ۷.۰ قواعد کلی

| موضوع | قاعده |
|---|---|
| Base URL | `http://localhost:8000/api/v1` (فرانت: `VITE_API_BASE`) |
| استثنا | `GET /health` بیرون از `/api/v1` |
| محتوا | `Content-Type: application/json` (به‌جز آپلود که نداریم) |
| احراز هویت | `Authorization: Bearer <access_token>` |
| تاریخ‌ها | رشتهٔ ISO-8601 با `Z`: `"2026-11-01T10:00:00Z"` |
| پاسخ موفق | `{"data": ...}` یا `{"data": [...], "meta": {...}}` |
| پاسخ خطا | `{"error": {"code", "message", "details"}}` |
| کد وضعیت ساخت | `201`؛ سایر موفق‌ها `200` |
| فیلد اضافی در بدنه | `422 VALIDATION_ERROR` (چون `extra="forbid"`) |
| Zwnj/فارسی | پیام‌های `message` فارسی و آمادهٔ نمایش؛ `code` انگلیسی |
| Swagger | `/docs` باید همه‌ی این‌ها را با `response_model` نشان دهد |

### ۷.۱ فهرست کامل اندپوینت‌ها

| # | متد و مسیر | کار | احراز | مالک |
|---|---|---|---|---|
| 1 | `GET /health` | سلامت اپ + DB | — | اسرا |
| 2 | `GET /api/v1/categories` | دسته‌ها + تعداد وسایل | — | اسرا |
| 3 | `POST /api/v1/auth/register` | ثبت‌نام | — | اسرا |
| 4 | `POST /api/v1/auth/login` | ورود | — | اسرا |
| 5 | `GET /api/v1/me` | پروفایل من | ✅ | اسرا |
| 6 | `GET /api/v1/items` | کاتالوگ + جست‌وجو + فیلتر | — | اسرا |
| 7 | `POST /api/v1/items` | ثبت وسیله | ✅ | اسرا |
| 8 | `GET /api/v1/items/{item_id}` | جزئیات | — | اسرا |
| 9 | `PATCH /api/v1/items/{item_id}` | ویرایش | ✅ مالک | اسرا |
| 10 | `DELETE /api/v1/items/{item_id}` | حذف نرم | ✅ مالک | اسرا |
| 11 | `GET /api/v1/me/items` | داشبورد صاحب وسیله | ✅ | اسرا |
| 12 | `GET /api/v1/items/{item_id}/availability` | بازه‌های اشغال | — | **ثنا** |
| 13 | `POST /api/v1/reservations` | ثبت درخواست | ✅ | **ثنا** |
| 14 | `GET /api/v1/me/reservations` | رزروهای من | ✅ | **ثنا** |
| 15 | `GET /api/v1/reservations/{reservation_id}` | جزئیات رزرو | ✅ طرفین | **ثنا** |
| 16 | `POST /api/v1/reservations/{id}/approve` | تأیید | ✅ صاحب | **ثنا** |
| 17 | `POST /api/v1/reservations/{id}/reject` | رد | ✅ صاحب | **ثنا** |
| 18 | `POST /api/v1/reservations/{id}/cancel` | لغو | ✅ طرفین | **ثنا** |
| 19 | `POST /api/v1/reservations/{id}/handover` | تحویل | ✅ صاحب | **ثنا** |
| 20 | `POST /api/v1/reservations/{id}/return` | بازگشت | ✅ طرفین | **ثنا** |
| 21 | `POST /api/v1/ai/search` | جست‌وجوی معنایی | — | شقایق |
| 22 | `GET /api/v1/ai/similar/{item_id}` | وسایل مشابه | — | شقایق |

---

### ۷.۲ `GET /health`

```json
// 200
{"status": "ok", "db": "up", "version": "0.1.0", "time": "2026-10-28T08:00:00Z"}
```

---

### ۷.۳ `GET /api/v1/categories`

```json
// 200
{"data": [
  {"value": "tools",       "count": 4},
  {"value": "electronics", "count": 3},
  {"value": "outdoor",     "count": 3},
  {"value": "household",   "count": 2}
]}
```

---

### ۷.۴ `POST /api/v1/auth/register`

```json
// Request
{"email": "asra@demo.ir", "password": "Demo1234!", "full_name": "اسرا", "phone": "0912..."}

// 201
{"data": {
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {"id": 2, "email": "asra@demo.ir", "full_name": "اسرا", "phone": null,
           "created_at": "2026-10-28T08:01:00Z"}
}}
```

خطاها: `409 EMAIL_ALREADY_EXISTS` — `422 VALIDATION_ERROR` (پسورد < ۸ کاراکتر، ایمیل نامعتبر)

**قواعد پسورد:** حداقل ۸ کاراکتر، حداقل یک حرف و یک رقم. ایمیل به lowercase تبدیل می‌شود.

---

### ۷.۵ `POST /api/v1/auth/login`

```json
// Request
{"email": "asra@demo.ir", "password": "Demo1234!"}

// 200 → همان ساختار register
```

خطا: `401 INVALID_CREDENTIALS` با پیام «ایمیل یا رمز عبور اشتباه است.» (بدون افشای کدام‌یک)

---

### ۷.۶ `GET /api/v1/me`

```json
// 200
{"data": {"id": 2, "email": "asra@demo.ir", "full_name": "اسرا", "phone": null,
          "created_at": "2026-10-28T08:01:00Z"}}
```

خطا: `401 UNAUTHORIZED`

---

### ۷.۷ `GET /api/v1/items`

**پارامترهای کوئری:**

| پارامتر | نوع | پیش‌فرض | توضیح |
|---|---|---|---|
| `q` | string | — | جست‌وجو در `title` و `description` (ILIKE) |
| `category` | enum | — | یکی از مقادیر `categories` |
| `condition` | enum | — | |
| `price_max` | int | — | سقف قیمت روزانه |
| `owner_id` | int | — | وسایل یک کاربر |
| `available_from` | datetime | — | باید با `available_to` همراه باشد |
| `available_to` | datetime | — | |
| `sort` | `newest\|price_asc\|price_desc` | `newest` | |
| `page` | int ≥1 | 1 | |
| `limit` | int 1..100 | 20 | |

```json
// 200
{"data": [
  {
    "id": 3,
    "owner_id": 4,
    "title": "دریل برقی بوش",
    "description": "دریل چکشی ۷۵۰ وات، همراه با بیت‌ست کامل.",
    "category": "tools",
    "condition": "good",
    "price_per_day": 50000,
    "image_url": "https://picsum.photos/seed/drill/600/400",
    "is_active": true,
    "owner": {"id": 4, "full_name": "شقایق"},
    "created_at": "2026-10-20T09:00:00Z",
    "updated_at": "2026-10-20T09:00:00Z"
  }
],
 "meta": {"page": 1, "limit": 20, "total": 1, "total_pages": 1, "has_next": false}}
```

**قواعد:**
- فقط `is_active = true`.
- اگر `available_from`/`available_to` داده شد: اعتبارسنجی بازه، سپس فیلتر با `free_item_ids()` (ثنا). اسرا **هیچ** کوئری روی `reservations` نمی‌نویسد.
- `q` خالی = بدون فیلتر. حداکثر طول `q` = ۱۰۰.
- مرتب‌سازی پیش‌فرض: `created_at DESC, id DESC`.

---

### ۷.۸ `POST /api/v1/items` (نیازمند توکن)

```json
// Request
{
  "title": "دریل برقی بوش",
  "description": "دریل چکشی ۷۵۰ وات همراه با بیت‌ست.",
  "category": "tools",
  "condition": "good",
  "price_per_day": 50000,
  "image_url": "https://picsum.photos/seed/drill/600/400"
}

// 201 → {"data": <item کامل با owner>}
```

`owner_id` **هرگز** از بدنه خوانده نمی‌شود؛ از توکن گرفته می‌شود (جلوگیری از جعل مالکیت).

---

### ۷.۹ `GET /api/v1/items/{item_id}`

```json
// 200 → {"data": <item با owner>}
// 404 NOT_FOUND  → {"error": {"code": "NOT_FOUND", "message": "وسیله پیدا نشد.", "details": null}}
```

---

### ۷.۱۰ `PATCH /api/v1/items/{item_id}` — فقط مالک

بدنه: هر زیرمجموعه‌ای از فیلدهای قابل ویرایش (`title`, `description`, `category`, `condition`, `price_per_day`, `image_url`, `is_active`). فیلد ارسال‌نشده = بدون تغییر.

```json
// 200 → {"data": <item به‌روزشده>}
```

خطاها: `403 FORBIDDEN` (غیرمالک) · `404 NOT_FOUND`

---

### ۷.۱۱ `DELETE /api/v1/items/{item_id}` — فقط مالک (حذف نرم)

```json
// 200
{"data": {"id": 3, "is_active": false}}
```

اگر رزرو `pending`/`approved`/`active` روی این وسیله وجود داشته باشد → `409 ITEM_HAS_ACTIVE_RESERVATIONS` با پیام «ابتدا رزروهای فعال این وسیله را تعیین تکلیف کنید.»
(اسرا این بررسی را **از `availability.py` یا یک تابع مشترک** می‌گیرد، نه با کوئری مستقیم؛ در عمل `has_active_reservations(item_id)` در `services/availability.py` تعریف می‌شود.)

---

### ۷.۱۲ `GET /api/v1/me/items`

```json
// 200
{"data": [
  {
    "id": 3, "owner_id": 4, "title": "دریل برقی بوش", "category": "tools",
    "condition": "good", "price_per_day": 50000, "image_url": "...",
    "is_active": true, "owner": {"id": 4, "full_name": "شقایق"},
    "created_at": "...", "updated_at": "...",
    "active_reservations_count": 1,
    "pending_requests_count": 2
  }
], "meta": {"page": 1, "limit": 20, "total": 1, "total_pages": 1, "has_next": false}}
```

- `active_reservations_count` = تعداد `approved` + `active`
- `pending_requests_count` = تعداد `pending` (برای نشان قرمز روی داشبورد)

---

### ۷.۱۳ `GET /api/v1/items/{item_id}/availability?from=…&to=…`

هر دو پارامتر اختیاری‌اند (پیش‌فرض: از الان تا ۳۰ روز آینده).

```json
// 200
{"data": {
  "item_id": 3,
  "from": "2026-11-01T00:00:00Z",
  "to": "2026-11-08T00:00:00Z",
  "is_available": true,
  "min_duration_hours": 1,
  "max_duration_days": 30,
  "busy": [
    {"start_at": "2026-11-02T10:00:00Z", "end_at": "2026-11-02T14:00:00Z"},
    {"start_at": "2026-11-04T08:00:00Z", "end_at": "2026-11-05T18:00:00Z"}
  ],
  "server_time": "2026-11-01T07:30:00Z"
}}
```

- `busy` فقط بازه‌های رزروهای `pending`/`approved`/`active` و **بدون** هیچ اطلاعاتی از متقاضی (حریم خصوصی).
- `is_available` = آیا کل بازهٔ `[from,to)` آزاد است.
- حداکثر ۱۰۰ ردیف `busy` (بیشتر شد: خطای `422 RANGE_TOO_WIDE`).

---

### ۷.۱۴ `POST /api/v1/reservations` (نیازمند توکن)

```json
// Request
{"item_id": 3, "start_at": "2026-11-02T10:00:00Z", "end_at": "2026-11-02T14:00:00Z",
 "message": "برای نصب قفسه لازمش دارم."}

// 201
{"data": {
  "id": 12,
  "item_id": 3,
  "borrower_id": 2,
  "start_at": "2026-11-02T10:00:00Z",
  "end_at": "2026-11-02T14:00:00Z",
  "status": "pending",
  "total_price": 50000,
  "message": "برای نصب قفسه لازمش دارم.",
  "decision_note": null,
  "cancel_reason": null,
  "returned_by": null,
  "created_at": "2026-11-01T07:31:00Z",
  "updated_at": "2026-11-01T07:31:00Z",
  "approved_at": null, "handover_at": null, "returned_at": null, "closed_at": null,
  "item": {"id": 3, "title": "دریل برقی بوش", "image_url": "...",
           "price_per_day": 50000, "owner_id": 4, "category": "tools", "condition": "good"},
  "borrower": {"id": 2, "full_name": "اسرا", "email": "asra@demo.ir"},
  "lender":   {"id": 4, "full_name": "شقایق", "email": "shaghayegh@demo.ir"},
  "permissions": {"can_approve": false, "can_reject": false,
                  "can_cancel": true, "can_handover": false, "can_return": false}
}}
```

**خطای ۴۰۹ (مهم‌ترین خطای پروژه):**

```json
// 409
{"error": {
  "code": "SLOT_CONFLICT",
  "message": "این بازه قبلاً رزرو شده است. یکی از بازه‌های پیشنهادی را انتخاب کنید.",
  "details": {
    "item_id": 3,
    "requested": {"start_at": "2026-11-02T12:00:00Z", "end_at": "2026-11-02T16:00:00Z"},
    "conflicts": [{"start_at": "2026-11-02T10:00:00Z", "end_at": "2026-11-02T14:00:00Z"}],
    "suggestions": [
      {"start_at": "2026-11-02T14:00:00Z", "end_at": "2026-11-02T18:00:00Z"},
      {"start_at": "2026-11-02T06:00:00Z", "end_at": "2026-11-02T10:00:00Z"},
      {"start_at": "2026-11-03T12:00:00Z", "end_at": "2026-11-03T16:00:00Z"}
    ]
  }
}}
```

سایر خطاها: `403 CANNOT_BOOK_OWN_ITEM` · `404 NOT_FOUND` · `409 ITEM_INACTIVE` · `422 VALIDATION_ERROR`

---

### ۷.۱۵ `GET /api/v1/me/reservations?role=borrower|lender|all&status=…&page&limit`

```json
// 200
{"data": [ <reservation کامل> ], "meta": {...}}
```

- `role=borrower` → `borrower_id = me` · `role=lender` → `item.owner_id = me` · `all` → هر دو (پیش‌فرض).
- `status` می‌تواند تک‌مقدار یا لیست باشد؟ **تک‌مقدار** (ساده نگه داریم).
- مرتب‌سازی: `created_at DESC`.
- `expire_stale_pending` قبل از کوئری اجرا می‌شود.

---

### ۷.۱۶ `GET /api/v1/reservations/{reservation_id}`

فقط `borrower` یا صاحب وسیله؛ دیگران `403 FORBIDDEN` با پیام «شما به این رزرو دسترسی ندارید.»

---

### ۷.۱۷–۷.۲۱ اندپوینت‌های گذار

| اندپوینت | بدنه | پاسخ موفق | خطاهای خاص |
|---|---|---|---|
| `POST /reservations/{id}/approve` | `{"decision_note": "..."}` (اختیاری) | `200` + reservation | `403 FORBIDDEN` · `409 INVALID_TRANSITION` |
| `POST /reservations/{id}/reject` | `{"decision_note": "..."}` (اختیاری) | `200` + reservation | همان |
| `POST /reservations/{id}/cancel` | `{"cancel_reason": "..."}` (اختیاری) | `200` + reservation | همان |
| `POST /reservations/{id}/handover` | `{}` یا بدون بدنه | `200` + reservation | همان |
| `POST /reservations/{id}/return` | `{"returned_by": "borrower"}` | `200` + reservation | همان + `422` اگر مقدار نامعتبر |

**نمونهٔ خطای گذار:**

```json
// 409
{"error": {"code": "INVALID_TRANSITION",
  "message": "این درخواست در وضعیت «رد شده» است و قابل تأیید نیست.",
  "details": {"reservation_id": 12, "current_status": "rejected", "attempted_action": "approve"}}}
```

**نمونهٔ خطای نقش:**

```json
// 403
{"error": {"code": "FORBIDDEN", "message": "فقط صاحب وسیله می‌تواند این درخواست را تأیید کند.", "details": null}}
```

> پیام‌های `message` باید **دقیق و راهنما** باشند؛ داور همین‌ها را می‌خواند.

---

### ۷.۲۲ `POST /api/v1/ai/search`

```json
// Request
{"query": "چیزی برای کمپینگ و شب‌مانی", "limit": 6, "category": null}

// 200
{"data": {
  "query": "چیزی برای کمپینگ و شب‌مانی",
  "normalized_query": "چیزی برای کمپینگ و شب مانی",
  "interpreted_filters": {"category": "outdoor", "price_max": null},
  "results": [
    {"item": { <item کامل> }, "score": 0.72, "matched_terms": ["چادر", "کمپینگ"]},
    {"item": { <item کامل> }, "score": 0.41, "matched_terms": ["کوله"]}
  ],
  "meta": {"count": 2, "engine": "tfidf-v1", "took_ms": 12}
}}
```

---

### ۷.۲۳ `GET /api/v1/ai/similar/{item_id}?limit=4`

```json
{"data": {"source_item_id": 3,
  "results": [{"item": {...}, "score": 0.66, "matched_terms": ["دریل"]}],
  "meta": {"count": 1, "engine": "tfidf-v1"}}}
```

---

### ۷.۲۴ جدول کامل کدهای خطا

| `code` | HTTP | چه وقت | چه کسی می‌سازد |
|---|---|---|---|
| `VALIDATION_ERROR` | 422 | ورودی نامعتبر (فیلد/بازه/طول) | هر دو |
| `UNAUTHORIZED` | 401 | توکن غایب/منقضی/نامعتبر | اسرا |
| `INVALID_CREDENTIALS` | 401 | ایمیل/پسورد غلط | اسرا |
| `FORBIDDEN` | 403 | نقش کافی نیست | هر دو |
| `CANNOT_BOOK_OWN_ITEM` | 403 | رزرو وسیلهٔ خود | ثنا |
| `NOT_FOUND` | 404 | موجودیت نیست | هر دو |
| `EMAIL_ALREADY_EXISTS` | 409 | ایمیل تکراری | اسرا |
| `SLOT_CONFLICT` | 409 | هم‌پوشانی بازه | **ثنا** |
| `INVALID_TRANSITION` | 409 | گذار غیرمجاز | **ثنا** |
| `ITEM_INACTIVE` | 409 | وسیله حذف/غیرفعال شده | ثنا |
| `ITEM_HAS_ACTIVE_RESERVATIONS` | 409 | حذف وسیلهٔ دارای رزرو فعال | اسرا (با تابع ثنا) |
| `RANGE_TOO_WIDE` | 422 | بازهٔ availability بیش از ۹۰ روز | ثنا |
| `INTERNAL_ERROR` | 500 | خطای پیش‌بینی‌نشده | هر دو |

**مرجع پیاده‌سازی خطا (اسرا، مشترک):**

```python
# app/core/errors.py
class AppError(Exception):
    def __init__(self, code: str, status_code: int, message: str, details: dict | None = None):
        self.code, self.status_code, self.message, self.details = code, status_code, message, details

# app/main.py
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )
```

`RequestValidationError` هم باید به همان قالب تبدیل شود:

```json
{"error": {"code": "VALIDATION_ERROR", "message": "ورودی نامعتبر است.",
  "details": {"fields": {"price_per_day": "باید بزرگ‌تر یا مساوی صفر باشد"}}}}
```

---

## ۸) فرانت‌اند (شقایق)

### ۸.۱ استک و ساختار

- **Vanilla JS (ES Modules)** + Vite + CSS خالص. بدون React/Vue.
- `dir="rtl"` و `lang="fa"` روی `<html>`.
- روتینگ ساده با `window.location.hash` (`#/items`, `#/items/3`, `#/my/items`…).
- یک `api/client.js` که همهٔ درخواست‌ها از آن عبور می‌کنند: تزریق توکن، پارس پاکت `data`/`error`، پرتاب `ApiError` با `code/message/details`.
- `USE_MOCK = true` تا وقتی بک آماده نشده؛ با `?mock=0` خاموش می‌شود.

### ۸.۲ صفحات و اندپوینت‌های هرکدام

| صفحه | مسیر | اندپوینت‌ها | اجزای اصلی |
|---|---|---|---|
| کاتالوگ | `#/` | `GET /items`, `GET /categories` | نوار جست‌وجو، چیپ دسته‌ها، فیلتر قیمت، گرید کارت، صفحه‌بندی، حالت خالی |
| جزئیات وسیله | `#/items/{id}` | `GET /items/{id}`, `GET /items/{id}/availability`, `POST /reservations` | گالری، مشخصات، تقویم بازه‌های اشغال، فرم رزرو، کارت صاحب وسیله |
| ورود | `#/login` | `POST /auth/login` | فرم، نمایش خطای ۴۰۱ |
| ثبت‌نام | `#/register` | `POST /auth/register` | فرم، اعتبارسنجی سمت کلاینت هم‌تراز بک |
| وسیلهٔ من — فرم | `#/items/new`, `#/items/{id}/edit` | `POST /items`, `PATCH /items/{id}` | فرم ۶ فیلدی، انتخاب دسته/وضعیت |
| داشبورد صاحب | `#/my/items` | `GET /me/items`, `GET /me/reservations?role=lender` | کارت‌های من، تب درخواست‌های در انتظار، دکمه‌های تأیید/رد از `permissions` |
| درخواست‌های من | `#/my/requests` | `GET /me/reservations?role=borrower` | تایم‌لاین وضعیت، لغو |
| دستیار هوشمند | `#/ai` | `POST /ai/search` | جعبهٔ جست‌وجو، چیپ تفسیر، نتایج با درصد تطابق |
| ۴۰۴ | هر مسیر ناشناس | — | پیام + بازگشت |

**قاعدهٔ سخت:** هر صفحه فقط از اندپوینت‌های ستون خودش استفاده می‌کند. اگر داده‌ای لازم شد که در API نیست، به بک بگو — در فرانت از خودت نساز.

### ۸.۳ کامپوننت‌ها و توکن‌های طراحی

**کامپوننت‌های الزامی (نام‌گذاری برای هماهنگی):**

`AppHeader`, `NavBar`, `ItemCard`, `ItemGrid`, `FilterBar`, `SearchInput`, `Pagination`, `Badge` (status), `Button`, `Input`, `Textarea`, `Select`, `DateRangeInput`, `Modal`, `Toast`, `EmptyState`, `Skeleton`, `ReservationCard`, `StatusTimeline`, `ConfirmDialog`, `ErrorBanner`, `SuggestionChips`.

**توکن‌ها (`styles/tokens.css`):**

```css
:root {
  --color-primary: #0f766e;
  --color-primary-600: #0d9488;
  --color-primary-50: #f0fdfa;
  --color-ink: #0f172a;
  --color-muted: #64748b;
  --color-line: #e2e8f0;
  --color-surface: #ffffff;
  --color-bg: #f8fafc;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-info: #2563eb;
  --color-danger: #dc2626;

  --radius-sm: 8px;  --radius-md: 12px;  --radius-lg: 20px;  --radius-full: 999px;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 24px; --space-6: 32px; --space-7: 48px;
  --shadow-sm: 0 1px 2px rgba(15,23,42,.06);
  --shadow-md: 0 8px 24px rgba(15,23,42,.08);
  --font-fa: "Vazirmatn", system-ui, sans-serif;
  --text-xs: 12px; --text-sm: 14px; --text-md: 16px; --text-lg: 20px; --text-xl: 28px;
}
```

**الزامات UI/UX:**

- اعداد فارسی در نمایش، اما **ورودی‌ها و ارسال به API همیشه لاتین**.
- هر کارت وسیله: تصویر (نسبت 3:2)، عنوان، دسته، قیمت روزانه، وضعیت.
- هر دکمهٔ عملیات **فقط** با `permissions` رندر می‌شود.
- حالت‌های `loading` / `empty` / `error` برای **هر** لیست و **هر** فرم. صفحهٔ سفید ممنوع.
- Mobile-first: یک ستون < ۷۶۸px، سه ستون ≥ ۱۰۲۴px.
- فوکوس کیبورد واضح (`:focus-visible`)، کنتراست حداقل 4.5:1.
- همهٔ متن‌ها فارسی؛ هیچ رشتهٔ انگلیسی در UI (حتی «OK»).

### ۸.۴ مدیریت توکن و وضعیت

```js
// store/auth.js
const KEY = "bb_token";           // قفل‌شده — همین نام
export const getToken = () => localStorage.getItem(KEY);
export const setToken = (t) => localStorage.setItem(KEY, t);
export const clearToken = () => localStorage.removeItem(KEY);
```

- بعد از `login`/`register`: ذخیرهٔ `access_token` + کاربر در `localStorage` (`bb_user` به‌صورت JSON).
- روی `401`: پاک کردن توکن، Toast «نشست شما منقضی شد»، هدایت به `#/login`.
- هیچ‌جا توکن را در URL یا `console.log` نگذار.

### ۸.۵ رفتار ۴۰۹ (مهم‌ترین UX پروژه)

```
کاربر بازه را انتخاب و «ثبت درخواست» را می‌زند
        │
        ▼
POST /reservations → 409 SLOT_CONFLICT
        │
        ├─ پیام فارسی در ErrorBanner (نه alert!)
        ├─ نمایش بازهٔ درخواستی + بازه(های) متداخل با برچسب «قبلاً رزرو شده»
        └─ ۳ دکمهٔ پیشنهاد: «۱۴:۰۰–۱۸:۰۰» → کلیک = پر کردن فرم + تلاش دوباره
```

- **هرگز** `alert()` نزن.
- هرگز پیام خام بک‌اند را بدون بررسی نمایش نده؛ `error.message` فارسی است، پس مستقیم قابل نمایش است.
- اگر `suggestions` خالی بود: پیام + دکمهٔ «انتخاب بازهٔ دیگر» که تقویم را باز می‌کند.
- همین رفتار برای `ITEM_INACTIVE` و `INVALID_TRANSITION` (با پیام مناسب و رفرش وضعیت).

### ۸.۶ Mock برای شروع سریع

فایل‌های `api/mock/items.json`, `item.json`, `reservations.json`, `availability.json`, `conflict.json` — **کپی دقیق از نمونه‌های بخش ۷**.
`client.js`:

```js
const MOCK = new URLSearchParams(location.search).get("mock") !== "0";
async function request(method, path, body) {
  if (MOCK) return mockRequest(method, path, body);   // از فایل‌های json
  ...
}
```

این باعث می‌شود شقایق از دقیقهٔ ۳۰ بدون بک‌اند کار کند و در T+02:00 فقط فلگ را بخواباند.

### ۸.۷ چک‌لیست UI

- [ ] بدون توکن، دکمه‌های «رزرو» → هدایت به `#/login` با `redirect` بازگشتی
- [ ] فرم رزرو `start_at < end_at` را قبل از ارسال چک می‌کند و پیام فارسی می‌دهد
- [ ] `datetime-local` → تبدیل صحیح به UTC ISO
- [ ] قیمت کل قبل از ثبت نمایش داده می‌شود (همان فرمول بک)
- [ ] تایم‌لاین وضعیت با `STATUS_LABEL`
- [ ] جدول‌ها/گریدها در ۳۶۰px نمی‌شکنند
- [ ] خالی‌بودن `image_url` → تصویر جانشین (`placeholder`)
- [ ] اسکلت لودینگ، نه پرش محتوا

---

## ۹) هوش مصنوعی — جست‌وجوی معنایی (شقایق)

### ۹.۱ تصمیم فنی (قفل)

| گزینه | تصمیم |
|---|---|
| LLM ابری (OpenAI/….) | ❌ نه — نیاز به کلید، شبکه، هزینه، ریسک در دمو |
| Embedding model محلی (sentence-transformers) | ❌ نه — دانلود مدل سنگین، ریسک نصب |
| **TF-IDF + نرمال‌سازی فارسی + دیکشنری مترادف** | ✅ **بله** — آفلاین، سریع، قطعی، قابل توضیح برای داور |

**نکتهٔ مهم:** روی ۱۲–۱۵ آیتم، TF-IDF با مترادف دستی از embedding هم بهتر جواب می‌دهد و توضیح‌پذیر است.

### ۹.۲ قرارداد

- `POST /api/v1/ai/search` — مالک: شقایق. **هیچ نوشتنی در DB ندارد.**
- ورودی: `{query, limit=6, category?}`
- خروجی: طبق بخش ۷.۲۲.
- `GET /api/v1/ai/similar/{item_id}?limit=4` — بر اساس شباهت توصیف/دسته.

### ۹.۳ الگوریتم

```python
PERSIAN_MAP = {"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه", "\u200c": " "}
SYNONYMS = {
    "کمپینگ": ["چادر", "کوله", "خوابگاه", "سفر", "طبیعت"],
    "نصب":    ["دریل", "پیچ", "ابزار"],
    "مهمانی": ["ظرف", "میز", "صندلی"],
    "سینما":  ["پروژکتور", "پرده"],
    ...
}

def normalize(text: str) -> str:
    text = text.lower()
    for a, b in PERSIAN_MAP.items(): text = text.replace(a, b)
    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def expand(text: str) -> str:
    tokens = normalize(text).split()
    extra = [w for t in tokens for w in SYNONYMS.get(t, [])]
    return " ".join(tokens + extra)
```

1. متن هر آیتم = `title + " " + description + " " + CATEGORY_LABEL[category] + " " + CONDITION_LABEL[condition]`
2. `TfidfVectorizer` (word, ngram 1–2) روی پیکرهٔ آیتم‌ها `fit` می‌شود (کش‌شده در حافظه؛ با تغییر آیتم‌ها invalidate).
3. بردار کوئریِ **گسترش‌یافته** با مترادف‌ها محاسبه و `cosine_similarity` گرفته می‌شود.
4. فیلتر `category` اگر داده شد؛ نتایج با `score > 0.05`؛ مرتب نزولی؛ `limit`.
5. اگر هیچ نتیجه‌ای نبود → **fallback** به `ILIKE` روی `title/description` (تابع `search_items` اسرا).
6. **اعتبارسنجی:** قبل از برگرداندن، هر آیتم باید `is_active` باشد. اگر `available_from/to` در بدنه آمد، از `free_item_ids()` ثنا فیلتر شود. (شقایق هیچ SQL روی `reservations` نمی‌نویسد.)

> کش: `@lru_cache` روی `(item_count, max_updated_at)` — ساده و کافی. اگر آیتم جدید اضافه شد، `updated_at` عوض می‌شود و کش می‌شکند.

### ۹.۴ `matched_terms` برای داور

برای هر نتیجه، ۳ واژهٔ مشترک با بالاترین `tfidf` را برگردان. این باعث می‌شود داور ببیند «چرا این نتیجه آمد» — خیلی مؤثرتر از یک عدد جادویی.

### ۹.۵ محدودیت‌های اعلام‌شده (در ارائه بگویید)

- پیکره کوچک است؛ TF-IDF به مترادف‌های دستی وابسته است.
- بدون تاریخچهٔ کاربر (personalization) — خارج از محدوده.
- مسیر ارتقا: جایگزینی `TfidfVectorizer` با embedding محلی بدون تغییر قرارداد API (فقط `engine` عوض می‌شود).

---

## ۱۰) تست و CI

### ۱۰.۱ حداقل تست‌های الزامی

| فایل | مالک | چه چیزی را ثابت می‌کند |
|---|---|---|
| `tests/test_auth.py` | اسرا | ثبت‌نام، ورود، ایمیل تکراری ۴۰۹، بدون توکن ۴۰۱، توکن نامعتبر ۴۰۱ |
| `tests/test_items.py` | اسرا | ساخت وسیله، ویرایش فقط توسط مالک (۴۰۳)، فیلتر دسته/قیمت، فیلتر تاریخ |
| `tests/test_transitions.py` | ثنا | همهٔ گذارهای مجاز + حداقل ۶ گذار غیرمجاز |
| `tests/test_concurrency.py` | ثنا | ۵۰ درخواست موازی → دقیقاً ۱ موفق |
| `tests/test_ai.py` | شقایق | کوئری مترادف نتیجه می‌دهد؛ آیتم غیرفعال برنمی‌گردد |

### ۱۰.۲ تست همزمانی (قلب ارائه)

```python
# tests/test_concurrency.py
import asyncio, httpx, pytest

@pytest.mark.asyncio
async def test_only_one_wins(client, seeded, token_borrower_factory):
    item_id = 3
    payload = {"item_id": item_id,
               "start_at": "2026-12-01T10:00:00Z",
               "end_at":   "2026-12-01T14:00:00Z"}
    tokens = [token_borrower_factory(i) for i in range(50)]   # ۵۰ کاربر متفاوت

    async with httpx.AsyncClient(base_url="http://api:8000", timeout=30) as ac:
        async def fire(tok):
            return await ac.post("/api/v1/reservations", json=payload,
                                 headers={"Authorization": f"Bearer {tok}"})
        responses = await asyncio.gather(*(fire(t) for t in tokens))

    codes = [r.status_code for r in responses]
    assert codes.count(201) == 1, f"expected exactly 1 success, got {codes.count(201)}"
    assert codes.count(409) == 49
    conflict = next(r for r in responses if r.status_code == 409).json()["error"]
    assert conflict["code"] == "SLOT_CONFLICT"
    assert len(conflict["details"]["suggestions"]) >= 1
```

**نکته:** ۵۰ کاربر متفاوت بساز، وگرنه ممکن است یک کاربر با خودش درگیر شود. همچنین دو تست مکمل بنویس:

- `test_adjacent_slots_ok`: ۱۰–۱۲ و ۱۲–۱۴ → هر دو ۲۰۱.
- `test_overlap_rejected`: ۱۰–۱۲ و ۱۱–۱۳ → دومی ۴۰۹.

### ۱۰.۳ CI (`.github/workflows/ci.yml` — مالک: ثنا)

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: {POSTGRES_USER: bb, POSTGRES_PASSWORD: bb, POSTGRES_DB: bb}
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U bb" --health-interval 5s
          --health-timeout 5s --health-retries 10
    env:
      DATABASE_URL: postgresql+psycopg://bb:bb@localhost:5432/bb
      SECRET_KEY: test-secret-key-at-least-32-characters
      PENDING_EXPIRE_HOURS: "24"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12", cache: pip}
      - run: pip install -r requirements.txt
      - run: alembic upgrade head
      - run: python -m app.seed
      - run: pytest -q
```

> CI سبز = شرط مرج به `main`. قرمز؟ همان لحظه فیکس یا revert؛ نه «بعداً».

---

## ۱۱) گیت و همکاری

### ۱۱.۱ شاخه‌ها

| شاخه | مالک | مبنا | مرج به |
|---|---|---|---|
| `main` | — | — | محافظت‌شده |
| `feat/api-platform` | اسرا | `main` | `main` (بعد از G1) |
| `feat/booking-engine` | ثنا | `main` (بعد از `0001`) | `main` (بعد از G3) |
| `feat/frontend` | شقایق | `main` (از دقیقهٔ ۰) | `main` (بعد از G2) |
| `chore/ci` | ثنا | `main` | `main` |
| `feat/ai-search` | شقایق | `main` (بعد از G4) | `main` |

### ۱۱.۲ ترتیب مرج (حتماً همین ترتیب)

1. اسرا: اسکلت + `0001_init` + auth + items → **مرج تا T+02:00**
2. ثنا: `0002_reservations` (ریبیس روی `main`) → مرج بعد از سبز شدن CI
3. شقایق: فرانت (مستقل، هر زمان بعد از G2)
4. شقایق: AI (بعد از G4)

**قانون:** `feat/booking-engine` قبل از وجود `0001` روی `main` **مرج نمی‌شود**. اگر اسرا تأخیر داشت، ثنا شاخه‌اش را روی `feat/api-platform` می‌بندد (نه روی `main`).

### ۱۱.۳ پیام کامیت

```
<type>(<scope>): <توضیح کوتاه فارسی>

type:  feat | fix | chore | docs | test | refactor
scope: auth | items | booking | db | ui | ai | infra | ci
```

مثال: `feat(booking): add exclusion constraint and atomic create`

### ۱۱.۴ قوانین PR

- هر PR ≤ ۴۰۰ خط تغییر. بیشتر شد → تقسیم کن.
- عنوان PR = همان پیام کامیت اصلی.
- توضیح PR: «چه چیزی»، «چرا»، «چطور تست شد»، «اسکرین‌شات» (برای UI).
- ریویو اجباری: مایگریشن → ثنا · قرارداد API → ثنا + شقایق · UI → شقایق · بقیه → یک نفر.
- **ریفکتور بعد از T+04:30 ممنوع.**

### ۱۱.۵ دستورهای گیت برای شروع سریع

```bash
git clone <repo> && cd borrowbetter
git checkout -b feat/api-platform        # اسرا
git checkout -b feat/frontend            # شقایق
git checkout -b feat/booking-engine      # ثنا

# قبل از هر push
git fetch origin && git rebase origin/main
git push -u origin HEAD
```

### ۱۱.۶ قالب اعلام تغییر قرارداد (فقط در گروه)

```
[CONTRACT CHANGE] v1.1
چه چیزی: افزودن فیلد `late_fee` به reservation
چرا: ...
اثر: schema B + response_model + types فرانت
تأیید: ثنا ✅ / شقایق ⏳
```

بدون این قالب، تغییر انجام‌شده = تخلف.

---

## ۱۲) خط زمانی ۶ ساعته

### ۱۲.۱ تکالیف قبل از مسابقه (T-minus — یک روز قبل)

| چه کسی | کار | زمان |
|---|---|---|
| **همه** | نصب و تست: Docker Desktop، Node 20، Python 3.12، `git config user.name` | ۴۵ دقیقه |
| **همه** | خواندن این فایل (کامل، یک‌بار) | ۲۵ دقیقه |
| **اسرا** | ساخت یک CRUD کوچک FastAPI + JWT + SQLAlchemy (تمرین عملی، همان الگو) | ۲ ساعت |
| **اسرا** | تست `docker compose` با postgres خالی + اتصال موفق | ۳۰ دقیقه |
| **ثنا** | تمرین قید `EXCLUDE` روی یک جدول نمونه در پستگرس محلی | ۴۵ دقیقه |
| **ثنا** | آماده کردن اسکلت `Dockerfile`/`alembic`/`pytest` در یک ریپوی تمرینی | ۱ ساعت |
| **شقایق** | طراحی ۶ فریم اصلی در فیگما + استخراج توکن‌ها | ۲ ساعت |
| **شقایق** | ساخت mock JSONها از روی بخش ۷ همین فایل | ۴۵ دقیقه |
| **همه** | تمرین ۲ دقیقه‌ای «دمو» به‌صورت شفاهی (بدون کد) | ۱۵ دقیقه |

> اگر این تکالیف انجام نشود، ۶ ساعت مسابقه صرف یادگیری ابزار می‌شود، نه ساختن محصول. **این مهم‌ترین بخش فایل است.**

### ۱۲.۲ خود مسابقه

| بازه | اسرا (A) | ثنا (B) | شقایق (C) | دروازه |
|---|---|---|---|---|
| **00:00–00:30** | ریپو، compose، `.env`، `/health`، خطای سراسری | مدل `reservation` + طراحی `0002` (بدون اجرا) | اسکلت Vite، `tokens.css`، چیدمان پایه، mock | **G0:** `docker compose up` سبز + mock UI |
| **00:30–01:15** | `0001` + auth (register/login/me) + `deps` | `0002` + `EXCLUDE` + تست قرمز همزمانی | کاتالوگ + کارت + فیلتر روی mock | — |
| **01:15–02:00** | CRUD items + `GET /items` + seed ۱۲ آیتم | `POST /reservations` اتمیک + `approve` + `permissions` — **`free_item_ids` تا T+02:30 روی `main`** | لاگین/ثبت‌نام + اتصال کاتالوگ به API واقعی | **G1 (02:00):** کل مسیر با `curl`: کاتالوگ → لاگین → رزرو |
| **02:00–03:00** | `GET /me/items` + PATCH/DELETE + قالب خطاها | `cancel` + `handover` + `return` + `INVALID_TRANSITION` | صفحهٔ جزئیات + فرم رزرو + رزرو واقعی از UI | **G2 (03:00):** رزرو از UI + تأیید از UI |
| **03:00–03:45** | فیلتر تاریخ با `free_item_ids()` + `available_from/to` | تست همزمانی سبز + `suggestions` + `availability` | UX خطای ۴۰۹ + چیپ پیشنهادها + داشبورد صاحب | **G3 (03:45):** ۴۰۹ با ۳ پیشنهاد کلیک‌پذیر |
| **03:45–04:30** | CORS، Swagger examples، seed نهایی، README | فیکس باگ‌ها، `expire` را در همه مسیرها، لاگ | داشبورد متقاضی + تایم‌لاین + «درخواست‌های من» | — |
| **04:30–05:15** | پشتیبانی یکپارچه‌سازی + تست دستی | ریویو AI + مرج نهایی + تگ | `POST /ai/search` + صفحهٔ دستیار | **G4 (05:15):** AI سبز |
| **05:15–06:00** | اجرای دمو #۱ | اجرای دمو #۲ + `git tag v0.1` | اسکرین‌شات‌ها + رفع باگ‌های UI | **G5:** یخ‌زدن کد + **G6:** دموی تمیز |

### ۱۲.۳ قواعد زمانی

- **T+00:30:** قرارداد ۱۰۰٪ قفل. هر تغییر بعدی = PR + ۲ تأیید + به‌روزرسانی نسخه.
- **T+02:00:** اگر G1 رد شد → **فوراً** از بخش ۱۳ حذف کنید، نه اینکه «۱۰ دقیقه دیگر».
- **T+04:30:** فقط باگ‌فیکس. `main` باید سبز باشد.
- **T+05:15:** کد یخ می‌زند. فقط متن ارائه و اسکرین‌شات.
- **T+05:30:** دموی کامل #۱. **T+05:45:** دموی کامل #۲. اگر هر دو سبز نبود، فیچرهای تزئینی را خاموش کنید.
- در هر دروازه، ۵ دقیقهٔ ایستاده: «چه چیزی سبز است؟ چه چیزی نیست؟ چه کسی گیر است؟»

### ۱۲.۴ اگر یک دروازه رد شد

| دروازه | اقدام فوری |
|---|---|
| G0 | اسکلت را از ریپوی تمرینی ثنا کپی کنید؛ داکر را رها و با `uvicorn` مستقیم اجرا کنید. |
| G1 | `GET /items` را با کوئری ساده (بدون فیلتر) تحویل دهید؛ فرانت را روی mock نگه دارید. |
| G2 | داشبوردها را حذف کنید؛ فقط جزئیات + رزرو + تأیید را نگه دارید. |
| G3 | حداقل: ۴۰۹ **بدون** پیشنهاد (پیام واضح) + تست ۵ درخواستی به‌جای ۵۰. |
| G4 | AI را از ارائه حذف کنید؛ صفحه را مخفی کنید (نه نصفه). |

---

## ۱۳) ترتیب حذف در صورت کمبود وقت

از بالا به پایین حذف کنید. **سه مورد آخر هرگز حذف نمی‌شوند.**

| # | فیچر | اثر حذف | قابل حذف تا |
|---|---|---|---|
| 1 | AI و جست‌وجوی معنایی | فقط بخش امتیازی | T+04:30 |
| 2 | `GET /ai/similar` | فقط صفحهٔ جزئیات یک بخش کم دارد | T+04:30 |
| 3 | داشبورد آماری | صفر (کسی انتظار ندارد) | T+03:30 |
| 4 | `GET /categories` (از enum در فرانت استفاده شود) | کم | T+03:00 |
| 5 | فیلتر `condition` | کم | T+03:00 |
| 6 | صفحه‌بندی (limit=100) | کم | T+03:00 |
| 7 | `PATCH /items` (فقط ساخت و حذف) | متوسط | T+03:30 |
| 8 | `GET /items?available_from` (فیلتر تاریخ در کاتالوگ) | متوسط | T+03:45 |
| 9 | «وسایل مشابه» | کم | T+04:00 |
| 10 | `decision_note` / `cancel_reason` (فقط null) | کم | T+03:00 |
| 11 | ⛔ **قید `EXCLUDE no_overlap` + رزرو اتمیک** | **فاجعه** — کل ارزش پروژه | هرگز |
| 12 | ⛔ **بررسی مالکیت و ۴۰۳** | **فاجعه** — داور تست می‌کند | هرگز |
| 13 | ⛔ **۴۰۹ با پیام قابل‌فهم** | **فاجعه** — سناریوی اصلی دمو | هرگز |

> اگر مجبور شدید بین «داشبورد زیبا» و «تست همزمانی سبز» یکی را انتخاب کنید، **تست** را انتخاب کنید. داوران کد و رفتار را می‌بینند، نه تعداد صفحه‌ها.

---

## ۱۴) Definition of Done هر نفر

### ۱۴.۱ اسرا (Backend A)

- [ ] `docker compose up --build` بدون خطا؛ `/health` → `db: "up"`
- [ ] `alembic upgrade head` روی دیتابیس خالی بدون خطا
- [ ] `python -m app.seed` دو بار اجرا شود و داده تکراری نسازد
- [ ] `POST /auth/register` و `/login` توکن برمی‌گردانند؛ `/me` با توکن کار می‌کند
- [ ] بدون توکن → `401 UNAUTHORIZED`؛ با توکن غیرمالک روی PATCH/DELETE → `403 FORBIDDEN`
- [ ] `GET /items` با `q`, `category`, `price_max`, `sort`, `page` کار می‌کند
- [ ] `GET /items?available_from&available_to` فقط وسایل آزاد در **کل** بازه را می‌دهد
- [ ] `GET /me/items` شمارنده‌های `active_reservations_count` و `pending_requests_count` را از توابع ثنا می‌گیرد
- [ ] همهٔ خطاها قالب `{"error": {...}}` دارند؛ `RequestValidationError` هم تبدیل شده
- [ ] `/docs` همهٔ اندپوینت‌ها را با نمونه نشان می‌دهد
- [ ] `pytest tests/test_auth.py tests/test_items.py` سبز
- [ ] README با دستورهای راه‌اندازی و کاربران دمو

### ۱۴.۲ ثنا (Backend B)

- [ ] `0002` قابل upgrade و downgrade است (دو بار تست شده)
- [ ] قید `no_overlap` در `\d reservations` دیده می‌شود
- [ ] ۱۰–۱۲ و ۱۲–۱۴ هر دو ثبت می‌شوند؛ ۱۰–۱۲ و ۱۱–۱۳ دومی ۴۰۹
- [ ] `POST /reservations` فقط با قفل ردیف + بررسی + درج کار می‌کند (اسکلت بخش ۶.۴)
- [ ] `pgcode` هندل شده و به `SLOT_CONFLICT` تبدیل می‌شود
- [ ] ۴۰۹ همیشه حداقل ۱ و حداکثر ۳ پیشنهاد دارد (اگر ممکن باشد) و پیشنهادها واقعاً آزادند
- [ ] همهٔ گذارها پیاده شده‌اند؛ گذار غیرمجاز → `INVALID_TRANSITION` با پیام فارسی
- [ ] `permissions` در پاسخ همهٔ اندپوینت‌های رزرو حاضر است
- [ ] `expire_stale_pending` در خواندن‌ها و گذارها اجرا می‌شود
- [ ] رزرو `cancelled/rejected/expired` بازه را قفل نمی‌کند (تست)
- [ ] `test_concurrency.py` (۵۰ درخواست) سبز و در CI
- [ ] CI روی GitHub Actions سبز؛ `main` محافظت‌شده

### ۱۴.۳ شقایق (Frontend + AI)

- [ ] ۸ صفحهٔ بخش ۸.۲ موجود و از طریق هدر قابل دسترسی
- [ ] هیچ کلید انگلیسی و هیچ متن انگلیسی در UI نیست
- [ ] نام فیلدها **عیناً** مطابق بخش ۴ (صفر تبدیل)
- [ ] دکمه‌های عملیات فقط از `permissions` ساخته می‌شوند
- [ ] ۴۰۹: پیام فارسی + بازهٔ متداخل + ۳ چیپ پیشنهاد کلیک‌پذیر
- [ ] `loading` / `empty` / `error` برای همهٔ لیست‌ها و فرم‌ها
- [ ] ریسپانسیو ۳۶۰px تا ۱۴۴۰px؛ RTL کامل
- [ ] توکن در `localStorage` با کلید `bb_token`؛ ۴۰۱ → خروج و هدایت به لاگین
- [ ] `datetime-local` → UTC ISO درست
- [ ] قیمت کل قبل از ثبت نمایش داده می‌شود
- [ ] `POST /ai/search` کار می‌کند؛ `matched_terms` نمایش داده می‌شود؛ آیتم غیرفعال برنمی‌گردد
- [ ] بدون بک‌اند (`?mock=1`) UI کامل قابل دیدن است

---

## ۱۵) چک‌لیست یکپارچه‌سازی نهایی (T+05:15 — همه با هم)

- [ ] دیتابیس از صفر: `docker compose down -v && docker compose up --build`
- [ ] `alembic upgrade head` و `seed` خودکار در استارتاپ اجرا شد
- [ ] ۴ کاربر و ۱۲ وسیله در کاتالوگ دیده می‌شود
- [ ] ثبت‌نام کاربر جدید از UI و ورود با آن
- [ ] جست‌وجوی «دریل» نتیجه می‌دهد؛ فیلتر دسته و قیمت کار می‌کند
- [ ] فیلتر تاریخ فقط وسایل آزاد را نشان می‌دهد
- [ ] رزرو ۱۰–۱۲ ثبت می‌شود؛ رزرو ۱۲–۱۴ برای همان وسیله ثبت می‌شود (مجاورت مجاز)
- [ ] رزرو ۱۱–۱۳ → ۴۰۹ + پیشنهاد
- [ ] دو تب همزمان، یک بازه → یکی موفق، یکی ۴۰۹ با پیام فارسی
- [ ] تأیید توسط صاحب وسیله؛ متقاضی نمی‌تواند تأیید کند (۴۰۳)
- [ ] تحویل → `active`؛ بازگشت با `returned_by` → `returned`
- [ ] رزرو لغوشده بازه را آزاد می‌کند (رزرو جدید موفق)
- [ ] داشبورد صاحب: شمارندهٔ درخواست‌های در انتظار درست است
- [ ] داشبورد متقاضی: تایم‌لاین وضعیت درست است
- [ ] `/docs` قابل استفاده است
- [ ] `pytest` سبز؛ CI سبز
- [ ] `git tag v0.1` زده شده و روی `main` است
- [ ] اسکرین‌شات ۴ صفحهٔ اصلی گرفته شده (برای اسلاید)
- [ ] دمو دو بار پشت سر هم بدون خطا اجرا شد

---

## ۱۶) ریسک‌ها و راه‌حل‌ها

| # | ریسک | احتمال | اثر | پیشگیری / واکنش |
|---|---|---|---|---|
| 1 | داکر روی ویندوز کند/گیر کند | بالا | بالا | حجم `pgdata` را نگه دار؛ اگر >۳ دقیقه شد، بدون داکر با `uvicorn` برو. |
| 2 | پورت ۸۰۰۰/۵۴۳۲ اشغال | متوسط | کم | `netstat -ano \| findstr :8000` و تغییر پورت در `.env` |
| 3 | خطای `passlib`/`bcrypt` | بالا | متوسط | `bcrypt==4.0.1` پین شود. اگر باز هم خطا: `pwdlib[argon2]`. |
| 4 | `CREATE EXTENSION btree_gist` مجوز ندارد | کم | بالا | کاربر پستگرس داکر superuser است؛ در dev مشکلی نیست. |
| 5 | Alembic enum را در downgrade نمی‌شناسد | متوسط | متوسط | `CREATE TYPE` صریح؛ تست `downgrade base`. |
| 6 | اختلاف ساعت کلاینت/سرور | متوسط | متوسط | `server_time` در availability + تحمل ۵ دقیقه. |
| 7 | `datetime-local` بدون `Z` → خطای ۴۲۲ | بالا | متوسط | تابع `toUtcIso()` در `format.js` (بخش ۱۸.۴) |
| 8 | اختلاف نام فیلد فرانت/بک | بالا | بالا | `extra="forbid"` در Pydantic → ۴۲۲ فوری؛ جدول بخش ۴. |
| 9 | N+1 در لیست رزروها | متوسط | کم | `joinedload(Reservation.item)`, `joinedload(item.owner)` |
| 10 | دو نفر روی `alembic/versions` | متوسط | بالا | قاعدهٔ «یک مایگریشن یک مالک» + ترتیب مرج بخش ۱۱.۲ |
| 11 | `main` قرمز نزدیک دمو | متوسط | بالا | تا T+05:15 تگ نزن؛ داشته باش `git reset --hard v0.1` |
| 12 | شقایق روی API نبوده گیر کند | بالا | بالا | mock از دقیقهٔ ۰؛ اگر اندپوینتی نیست، ۱۵ دقیقه صبر، بعد mock. |
| 13 | اسرا در `SELECT FOR UPDATE`/async گیر کند | متوسط | متوسط | **sync** استفاده می‌کنیم؛ الگوی آمادهٔ بخش ۶.۴ کپی شود. |
| 14 | کاربر «همه» را با هم قاطی کردن | کم | متوسط | ماکروها را قبل از شروع دمو ببندید. |
| 15 | اینترنت سالن قطع | متوسط | بالا | فونت لوکال، بدون CDN، بدون LLM ابری، تصاویر با `picsum` + placeholder محلی. |

---

## ۱۷) پروتکل ارتباط تیم

### ۱۷.۱ ریتم

| زمان | چه چیزی | مدت |
|---|---|---|
| T+00:00 | سینک شروع: خواندن دروازه‌ها و مالکیت | ۱۰ دقیقه |
| هر دروازه | سینک ایستاده: سبز/قرمز/گیر | ۵ دقیقه |
| T+04:30 | سینک یخ‌زدن | ۱۰ دقیقه |
| T+05:30 | دموی تمرینی #۱ | ۱۵ دقیقه |

### ۱۷.۲ قالب پیام‌ها (در گروه)

```
[BLOCK] روی <موضوع> گیر کرده‌ام. نیاز دارم <چیزی>. تخمین <N> دقیقه.
[DONE] <تسک> تمام شد. commit: <hash>. آمادهٔ تست: <لینک/دستور>
[CONTRACT CHANGE] v1.x — <خلاصه> — تأیید: <نام‌ها>
[REVIEW] PR #<n> آمادهٔ ریویو. ریویوور: <نام>
```

### ۱۷.۳ قوانین ارتباطی

1. **سؤال فنی را در گروه بپرس، نه DM.** جواب برای همه ارزش دارد.
2. **قبل از ۱۵ دقیقه سرچ شخصی مزاحم نشو؛ بعد از ۱۵ دقیقه حتماً بپرس.**
3. **دیباگ گروهی روی لپ‌تاپ یک نفر ممنوع** (بیش از ۵ دقیقه). اسکرین‌شیر کوتاه یا پیام متنی.
4. **هیچ‌کس کد دیگری را «سریع درست نمی‌کند».** پیام بده، مالک انجام می‌دهد.
5. **تصمیم شفاهی = تصمیم نگرفته.** هر تصمیم در بخش ۱۸.۶ ثبت می‌شود.
6. **در حضور داور، فقط یک نفر صحبت می‌کند** (شقایق برای UI، ثنا برای فنی). بقیه تأیید می‌کنند.

### ۱۷.۴ تقسیم نقش در ارائه

| بخش ارائه | گوینده |
|---|---|
| مسئله و ایده | اسرا |
| معماری و تضمین همزمانی | ثنا |
| دموی محصول | شقایق |
| جمع‌بندی و نقشهٔ راه | ثنا |

---

## ۱۸) ضمیمه‌ها

### ۱۸.۱ کاربران و دادهٔ دمو (seed — مالک: اسرا)

| ایمیل | پسورد | نام | نقش |
|---|---|---|---|
| `sana@demo.ir` | `Demo1234!` | ثنا | صاحب چند وسیله |
| `asra@demo.ir` | `Demo1234!` | اسرا | متقاضی |
| `shaghayegh@demo.ir` | `Demo1234!` | شقایق | صاحب یک وسیله |
| `demo@demo.ir` | `Demo1234!` | کاربر دمو | برای ثبت‌نام‌های تستی |

**۱۲ وسیله (حداقل):**

| # | عنوان | دسته | وضعیت | قیمت/روز | صاحب |
|---|---|---|---|---|---|
| 1 | دریل برقی بوش | tools | good | 50000 | ثنا |
| 2 | پیچ‌گوشتی برقی | tools | good | 30000 | ثنا |
| 3 | نردبان آلومینیومی ۴ متری | tools | fair | 40000 | ثنا |
| 4 | جعبه‌ابزار کامل | tools | new | 25000 | اسرا |
| 5 | پروژکتور خانگی | electronics | good | 90000 | ثنا |
| 6 | دوربین عکاسی کانن | electronics | new | 250000 | شقایق |
| 7 | بلندگوی بلوتوثی | electronics | good | 20000 | اسرا |
| 8 | چادر مسافرتی ۴ نفره | outdoor | good | 70000 | ثنا |
| 9 | کوله‌پشتی کوهنوردی | outdoor | fair | 35000 | اسرا |
| 10 | چراغ‌قوهٔ کمپینگ | outdoor | new | 10000 | ثنا |
| 11 | ماشین لباسشویی (امانتی!) | household | good | 300000 | شقایق |
| 12 | ست ظروف مهمانی | household | good | 15000 | اسرا |

**رزروهای نمونه (برای دموی آماده):** یکی `approved` برای فردا، یکی `returned` برای هفتهٔ قبل، یکی `pending` روی وسیلهٔ ثنا (تا دمو با یک کلیک شروع شود).

> ⚠️ seed نباید با قید `no_overlap` تصادم کند: بازه‌ها روی وسایل مختلف یا بازه‌های غیرهمپوشان.

### ۱۸.۲ اسکلت `availability.py` (تنها نقطهٔ اتصال — مالک: ثنا)

```python
# app/services/availability.py
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

def free_item_ids(db: Session, item_ids: list[int], start: datetime, end: datetime) -> set[int]:
    """زیرمجموعه‌ای از item_ids که در کل بازهٔ [start, end) آزادند."""
    if not item_ids:
        return set()

    rows = db.execute(text("""
        SELECT i.id
          FROM items i
         WHERE i.id = ANY(:ids)
           AND i.is_active
           AND NOT EXISTS (
                 SELECT 1 FROM reservations r
                  WHERE r.item_id = i.id
                    AND r.status IN ('pending','approved','active')
                    AND tstzrange(r.start_at, r.end_at, '[)')
                        && tstzrange(:start_at, :end_at, '[)')
               )
    """), {"ids": item_ids, "start_at": start, "end_at": end}).scalars().all()
    return set(rows)


def assert_bookable(db: Session, item_id: int, start: datetime, end: datetime) -> None:
    """اگر بازه آزاد نیست، AppError('SLOT_CONFLICT', 409, ...) پرتاب می‌کند."""
    ...


def has_active_reservations(db: Session, item_id: int) -> bool:
    """برای DELETE /items/{id} — اسرا صدا می‌زند، مالکیت کد با ثنا."""
    ...
```

> این سه تابع **تنها** راه دسترسی اسرا و شقایق به دادهٔ رزرو هستند. امضاها قفل‌اند.
>
> ⏰ **`free_item_ids` باید تا T+02:30 روی `main` باشد** — حتی اگر بقیهٔ موتور رزرو آماده نباشد. اسرا در بازهٔ 03:00–03:45 به آن نیاز دارد و اگر نباشد، فیلتر تاریخ کل کاتالوگ می‌خوابد. نسخهٔ اول می‌تواند ساده و بدون پیشنهاد باشد.

### ۱۸.۳ کوئری‌های مرجع برای ثنا

```sql
-- بازه‌های مشغول یک وسیله
SELECT start_at, end_at
  FROM reservations
 WHERE item_id = :item_id
   AND status IN ('pending','approved','active')
   AND tstzrange(start_at, end_at, '[)') && tstzrange(:from, :to, '[)')
 ORDER BY start_at
 LIMIT 100;

-- شمارنده‌های داشبورد
SELECT
  count(*) FILTER (WHERE r.status IN ('approved','active')) AS active_count,
  count(*) FILTER (WHERE r.status = 'pending')              AS pending_count
  FROM reservations r
  JOIN items i ON i.id = r.item_id
 WHERE i.owner_id = :me;
```

### ۱۸.۴ `format.js` (شقایق) — تاریخ و پول

```js
export const toUtcIso = (localValue) => new Date(localValue).toISOString();

export const formatMoney = (n) =>
  new Intl.NumberFormat("fa-IR").format(n) + " تومان";

export const formatDateTime = (iso) =>
  new Intl.DateTimeFormat("fa-IR", {
    dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Tehran",
  }).format(new Date(iso));

export const formatDate = (iso) =>
  new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeZone: "Asia/Tehran" })
    .format(new Date(iso));
```

**قانون:** ورودی `<input type="datetime-local">` همیشه با `toUtcIso()` به API می‌رود. نمایش همیشه با `formatDateTime()`.

### ۱۸.۵ برگهٔ تقلب `curl` (برای تست سریع بدون UI)

```bash
BASE=http://localhost:8000/api/v1

# ثبت‌نام و گرفتن توکن
TOKEN=$(curl -s -X POST $BASE/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"test@demo.ir","password":"Demo1234!","full_name":"تست"}' | jq -r .data.access_token)

# کاتالوگ
curl -s "$BASE/items?q=دریل&category=tools&page=1&limit=5" | jq

# ثبت رزرو
curl -s -X POST $BASE/reservations -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"item_id":1,"start_at":"2026-12-01T10:00:00Z","end_at":"2026-12-01T14:00:00Z"}' | jq

# تأیید (با توکن صاحب وسیله)
curl -s -X POST $BASE/reservations/1/approve -H "Authorization: Bearer $OWNER_TOKEN" | jq
```

### ۱۸.۶ لاگ تصمیم‌ها (هر تصمیم جدید اینجا ثبت می‌شود)

| تاریخ/ساعت | تصمیم | تصمیم‌گیرنده | تأییدکننده |
|---|---|---|---|
| T+00:00 | استک FastAPI + PostgreSQL + Vanilla JS | ثنا | همه |
| T+00:00 | SQLAlchemy sync (نه async) | ثنا | همه |
| T+00:00 | حذف Redis/Celery برای MVP | ثنا | همه |
| T+00:00 | AI با TF-IDF محلی (نه LLM ابری) | شقایق | ثنا |
| T+00:00 | همه‌ی تاریخ‌ها UTC و ISO-8601 | همه | — |
| T+00:00 | نام‌ها `snake_case` در همه لایه‌ها | همه | — |

### ۱۸.۷ واژه‌نامه

| اصطلاح | معنی در این پروژه |
|---|---|
| **وسیله (item)** | شیئی که برای امانت ثبت می‌شود |
| **صاحب وسیله (lender)** | `items.owner_id` — تأیید/رد/تحویل می‌کند |
| **متقاضی (borrower)** | `reservations.borrower_id` — درخواست می‌دهد |
| **رزرو (reservation)** | یک بازهٔ زمانی روی یک وسیله با یک وضعیت |
| **بازه (slot)** | `[start_at, end_at)` — نیمه‌باز |
| **هم‌پوشانی (overlap)** | اشتراک غیرخالی دو بازه؛ ممنوع برای رزروهای فعال |
| **گذار (transition)** | تغییر وضعیت مجاز طبق جدول ۶.۱ |
| **انقضای تنبل (lazy expire)** | منقضی کردن `pending`های قدیمی در لحظهٔ خواندن، بدون cron |
| **قید exclusion** | محدودیت پستگرس که هم‌پوشانی را در سطح دیتابیس رد می‌کند |
| **`23P01`** | کد خطای پستگرس برای نقض exclusion |
| **پاکت (envelope)** | ساختار یکسان `data` / `error` در همهٔ پاسخ‌ها |

### ۱۸.۸ امضا (هر نفر پس از خواندن کامل، ✅ بزند)

| نام | نقش | تعهد |
|---|---|---|
| اسرا | Backend A | بخش ۱۴.۱ |
| ثنا | Backend B + Tech Lead | بخش ۱۴.۲ |
| شقایق | Frontend + AI | بخش ۱۴.۳ |

---

**پایان سند — نسخهٔ ۱.۰ — قفل‌شده در T+00:00**

> اگر چیزی در این سند مبهم است، **قبل از T+00:30** بپرس. بعد از آن، ابهام را با «ساده‌ترین گزینهٔ سازگار با این سند» حل کن و در بخش ۱۸.۶ ثبت کن.
