#!/usr/bin/env bash
# Local quality gate — mirrors primary CI workflows (ci.yml + lint.yml + security.yml).
# Usage: ./scripts/check.sh [backend|frontend|security|lint|all]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
TARGET="${1:-all}"

# Same paths as .github/workflows/ci.yml and lint.yml
RUFF_PATHS=(
  api/
  utils/
  merkle/
  graph_db/
  parser/tree_sitter_parser.py
  tests/
)

log() { printf '\n==> %s\n' "$*"; }

activate_python() {
  # shellcheck disable=SC1091
  if [[ -f "$ROOT/.venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT/.venv/bin/activate"
  elif [[ -f "$ROOT/backend/venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT/backend/venv/bin/activate"
  elif [[ -f "$ROOT/venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT/venv/bin/activate"
  fi
}

run_backend() {
  log "Backend: ruff (CI scope) + pytest"
  activate_python
  cd "$ROOT/backend"
  # Prefer `python -m ruff` so the venv tool is used, not a stale global binary
  if python -m ruff --version >/dev/null 2>&1; then
    python -m ruff check "${RUFF_PATHS[@]}"
  else
    ruff check "${RUFF_PATHS[@]}"
  fi
  pytest tests/ -q --tb=short
  cd "$ROOT"
}

run_backend_mypy() {
  log "Backend: mypy (advisory — legacy type debt may fail)"
  activate_python
  cd "$ROOT/backend"
  if python -m mypy --version >/dev/null 2>&1; then
    python -m mypy \
      api/ \
      utils/ \
      merkle/ \
      graph_db/ \
      parser/tree_sitter_parser.py \
      --config-file pyproject.toml \
      || true
  else
    echo "mypy not installed; skip (pip install -r requirements.txt)"
  fi
  cd "$ROOT"
}

run_frontend() {
  log "Frontend: eslint + tsc (app) + vitest"
  cd "$ROOT/frontend"
  npm run lint
  npx tsc --noEmit -p tsconfig.app.json
  npm run test -- --run
  cd "$ROOT"
}

run_security() {
  log "Security: pip-audit + npm audit (high)"
  activate_python
  python -m pip install -q pip-audit 2>/dev/null || true
  if command -v pip-audit >/dev/null 2>&1 || python -m pip_audit --help >/dev/null 2>&1; then
    pip-audit -r backend/requirements.txt || true
  else
    echo "pip-audit unavailable; skip"
  fi
  cd "$ROOT/frontend"
  npm audit --omit=dev --audit-level=high || true
  cd "$ROOT"
}

run_lint_extras() {
  log "Lint extras: markdownlint (advisory)"
  if command -v markdownlint >/dev/null 2>&1; then
    markdownlint \
      --config .markdownlint.json \
      "README.md" \
      "docs/**/*.md" \
      "AGENTS.md" \
      "CONTRIBUTING.md" \
      "SECURITY.md" \
      "CHANGELOG.md" \
      || true
  else
    echo "markdownlint-cli not installed; skip (npm i -g markdownlint-cli)"
  fi
}

case "$TARGET" in
  backend) run_backend; run_backend_mypy ;;
  frontend) run_frontend ;;
  security) run_security ;;
  lint) run_backend; run_frontend; run_lint_extras ;;
  all)
    run_backend
    run_backend_mypy
    run_frontend
    run_security
    run_lint_extras
    log "All local checks finished (mirrors CI primary jobs)"
    ;;
  *)
    echo "Usage: $0 [backend|frontend|security|lint|all]" >&2
    exit 2
    ;;
esac
