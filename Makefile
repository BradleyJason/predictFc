.PHONY: install dev test train lint db-migrate help

help:
	@echo "PredictFC — Commandes disponibles"
	@echo "──────────────────────────────────"
	@echo "make install      → Installer toutes les dépendances"
	@echo "make dev          → Lancer l'environnement local complet"
	@echo "make test         → Tests + lint"
	@echo "make train        → Pipeline DVC complet"
	@echo "make lint         → Ruff uniquement"
	@echo "make db-migrate   → Appliquer les migrations Alembic"

install:
	cd backend && poetry install
	cd ml && poetry install
	cd frontend && npm install

dev:
	docker-compose up --build

test:
	cd backend && poetry run pytest --cov=app --cov-report=term-missing
	cd backend && poetry run ruff check .

train:
	cd ml && poetry run dvc repro

lint:
	cd backend && poetry run ruff check .
	cd ml && poetry run ruff check .

db-migrate:
	cd backend && poetry run alembic upgrade head

db-rollback:
	cd backend && poetry run alembic downgrade -1
