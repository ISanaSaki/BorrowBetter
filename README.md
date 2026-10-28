# BorrowBetter

**A community tool-lending library** — FastAPI + PostgreSQL.

People list the things they rarely use (a drill, a tent, a projector…), neighbours
request them for a specific time window, the owner approves or rejects, and the
hand-over and return are recorded.

> The team's single source of truth is [`docs/TEAM_SPEC.md`](docs/TEAM_SPEC.md) (Persian).
> Anything that is not decided there, is not decided.

---

## Key strength: concurrency enforced by the database

```sql
ALTER TABLE reservations
  ADD CONSTRAINT no_overlap
  EXCLUDE USING gist (
    item_id WITH =,
    tstzrange(start_at, end_at, '[)') WITH &&
  )
  WHERE (status IN ('pending','approved','active'));
```

Three layers:

| Layer | Tool | Guarantee |
|---|---|---|
| 1 | `SELECT … FOR UPDATE` on the item row | serialises all booking attempts for one item |
| 2 | `NOT EXISTS` overlap check | fast, readable 409 + alternative slots |
| 3 | `EXCLUDE no_overlap` | the final guarantee, even if the code has a bug (`23P01`) |

50 simultaneous requests: `tests/test_concurrency.py` — exactly one `201`, the rest
`409 SLOT_CONFLICT` with at least one genuinely free suggestion.

---

## Running

### Docker (primary)

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:8000/health
```

`alembic upgrade head` and `python -m app.seed` run automatically on startup.

### No Docker — `run.py`

```bash
python run.py --install     # first time only: create .venv + install
python run.py               # migrate + seed + uvicorn --reload
```

- Creates `.env` from `.env.example` if it is missing.
- Rewrites a docker-internal `db` host in `DATABASE_URL` to
  `127.0.0.1:POSTGRES_HOST_PORT` (default `5433`), so the container database can be
  reused from the host without editing `.env`.
- `python run.py --check` only verifies the database and migrations.
- Flags: `--port 8010`, `--no-reload`, `--no-migrate`, `--no-seed`, `--host 0.0.0.0`.
- Busy port / unreachable database produce a short actionable message instead of a traceback.

### Manual (without `run.py`)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt -i https://mirror-pypi.runflare.com/simple

# in .env:  DATABASE_URL=postgresql+psycopg://borrowbetter:borrowbetter@127.0.0.1:5433/borrowbetter
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: <http://localhost:8000/docs>
- OpenAPI schema: <http://localhost:8000/openapi.json>
- Health: `GET /health` → `{"status":"ok","db":"up",…}`

### Demo users (password for all: `Demo1234!`)

| Email | Name | Role |
|---|---|---|
| `sana@demo.ir` | Sana | owns several items |
| `asra@demo.ir` | Asra | borrower |
| `shaghayegh@demo.ir` | Shaghayegh | owns one item |
| `demo@demo.ir` | Demo user | for test sign-ups |

---

## Tests

```bash
pytest -q                      # 34 tests, ~12s
pytest tests/test_concurrency.py -q -s
```

Requires a migrated database (`alembic upgrade head`) and a valid `DATABASE_URL`.

| File | Owner | Covers |
|---|---|---|
| `test_auth.py` | Asra | sign-up / login / 401 |
| `test_items.py` | Asra | CRUD, filters, permissions |
| `test_transitions.py` | Sana | every allowed and forbidden transition |
| `test_concurrency.py` | Sana | 50 simultaneous requests, DB constraint, expiry |

---

## Structure and ownership

```
app/
├── main.py, core/, db/            <- Asra
├── models/user.py, item.py        <- Asra
├── models/reservation.py          <- Sana
├── routers/auth|users|items.py    <- Asra
├── routers/reservations.py        <- Sana   (also /items/{id}/availability)
├── services/booking|availability|lifecycle|permissions.py  <- Sana
├── services/auth|items|search.py  <- Asra
├── services/ai_search.py          <- Shaghayegh
└── seed.py                        <- Asra

alembic/versions/0001_init.py            <- Asra
alembic/versions/0002_reservations.py    <- Sana
frontend/                                <- Shaghayegh
```

**The single integration point:** `app/services/availability.py`

```python
free_item_ids(db, item_ids, start, end) -> set[int]
assert_bookable(db, item_id, start, end) -> None
has_active_reservations(db, item_id) -> bool
```

Nobody except Sana writes a query against `reservations`.

---

## Response contract

```jsonc
// success
{"data": {...}}
{"data": [...], "meta": {"page":1,"limit":20,"total":3,"total_pages":1,"has_next":false}}

// error
{"error": {"code": "SLOT_CONFLICT", "message": "<user-facing text>", "details": {...}}}
```

All timestamps are UTC and ISO-8601 with `Z`. All keys are `snake_case` — the
frontend performs no conversion. `error.message` is user-facing and localised
(Persian, per spec §7.0); everything else in the API surface is English.

## Quick commands

| Command | Action |
|---|---|
| `make up` / `make logs` / `make down` | Docker |
| `make migrate` | `alembic upgrade head` |
| `make seed` | demo data (idempotent) |
| `make test` | `pytest -q` |
| `make reset` | wipe + rebuild the database |

## Running without Docker (Windows / VS Code)

Docker is the official path, but the API also runs from a plain terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python run.py            # or: .\run.cmd
```

VS Code is preconfigured: open the repository root, select `.venv\Scripts\python.exe`
as the interpreter, then press `F5` and pick **API - run.py (local)** or
**Tests (pytest)**.

Full walkthrough, including PostgreSQL setup without Docker and a troubleshooting
table: [`docs/LOCAL_DEV.md`](docs/LOCAL_DEV.md).
