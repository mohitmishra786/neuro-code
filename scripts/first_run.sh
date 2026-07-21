#!/usr/bin/env bash
# NeuroCode first-run: start Neo4j, backend, parse demo, print URLs.
# Prefers Docker for Neo4j; runs backend + parse on host for reliability.
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
need_cmd curl

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

log "Starting Neo4j (Docker)…"
compose up neo4j -d

log "Waiting for Neo4j Bolt on localhost:7687…"
attempts=0
until docker exec neurocode-neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" >/dev/null 2>&1; do
  attempts=$((attempts + 1))
  if [[ "$attempts" -ge 40 ]]; then
    die "Neo4j did not become ready. Logs: docker logs neurocode-neo4j"
  fi
  sleep 3
done
log "Neo4j is ready."

if [[ ! -d "$ROOT/venv" && ! -d "$ROOT/.venv" ]]; then
  log "Creating Python venv…"
  python3 -m venv "$ROOT/venv"
fi
# shellcheck disable=SC1091
if [[ -f "$ROOT/venv/bin/activate" ]]; then
  source "$ROOT/venv/bin/activate"
elif [[ -f "$ROOT/.venv/bin/activate" ]]; then
  source "$ROOT/.venv/bin/activate"
fi

log "Installing backend dependencies…"
pip install -q -r "$ROOT/backend/requirements.txt"

export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD
export API_ALLOWED_PARSE_PATHS="${API_ALLOWED_PARSE_PATHS:-$ROOT}"

log "Parsing demo package: $DEMO_PATH"
python "$ROOT/scripts/parse_codebase.py" "$DEMO_PATH" --clear

# Start backend if not already healthy
if ! curl -sf "${BACKEND_URL}/health" >/dev/null 2>&1; then
  log "Starting backend on :8000…"
  (
    cd "$ROOT/backend"
    nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 >"$ROOT/.neurocode-backend.log" 2>&1 &
    echo $! >"$ROOT/.neurocode-backend.pid"
  )
  attempts=0
  until curl -sf "${BACKEND_URL}/health" >/dev/null 2>&1; do
    attempts=$((attempts + 1))
    if [[ "$attempts" -ge 30 ]]; then
      die "Backend failed to start. See .neurocode-backend.log"
    fi
    sleep 1
  done
fi
log "Backend is healthy."

# Start frontend if needed
if ! curl -sf "${FRONTEND_URL}" >/dev/null 2>&1; then
  if command -v npm >/dev/null 2>&1; then
    log "Starting frontend on :3000…"
    (
      cd "$ROOT/frontend"
      if [[ ! -d node_modules ]]; then
        npm install --silent
      fi
      nohup npm run dev -- --host 0.0.0.0 --port 3000 >"$ROOT/.neurocode-frontend.log" 2>&1 &
      echo $! >"$ROOT/.neurocode-frontend.pid"
    )
    attempts=0
    until curl -sf "${FRONTEND_URL}" >/dev/null 2>&1; do
      attempts=$((attempts + 1))
      if [[ "$attempts" -ge 45 ]]; then
        log "Frontend not responding yet — start manually: cd frontend && npm run dev"
        break
      fi
      sleep 2
    done
  else
    log "npm not found; start frontend manually: cd frontend && npm run dev"
  fi
fi

cat <<EOF

NeuroCode is ready.

  Frontend:  ${FRONTEND_URL}
  API:       ${BACKEND_URL}
  API docs:  ${BACKEND_URL}/docs  (development)
  Neo4j:     http://localhost:7474  (user: neo4j / pass: ${NEO4J_PASSWORD})

Open ${FRONTEND_URL} and double-click nodes to expand the hierarchy.

Stop Neo4j:
  docker compose -f docker/docker-compose.yml stop neo4j

EOF
