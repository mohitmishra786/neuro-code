# Benchmarks & performance goals

**Last updated:** 2026-07-21  

## Design goals (not claims of measured production performance)

These match the product architecture constraints (lazy root load, single-node expand, etc.):

| Metric | Goal | Implementation intent |
|--------|------|------------------------|
| Initial page load | &lt; 2s | Load root packages only |
| Node expansion | &lt; 50ms | Single expand API + cache |
| Interactive FPS | 60 FPS | ReactFlow layout for visible subset |
| Parse 1000 files | &lt; 30s | Tree-sitter + 4-pass parser |
| Incremental update | &lt; 1s | Merkle + watcher |
| Max design scale | 100k files | Lazy load + pagination |
| Search | &lt; 200ms | Neo4j full-text (when indexed) |

## How to measure locally

```bash
# Requires Neo4j running and backend deps installed
python scripts/benchmark.py /path/to/python/project
```

Record hardware, OS, Neo4j version, and NeuroCode commit when pasting results below.

## Recorded results

### Template

```
Date:
Commit:
Hardware:
Neo4j version:
Project / file count:
Results:
  - parse mean_ms:
  - notes:
```

### Runs

*No checked-in production benchmark run yet.*  
When CI or a maintainer runs `scripts/benchmark.py` against a public repo (e.g. `requests`, Flask), paste the table here and only then promote numbers into marketing copy.

### Micro-validation (demo package)

The bundled `examples/demo_pkg` is intentionally tiny (&lt;10 modules) and is **not** a performance benchmark—only a first-run correctness fixture.
