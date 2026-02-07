# AGENTS.md

This file contains project conventions and commands for agentic coding assistants.

## Build, Lint, and Test Commands

### Backend (Python 3.11+)
```bash
cd backend

# Run tests
pytest -v                              # All tests
pytest tests/test_parser.py -v          # Single file
pytest tests/test_parser.py::test_name -v  # Single test
pytest -k "test_name_pattern" -v        # Tests matching pattern

# Lint and format
ruff check .                           # Lint check
ruff check . --fix                     # Auto-fix linting
mypy .                                 # Type check

# Run server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (TypeScript + React)
```bash
cd frontend

# Run tests
npm run test                           # All tests
npm run test -- TreeGraph.test.ts -t "test name"  # Single test

# Build and lint
npm run build                          # Production build
npm run type-check                     # TypeScript check
npm run lint                           # ESLint check
npm run lint:fix                       # Auto-fix linting

# Dev server
npm run dev                            # Start dev server on port 3000
```

## Code Style Guidelines

### Python (Backend)

**Imports**: Ruff/isort configured. Standard library first, third-party, then local modules.
```python
from pathlib import Path
from typing import Any
import structlog

from parser.models import ModuleInfo
from utils.logger import LoggerMixin
```

**Type Hints**: Use Python 3.10+ union syntax (|). All functions must have type hints.
```python
def parse_file(self, file_path: Path) -> ModuleInfo:
    result: str | None = None
    items: list[str] = []
```

**Classes**: Use `@dataclass(slots=True)` for data models. Use LoggerMixin for logging.
```python
from dataclasses import dataclass, field

@dataclass(slots=True)
class ClassInfo:
    name: str
    items: list[str] = field(default_factory=list)

class MyClass(LoggerMixin):
    def method(self) -> None:
        self.log.info("message", key="value")
```

**Naming**:
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_CASE`
- Private: `_leading_underscore`
- Async functions: prefixed with `async def`

**Error Handling**: Use structured logging for errors. Catch specific exceptions.
```python
try:
    await self._driver.verify_connectivity()
except Exception as e:
    self.log.error("operation_failed", error=str(e))
    raise
```

**Logging**: Use `self.log` (from LoggerMixin) with structured keys.
```python
self.log.info("parsed_file", path=str(file_path), count=len(items))
self.log.error("failed_operation", error=str(e), context="value")
```

### TypeScript (Frontend)

**Imports**: Use `@` alias for src/ imports. React hooks first.
```typescript
import { useEffect, useCallback } from 'react';
import { useTreeStore } from '@/stores/treeStore';
import { CircleNode } from '@/components/nodes/CircleNode';
```

**Components**: Functional components with hooks. Props interface inline.
```typescript
function TreeGraph() {
    const nodes = useTreeStore((state) => state.nodes);

    return <div className="tree-graph">{/* content */}</div>;
}
```

**State Management**: Use Zustand stores with selector pattern.
```typescript
const nodes = useTreeStore((state) => state.nodes);
const selectNode = useTreeStore((state) => state.selectNode);
```

**Callbacks**: Use `useCallback` for event handlers passed as props.
```typescript
const handleClick = useCallback((event: MouseEvent) => {
    selectNode(node.id);
}, [selectNode]);
```

**Naming**:
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Interfaces/Types: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Booleans: `is`/`has` prefix (`isLoading`, `hasChildren`)

**Error Handling**: Use error state in stores. Display error banners.
```typescript
const error = useTreeStore((state) => state.error);
if (error) return <div className="error">{error}</div>;
```

## Project Structure

```
neuro-code/
├── backend/                 # Python 3.11+ FastAPI + Neo4j
│   ├── parser/              # Tree-sitter parsing
│   ├── graph_db/            # Neo4j client
│   ├── api/                 # FastAPI routes
│   └── tests/               # pytest tests
├── frontend/                # React 18 + TypeScript
│   └── src/
│       ├── components/      # React components
│       ├── stores/          # Zustand stores
│       └── types/           # TypeScript types
└── scripts/                 # CLI utilities
```

## Key Patterns

**Hierarchical IDs**: Backend uses `file_path::class::method` format for node IDs.

**Async/await**: Backend is fully async. Use `async def` and `await` for all I/O.

**Dataclasses**: Use `@dataclass(slots=True)` for all data models.

**Logging**: Use structured logging with key-value pairs, not formatted strings.

**Type Safety**: Frontend uses strict TypeScript. Backend uses mypy with strict mode.
