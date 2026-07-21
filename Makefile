.PHONY: demo up down parse-demo health test-backend test-frontend test lint check security type-check install-hooks

# Fastest path to a graph: start stack + parse examples/demo_pkg
demo:
	@chmod +x scripts/first_run.sh
	./scripts/first_run.sh

up:
	docker compose -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down

parse-demo:
	python scripts/parse_codebase.py examples/demo_pkg --clear

health:
	@curl -sf http://localhost:8000/health && echo "" || (echo "Backend unhealthy" && exit 1)

test-backend:
	cd backend && pytest tests/ -v --tb=short

test-frontend:
	cd frontend && npm run test -- --run

test: test-backend test-frontend

# Match CI ruff scope (not full tree — legacy debt remains)
lint:
	cd backend && python -m ruff check api/ utils/ merkle/ graph_db/ parser/tree_sitter_parser.py tests/
	cd frontend && npm run lint

type-check:
	cd frontend && npx tsc --noEmit -p tsconfig.app.json

# Full local gate (mirrors CI primary jobs — see scripts/check.sh)
check:
	@chmod +x scripts/check.sh
	./scripts/check.sh all

security:
	@chmod +x scripts/check.sh
	./scripts/check.sh security

# Install git hooks that mirror CI (requires: pip install pre-commit)
install-hooks:
	pip install pre-commit
	pre-commit install
	@echo "Hooks installed. Run: pre-commit run --all-files"