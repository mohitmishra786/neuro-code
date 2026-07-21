#!/usr/bin/env bash
# Local quality gate — mirrors primary CI workflows.
# Usage: ./scripts/check.sh [backend|frontend|security|all]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
TARGET="${1:-all}"

log() { printf '\n==> %s\n' "$*"; }

run_backend() {
  log "Backend: ruff + pytest"
  # shellcheck disable=SC1091
  if [[ -f .venv/bin/activate ]]; then source .venv/bin/activate
  elif [[ -f venv/bin/activate ]]; then source venv/bin/activate
  fi
  cd "$ROOT/backend"
  ruff check .
  pytest tests/ -q --tb=short
  cd "$ROOT"
}

run_frontend() {
  log "Frontend: eslint + tsc + vitest"
  cd "$ROOT/frontend"
  npm run lint
  npx tsc --noEmit -p tsconfig.app.json
  npm run test -- --run
  cd "$ROOT"
}

run_security() {
  log "Security: pip-audit + npm audit (high)"
  # shellcheck disable=SC1091
  if [[ -f .venv/bin/activate ]]; then source .venv/bin/activate
  elif [[ -f venv/bin/activate ]]; then source venv/bin/activate
  fi
  python -m pip install -q pip-audit
  pip-audit -r backend/requirements.txt || true
  cd "$ROOT/frontend"
  npm audit --omit=dev --audit-level=high || true
  cd "$ROOT"
}

case "$TARGET" in
  backend) run_backend ;;
  frontend) run_frontend ;;
  security) run_security ;;
  all)
    run_backend
    run_frontend
    run_security
    log "All local checks finished"
    ;;
  *)
    echo "Usage: $0 [backend|frontend|security|all]" >&2
    exit 2
    ;;
esac
