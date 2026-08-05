.PHONY: install up down test lint typecheck check seed benchmark

install:
	uv sync

up:
	docker compose up --build -d

down:
	docker compose down

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy .

check: test lint typecheck

seed:
	uv run python scripts/produce_events.py

benchmark:
	./scripts/benchmark.sh
