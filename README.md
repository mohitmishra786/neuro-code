# NeuroCode

**Interactive Hierarchical Code Visualization System**

Transform Python codebases into explorable, hierarchical knowledge graphs with instant, smooth navigation.

## Requirements

- **Python 3.11+** (required)
- Node.js 18+ (for frontend)
- Neo4j 5.x (graph database)
- Docker & Docker Compose (optional, for containerized deployment)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-org/neurocode.git
cd neurocode
```

### 2. Backend Setup (Python 3.11+)

```bash
# Create virtual environment with Python 3.11
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate   # On Windows

# Verify Python version
python --version  # Should show Python 3.11.x

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Start Neo4j Database

```bash
# Using Docker
docker-compose -f docker/docker-compose.yml up neo4j -d

# Or install Neo4j locally and start it
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Start Backend Server

```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Parse a Codebase

```bash
# Parse a Python project
python scripts/parse_codebase.py /path/to/your/python/project
```

### 7. Open Visualization

Navigate to `http://localhost:3000` in your browser.

## Project Structure

```
NeuroCode/
├── backend/                 # Python 3.11+ backend
│   ├── parser/              # Tree-sitter + AST parsing
│   ├── graph_db/            # Neo4j integration
│   ├── merkle/              # Change detection system
│   ├── watcher/             # File system watcher
│   ├── api/                 # FastAPI REST + WebSocket
│   ├── utils/               # Shared utilities
│   └── tests/               # pytest test suite
├── frontend/                # React 18 + TypeScript
│   └── src/
│       ├── components/      # React components
│       ├── hooks/           # Custom hooks
│       ├── stores/          # Zustand state
│       ├── services/        # API client
│       └── utils/           # Utilities
├── docker/                  # Docker configuration
├── scripts/                 # CLI tools
└── docs/                    # Documentation
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Initial page load | < 2 seconds |
| Node expansion | < 50ms |
| Rendering FPS | 60 FPS |
| Parse 1000 files | < 30 seconds |
| Incremental update | < 1 second |
| Maximum codebase size | 100,000 files |

## Technology Stack

### Backend (Python 3.11+)
- **Parser**: Tree-sitter + Python AST
- **Database**: Neo4j 5.x (graph database)
- **API**: FastAPI with async support
- **File Watching**: watchdog

### Frontend
- **Framework**: React 18 + TypeScript
- **Rendering**: Sigma.js v3 (WebGL)
- **State**: Zustand
- **Build**: Vite

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm run test
```

### Code Quality

```bash
# Backend linting
cd backend
ruff check .
mypy .

# Frontend linting
cd frontend
npm run lint
```

## Documentation

- [API Reference](docs/API.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## License

MIT License - see [LICENSE](LICENSE) for details.
