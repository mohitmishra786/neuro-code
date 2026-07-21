#!/usr/bin/env bash
# NeuroCode first-run: start stack (or Neo4j), parse demo package, print URLs.
# Usage: ./scripts/first_run.sh
# Requires: Docker (for Neo4j/full stack) and Python 3.11+ with backend deps for parse.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DEMO_PATH="$ROOT/examples/demo_pkg"
COMPOSE_FILE="$ROOT/docker/docker-compose.yml"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-neurocode_password}"

log() { printf '==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

need_cmd docker
need_cmd python3

if ! docker compose version >/dev/null 2>&1 && ! docker-compose version >/dev/null 2>&1; then
  die "Docker Compose is required (docker compose or docker-compose)"
fi

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" "$@"
  else
    docker-compose -f "$COMPOSE_FILE" "$@"
  fi
}

log "Starting NeuroCode services (Neo4j, backend, frontend)…"
compose up -d

log "Waiting for backend health at ${BACKEND_URL}/health …"
attempts=0
until curl -sf "${BACKEND_URL}/health" >/dev/null 2>&1; do
  attempts=$((attempts + 1))
  if [[ "$attempts" -ge 60 ]]; then
    die "Backend did not become healthy within 60s. Check: docker compose -f docker/docker-compose.yml logs"
  fi
  sleep 2
done
log "Backend is healthy."

# Prefer host-side parse so Neo4j is reachable on localhost:7687
if [[ ! -d "$ROOT/backend" ]]; then
  die "backend/ directory missing"
fi

log "Installing backend dependencies if needed…"
if [[ ! -d "$ROOT/venv" ]]; then
  python3 -m venv "$ROOT/venv"
  # shellcheck disable=SC1091
  source "$ROOT/venv/bin/activate"
  pip install -q -r "$ROOT/backend/requirements.txt"
else
  # shellcheck disable=SC1091
  source "$ROOT/venv/bin/activate"
fi

export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD

log "Parsing demo package: $DEMO_PATH"
python "$ROOT/scripts/parse_codebase.py" "$DEMO_PATH" --clear

cat <<EOF

NeuroCode is ready.

  Frontend:  ${FRONTEND_URL}
  API:       ${BACKEND_URL}
  API docs:  ${BACKEND_URL}/docs  (development)
  Neo4j:     http://localhost:7474  (user: neo4j / pass: ${NEO4J_PASSWORD})

Open ${FRONTEND_URL} and double-click nodes to expand the hierarchy.

Stop services:
  docker compose -f docker/docker-compose.yml down

EOF
