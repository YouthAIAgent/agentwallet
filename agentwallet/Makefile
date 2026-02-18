# AgentWallet Protocol — Developer shortcuts
# Run `make help` to see all commands

.PHONY: help setup start stop restart logs test lint shell clean

# Default target
help:
	@echo ""
	@echo "AgentWallet Protocol — Make commands"
	@echo "──────────────────────────────────────"
	@echo "  make setup    First-time setup (clone → run → ready)"
	@echo "  make start    Start API + Postgres + Redis"
	@echo "  make stop     Stop all containers"
	@echo "  make restart  Restart the API container"
	@echo "  make logs     Tail API logs"
	@echo "  make test     Run all 110 tests"
	@echo "  make lint     Ruff linter check"
	@echo "  make shell    Open bash inside API container"
	@echo "  make clean    Stop containers and remove volumes (⚠ deletes data)"
	@echo ""

# First-time setup
setup:
	@bash setup.sh

# Start core services
start:
	docker compose up -d postgres redis api
	@echo "API running at http://localhost:8000"

# Start everything including dashboard
start-all:
	docker compose up -d
	@echo "API: http://localhost:8000  |  Dashboard: http://localhost:5173"

# Stop all containers
stop:
	docker compose down

# Restart only the API (useful after code changes)
restart:
	docker compose restart api

# Tail API logs
logs:
	docker compose logs -f api

# Run all tests (SQLite, no DB needed)
test:
	@pip install -e ".[dev]" -q
	pytest packages/api/tests -v --tb=short

# Lint with ruff
lint:
	@command -v ruff >/dev/null 2>&1 || pip install ruff -q
	ruff check packages/api/agentwallet/

# Open bash in running API container
shell:
	docker compose exec api bash

# Full reset — removes volumes (all DB data lost)
clean:
	@echo "This will delete all local data (Postgres volumes). Press Ctrl+C to cancel."
	@sleep 3
	docker compose down -v
	@echo "Done. Run 'make setup' to start fresh."
