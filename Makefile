.PHONY: demo up down parse-demo health test-backend test-frontend test lint

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

lint:
	cd backend && ruff check .
	cd frontend && npm run lint && npm run type-check
