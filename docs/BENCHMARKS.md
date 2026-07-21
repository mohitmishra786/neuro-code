# Benchmarks & performance goals

**Last updated:** 2026-07-21  

## Design goals (not SLAs)

| Metric | Goal | Implementation intent |
|--------|------|------------------------|
| Initial page load | &lt; 2s | Load root packages only |
| Node expansion | &lt; 50ms | Single expand API + cache |
| Interactive FPS | 60 FPS | ReactFlow for visible subset |
| Parse 1000 files | &lt; 30s | Tree-sitter + multi-pass |
| Incremental update | &lt; 1s | Merkle + watcher |
| Search | &lt; 200ms | Neo4j full-text when indexed |

## How to measure

```bash
# Requires Neo4j running
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=neurocode_password
python scripts/benchmark.py /path/to/python/project
```

## Recorded results

### 2026-07-21 — examples/demo_pkg (6 modules)

| Machine | macOS aarch64 (Apple Silicon), Python 3.14 venv, Neo4j 5.26-community Docker |
|---------|-------------------------------------------------------------------------------|
| Commit  | audit/pre-launch-implementation branch                                        |

| Operation | Mean | Median | Min | Max |
|-----------|------|--------|-----|-----|
| Parse single file (tree-sitter) | ~0.5–2ms range typical | — | — | — |
| Hash all modules | 0.13ms | 0.13ms | 0.13ms | 0.14ms |
| Extract relationships (6 modules) | 0.14ms | 0.08ms | 0.06ms | 0.27ms |
| **Full parse + store** (CLI wall clock) | **0.79–1.15s** | — | — | — |
| Get root nodes (API/Neo4j) | **4.05ms** | 3.65ms | 2.20ms | 6.22ms |
| Search nodes | **17.34ms** | 4.00ms | 3.14ms | 71.70ms |

**Notes**

- Demo package is intentionally tiny; numbers are **correctness/perf smoke**, not 1000-file scale proof.
- Root-node fetch &lt; 50ms on this machine → node expansion goal is **plausible** for small graphs.
- Search mean skewed by cold-start max (71ms); median 4ms under goal.
- Full-scale (1000 files / 100k files) **not yet measured** — see GitHub issue for follow-up.

### Template for new runs

```text
Date:
Commit:
Hardware:
Neo4j version:
Project / file count:
Results:
```
