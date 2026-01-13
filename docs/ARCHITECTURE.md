# NeuroCode Architecture

## System Overview

NeuroCode transforms Python codebases into interactive, explorable knowledge graphs with real-time updates and smooth navigation.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Sigma   │  │  Zustand │  │  Search  │  │    WebSocket     │ │
│  │  Graph   │  │  Store   │  │  Panel   │  │    Handler       │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │
└───────┼─────────────┼─────────────┼─────────────────┼───────────┘
        │             │             │                 │
        └─────────────┴─────────────┴─────────────────┘
                              │
                    REST API + WebSocket
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                         Backend (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  │  ┌──────────┐  ┌──────────────┐  │
│  │  Graph   │  │  Search  │  │  │ WebSocket│  │    File      │  │
│  │  Routes  │  │  Routes  │  │  │  Handler │  │   Watcher    │  │
│  └────┬─────┘  └────┬─────┘  │  └────┬─────┘  └──────┬───────┘  │
└───────┼─────────────┼────────┼───────┼───────────────┼──────────┘
        │             │        │       │               │
        └─────────────┴────────┴───────┘               │
                      │                                │
┌─────────────────────┼────────────────────────────────┼──────────┐
│                     │      Core Services             │          │
│  ┌──────────────────┴──────────┐  ┌──────────────────┴───────┐  │
│  │         Neo4j Client        │  │      Parser + Merkle     │  │
│  │     (Graph Operations)      │  │   (Code Analysis)        │  │
│  └──────────────┬──────────────┘  └──────────────────────────┘  │
└─────────────────┼───────────────────────────────────────────────┘
                  │
         ┌────────┴────────┐
         │     Neo4j       │
         │    Database     │
         └─────────────────┘
```

---

## Data Flow

### Initial Load
1. User opens application
2. Frontend requests root nodes via `GET /graph/root`
3. Backend queries Neo4j for top-level modules
4. Frontend renders nodes with Sigma.js

### Node Expansion
1. User clicks a node
2. Frontend requests children via `GET /graph/node/{id}/children`
3. Backend queries Neo4j for CONTAINS relationships
4. Frontend adds children to graph with animation
5. ForceAtlas2 layout adjusts positions

### File Change
1. File watcher detects change
2. Debouncer accumulates changes (500ms)
3. Parser re-parses changed files
4. Merkle tree identifies modified nodes
5. Neo4j updated with delta changes
6. WebSocket broadcasts update to clients
7. Frontend refreshes affected nodes

---

## Components

### Parser Layer
- **TreeSitterParser**: Fast, incremental parsing with Tree-sitter
- **ASTAnalyzer**: Semantic analysis with Python's AST
- **RelationshipExtractor**: Builds code relationships

### Graph Engine
- **Neo4jClient**: Async client with connection pooling
- **GraphSchema**: Node/relationship definitions
- **QueryLibrary**: Optimized Cypher queries

### Merkle Tree
- **HashCalculator**: SHA-256 content hashing
- **ChangeDetector**: Identifies modified code elements

### API Layer
- **FastAPI**: Async REST + WebSocket server
- **Graph Routes**: CRUD for graph data
- **Search Routes**: Full-text search

### Frontend
- **Sigma.js**: WebGL graph rendering
- **Zustand**: State management
- **IndexedDB**: Client-side caching

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Root nodes load | < 100ms |
| Node expansion | < 50ms |
| Search results | < 200ms |
| File update | < 1s |
| Initial render | < 2s |
| Frame rate | 60 FPS |
| Max nodes visible | 10,000 |
| Max codebase size | 100,000 files |
