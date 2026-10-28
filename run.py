#!/usr/bin/env python
"""BorrowBetter launcher — run the project on your own machine, no Docker needed.

    python run.py                start on http://127.0.0.1:8000 (auto-reload)
    python run.py --port 8010    different port
    python run.py --no-reload    disable auto-reload
    python run.py --check        database + migrations check only, no server
    python run.py --install      create .venv and install requirements (mirror)

Before starting:
  1) If .env is missing it is created from .env.example.
  2) If the database URL points at the docker service host `db`, it is
     rewritten to 127.0.0.1:POSTGRES_HOST_PORT (default 5433), so the same
     container database works from the host without editing .env.
  3) Migrations and demo seed run automatically (both idempotent).
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED_MODULES = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "sqlalchemy": "SQLAlchemy",
    "psycopg": "psycopg[binary]",
    "alembic": "alembic",
    "pydantic": "pydantic",
    "pydantic_settings": "pydantic-settings",
    "jwt": "PyJWT",
    "passlib": "passlib[bcrypt]",
    "orjson": "orjson",
    "dotenv": "python-dotenv",
}

DEFAULT_PIP_INDEX = os.environ.get("PIP_INDEX_URL", "https://mirror-pypi.runflare.com/simple")
DEMO_PASSWORD = "Demo1234!"


# --------------------------------------------------------------------------- #
# console / printing
# --------------------------------------------------------------------------- #
def _setup_console() -> None:
    """UTF-8 output on Windows so emoji and non-ASCII text do not crash."""
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def say(message: str = "") -> None:
    print(message, flush=True)


def fail(message: str, hint: str = "") -> int:
    say(f"\n[FAIL] {message}")
    if hint:
        say(hint)
    return 1


# --------------------------------------------------------------------------- #
# dependencies
# --------------------------------------------------------------------------- #
def venv_python() -> Path | None:
    candidate = ROOT / (".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python")
    return candidate if candidate.exists() else None


def missing_dependencies() -> list[str]:
    missing: list[str] = []
    for module, package in REQUIRED_MODULES.items():
        try:
            __import__(module)
        except Exception:
            missing.append(package)
    return missing


def install_hint() -> str:
    return (
        "\nHow to fix:\n"
        "  python run.py --install                    # create .venv + install (recommended)\n"
        "  python -m venv .venv\n"
        "  .venv\\Scripts\\activate\n"
        f"  pip install -r requirements.txt -i {DEFAULT_PIP_INDEX}\n"
    )


def bootstrap() -> int:
    """Create .venv and install requirements through a reachable PyPI mirror."""
    say("[1/3] Installing dependencies into .venv ...")
    venv_dir = ROOT / ".venv"
    python = venv_python()
    uv = shutil.which("uv")

    if python is None:
        if uv:
            say(f"      {uv} venv {venv_dir}")
            result = subprocess.run([uv, "venv", str(venv_dir), "--python", "3.12"])
        else:
            say(f"      {sys.executable} -m venv {venv_dir}")
            result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)])
        python = venv_python()
        if result.returncode != 0 or python is None:
            return fail(
                "Could not create the virtual environment.",
                "Try manually:\n"
                "  python -m venv .venv\n"
                "  .venv\\Scripts\\python -m pip install -r requirements.txt",
            )

    requirements = str(ROOT / "requirements.txt")
    index = DEFAULT_PIP_INDEX
    if uv:
        cmd = [uv, "pip", "install", "--python", str(python), "--index-url", index, "-r", requirements]
    else:
        cmd = [str(python), "-m", "pip", "install", "--index-url", index, "-r", requirements]

    say(f"      Installing from {index} ...")
    if subprocess.run(cmd).returncode != 0:
        return fail(
            "Installing dependencies failed.",
            "Try another mirror:\n"
            "  $env:PIP_INDEX_URL='https://pypi.tuna.tsinghua.edu.cn/simple'\n"
            "  python run.py --install",
        )

    say("[2/3] Install complete.")
    say("[3/3] Starting the application ...\n")
    return subprocess.call([str(python), str(Path(__file__).resolve()), *sys.argv[1:]])


# --------------------------------------------------------------------------- #
# environment / database
# --------------------------------------------------------------------------- #
def load_env() -> None:
    env_file = ROOT / ".env"
    if not env_file.exists():
        example = ROOT / ".env.example"
        if example.exists():
            shutil.copy(example, env_file)
            say("[info] .env created from .env.example")

    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    # override=False -> real environment variables win over .env
    load_dotenv(env_file, override=False)


def resolve_database_url() -> str:
    """Translate docker-internal hosts (`db`) into something the host can reach."""
    from sqlalchemy.engine import make_url

    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        raise RuntimeError("DATABASE_URL is not set (neither in the environment nor in .env).")

    url = make_url(raw)
    if url.host in {"db", "postgres", "database", "api-db"}:
        port = int(os.environ.get("POSTGRES_HOST_PORT") or 5433)
        url = url.set(host="127.0.0.1", port=port)
        say(f"[info] Database host rewritten: {url.host}:{url.port}")

    resolved = url.render_as_string(hide_password=False)
    os.environ["DATABASE_URL"] = resolved
    return resolved


def check_database(url: str) -> tuple[bool, str]:
    import psycopg
    from sqlalchemy.engine import make_url

    dsn = make_url(url).set(drivername="postgresql").render_as_string(hide_password=False)
    try:
        with psycopg.connect(dsn, connect_timeout=4) as conn:
            conn.execute("SELECT 1")
        return True, ""
    except Exception as exc:  # noqa: BLE001 - we only need a one-line reason
        text = str(exc).strip()
        return False, text.splitlines()[0] if text else exc.__class__.__name__


def database_hint(url: str, error: str) -> str:
    from sqlalchemy.engine import make_url

    parsed = make_url(url)
    target = f"{parsed.host}:{parsed.port}/{parsed.database}"
    return (
        f"\n   target: {target}\n   error : {error}\n\n"
        "Options:\n"
        "  1) Start the docker database that .env points at:\n"
        "       docker compose up -d db\n"
        "  2) Use your local PostgreSQL instead (in .env):\n"
        "       DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@127.0.0.1:5432/borrowbetter\n"
        "  3) Create the database manually:\n"
        '       psql -U postgres -c "CREATE DATABASE borrowbetter;"\n'
    )


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"].replace("%", "%%"))
    command.upgrade(cfg, "head")


def run_seed() -> bool:
    from app.db.session import SessionLocal
    from app.seed import seed

    with SessionLocal() as db:
        return seed(db)


# --------------------------------------------------------------------------- #
# server
# --------------------------------------------------------------------------- #
def port_free(host: str, port: int) -> bool:
    probe = "127.0.0.1" if host in ("0.0.0.0", "::", "") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.4)
        return sock.connect_ex((probe, port)) != 0


def print_banner(host: str, port: int) -> None:
    from sqlalchemy.engine import make_url

    url = make_url(os.environ["DATABASE_URL"])
    shown = "127.0.0.1" if host in ("0.0.0.0", "::", "") else host
    say("")
    say("  +------------------------------------------------------------+")
    say("  |  BorrowBetter  -  local tool-lending library                |")
    say("  +------------------------------------------------------------+")
    say(f"   API        http://{shown}:{port}/api/v1")
    say(f"   Swagger    http://{shown}:{port}/docs")
    say(f"   OpenAPI    http://{shown}:{port}/openapi.json")
    say(f"   Health     http://{shown}:{port}/health")
    say(f"   Database   {url.host}:{url.port}/{url.database}")
    say("   Demo users sana@demo.ir / asra@demo.ir / shaghayegh@demo.ir")
    say(f"   Password   {DEMO_PASSWORD}")
    say("   Stop       Ctrl+C")
    say("")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run BorrowBetter locally (no Docker required).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python run.py                 # http://127.0.0.1:8000\n"
            "  python run.py --port 8010     # another port\n"
            "  python run.py --check         # verify DB + migrations only\n"
            "  python run.py --install       # bootstrap .venv\n"
        ),
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port (default: 8000)")
    parser.add_argument("--no-reload", action="store_true", help="disable auto-reload")
    parser.add_argument("--no-migrate", action="store_true", help="skip alembic upgrade")
    parser.add_argument("--no-seed", action="store_true", help="skip demo seed")
    parser.add_argument("--check", action="store_true", help="check only, do not start the server")
    parser.add_argument("--install", action="store_true", help="create .venv and install requirements")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _setup_console()
    args = parse_args(argv if argv is not None else sys.argv[1:])
    os.chdir(ROOT)

    missing = missing_dependencies()
    if missing:
        local = venv_python()
        if local is not None and Path(sys.executable).resolve() != local.resolve():
            say("[info] Running with the project virtualenv (.venv) ...\n")
            return subprocess.call([str(local), str(Path(__file__).resolve()), *sys.argv[1:]])
        if args.install:
            return bootstrap()
        return fail(f"Missing dependencies: {', '.join(missing)}", install_hint())

    load_env()
    try:
        database_url = resolve_database_url()
    except Exception as exc:  # noqa: BLE001
        return fail(
            str(exc),
            "\nExample in .env:\nDATABASE_URL=postgresql+psycopg://user:pass@127.0.0.1:5432/borrowbetter",
        )

    ok, error = check_database(database_url)
    if not ok:
        return fail("Could not connect to the database.", database_hint(database_url, error))

    if not args.no_migrate:
        say("[1/2] Applying migrations ...")
        run_migrations()
        say("      Migrations up to date.")

    if not args.no_seed:
        created = run_seed()
        say("[2/2] Demo data created." if created else "[2/2] Demo data already present.")

    if args.check:
        say("\n[OK] Everything is ready. Start with:  python run.py")
        return 0

    if not port_free(args.host, args.port):
        return fail(
            f"Port {args.port} is already in use.",
            f"  use another port:      python run.py --port {args.port + 1}\n"
            "  or stop the container: docker compose stop api",
        )

    print_banner(args.host, args.port)

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        reload_dirs=[str(ROOT / "app")] if not args.no_reload else None,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
