# Local development on Windows (no Docker Desktop required)

This guide covers running the API from a plain terminal or from VS Code.
Docker remains the official path (`docker compose up --build -d`); this is the
fallback for machines where Docker Desktop is missing or broken.

## 1. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| PostgreSQL | 16+ (server) | `psql --version` |
| Git | any recent | `git --version` |

You still need a PostgreSQL server, because the schema relies on `btree_gist`,
native ENUM types and the `EXCLUDE` constraint. Two ways to get one without the
full Compose stack:

- start only the database container: `docker compose up -d db`
- or install PostgreSQL natively and create a database: `CREATE DATABASE borrowbetter;`

## 2. Create the virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

If PowerShell blocks the activation script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

If `python -m venv` fails with an `ensurepip` error, create the environment
without pip and install through the global interpreter:

```powershell
python -m venv .venv --without-pip
python -m pip --python .venv install -r requirements-dev.txt
```

## 3. Configure `.env`

`run.py` creates `.env` from `.env.example` when it is missing and rewrites the
`db` host to `127.0.0.1:<POSTGRES_PORT>` automatically, so the Compose database
is reachable from the host without editing anything.

If you use a natively installed PostgreSQL, set the URL explicitly:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres:yourpassword@localhost:5432/borrowbetter
```

## 4. Run

```powershell
python run.py            # http://127.0.0.1:8000 (auto-reload)
.\run.cmd                # same, double-click friendly, uses .venv automatically
python run.py --port 8010
python run.py --check    # database + migrations only, no server
```

Swagger UI: <http://127.0.0.1:8000/docs> · Health: <http://127.0.0.1:8000/health>

## 5. VS Code

1. `File -> Open Folder` and pick the repository root (the folder that contains `run.py`).
2. Accept the recommended extensions (Python, Pylance, Ruff) when prompted.
3. `Ctrl+Shift+P` -> **Python: Select Interpreter** -> `.venv\Scripts\python.exe`.
4. Press `F5` and choose one of the ready profiles:
   - **API - run.py (local)**
   - **API - uvicorn (reload)**
   - **Tests (pytest)**

The test runner in the Testing sidebar also works once the interpreter is set.

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `running scripts is disabled on this system` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `Port 8000 is already in use` | `python run.py --port 8010` |
| `ModuleNotFoundError: fastapi` | the venv is not active; use `.\.venv\Scripts\python.exe -m ...` or select the interpreter in VS Code |
| `could not connect to server` on startup | PostgreSQL is not running, or `DATABASE_URL` points at the wrong host/port |
| `type "btree_gist" does not exist` | the extension is created by migration `0001`; run `alembic upgrade head` |
| `alembic: command not found` | run it through the interpreter: `python -m alembic upgrade head` |
| Windows console mangles non-ASCII output | `chcp 65001` or use Windows Terminal |

## 7. Useful commands

```powershell
pytest -q                      # full suite
pytest -q --lf                 # last failures only
ruff check . ; ruff format --check .
python -m alembic upgrade head # apply migrations
python -m app.seed             # demo data (idempotent)
```
