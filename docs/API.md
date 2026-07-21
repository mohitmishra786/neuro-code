# NeuroCode API Documentation

## Base URL

```text
http://localhost:8000
```

## Authentication

**Development / local-only:** no general authentication required.

- Set `API_KEY` to require a Bearer token on destructive operations (`DELETE /graph/clear`).
- `POST /graph/parse` is restricted to directories listed in `API_ALLOWED_PARSE_PATHS`.
  - When unset, the backend **defaults to the process current working directory** (`os.getcwd()` via settings).
  - Prefer setting an explicit allowlist in any shared/deployed environment.
- Rate limiting keys the **TCP peer address** by default. Set `API_TRUSTED_PROXIES` (IPs/CIDRs) only when behind a known reverse proxy before trusting `X-Forwarded-For`.
- **Do not** expose this API on the public internet without additional auth and network controls.

---

## Health Check

### GET /health
Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "neo4j": "connected"
}
```

---

## Graph Operations

### GET /graph/root
Get all root-level modules.

**Response:**
```json
{
  "nodes": [
    {
      "id": "uuid",
      "name": "module_name",
      "type": "module",
      "qualified_name": "package.module_name",
      "child_count": 5
    }
  ],
  "total": 10
}
```

### GET /graph/node/{node_id}
Get a single node by ID.

**Parameters:**
- `node_id` (path): Node UUID

**Response:**
```json
{
  "id": "uuid",
  "name": "ClassName",
  "type": "class",
  "qualified_name": "module.ClassName",
  "line_number": 42,
  "docstring": "Class description",
  "child_count": 3
}
```

### GET /graph/node/{node_id}/children
Get immediate children of a node.

**Parameters:**
- `node_id` (path): Parent node UUID
- `limit` (query, optional): Max results (default: 1000)

**Response:**
```json
{
  "parent_id": "uuid",
  "children": [...],
  "total": 5
}
```

### GET /graph/node/{node_id}/ancestors
Get ancestor path for breadcrumbs.

**Response:**
```json
{
  "node_id": "uuid",
  "ancestors": [
    {"id": "...", "name": "root_module", "type": "module"},
    {"id": "...", "name": "ParentClass", "type": "class"}
  ]
}
```

### GET /graph/node/{node_id}/references
Get nodes that reference or are referenced by this node.

**Response:**
```json
{
  "node_id": "uuid",
  "references": [
    {
      "id": "...",
      "name": "other_function",
      "type": "function",
      "relationship_type": "CALLS",
      "direction": "outgoing"
    }
  ],
  "total": 3
}
```

### POST /graph/parse
Parse a codebase and populate the graph.

**Request Body:**
```json
{
  "path": "/path/to/python/project",
  "recursive": true
}
```

**Response:**
```json
{
  "status": "completed",
  "modules_parsed": 50,
  "relationships_created": 200,
  "errors": []
}
```

### POST /graph/update
Update graph for changed files.

**Request Body:**
```json
{
  "paths": ["/path/to/changed/file.py"]
}
```

### DELETE /graph/clear
Clear all data from the graph.

---

## Search

### GET /search
Full-text search across nodes.

**Parameters:**
- `q` (query, required): Search query
- `limit` (query, optional): Max results (default: 50)
- `type_filter` (query, optional): Filter by type

**Response:**
```json
{
  "query": "search_term",
  "results": [
    {
      "id": "uuid",
      "name": "matching_name",
      "type": "function",
      "score": 0.95
    }
  ],
  "total": 5
}
```

### GET /search/suggest
Get autocomplete suggestions.

**Parameters:**
- `q` (query, required): Partial query
- `limit` (query, optional): Max suggestions (default: 10)

---

## WebSocket

### WS /ws
Real-time updates connection.

**Client Messages:**
```json
{"type": "heartbeat"}
```

**Server Messages:**
```json
{"type": "file_changed", "path": "/path/to/file.py", "change_type": "modified"}
{"type": "graph_updated", "added_count": 1, "modified_count": 0, "removed_count": 0}
```
