.PHONY: up logs down migrate seed test reset fmt

up:
	docker compose up --build -d

logs:
	docker compose logs -f api

down:
	docker compose down

migrate:
	alembic upgrade head

seed:
	python -m app.seed

test:
	pytest -q

reset:
	docker compose down -v
	docker compose up --build -d

fmt:
	ruff format . && ruff check --fix .
