.DEFAULT_GOAL := help
.PHONY: help install dev up down logs migrate revision lint format type test cover seed shell

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:  ## Create venv and install all deps (incl. dev)
	python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

dev:  ## Run API locally with autoreload (needs running postgres+redis)
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

up:  ## Start the full stack with docker compose
	docker compose up --build

down:  ## Stop the stack and remove volumes
	docker compose down -v

logs:  ## Tail API logs
	docker compose logs -f api

migrate:  ## Apply DB migrations to head
	alembic upgrade head

revision:  ## Autogenerate a migration: make revision m="add foo"
	alembic revision --autogenerate -m "$(m)"

lint:  ## Lint with ruff
	ruff check app tests

format:  ## Auto-format with ruff
	ruff format app tests && ruff check --fix app tests

type:  ## Static type-check with mypy
	mypy app

test:  ## Run the test suite
	pytest

cover:  ## Run tests with HTML coverage report
	pytest --cov-report=html && echo "open htmlcov/index.html"

seed:  ## Seed demo data (admin user + sample products)
	python -m app.scripts.seed

shell:  ## Open a psql shell on the compose postgres
	docker compose exec postgres psql -U shop -d shop
