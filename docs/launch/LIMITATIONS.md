# Known limitations (v0.1.x)

Paste-friendly for HN / issues.

1. **Python only** — other languages are out of scope for 0.1.  
2. **Local / self-hosted** — no public hosted multi-tenant demo yet. Docker recommended.  
3. **API has no general auth** — bind to localhost; do not expose to the internet.  
4. **Performance table is goals** — see `docs/BENCHMARKS.md`; do not treat as SLAs.  
5. **Desktop UI** — mobile/touch not a primary target.  
6. **CALLS edge quality** depends on static analysis limits (dynamic calls, complex imports).  
7. **Neo4j is a hard dependency** — heavier than a pure VS Code extension.  
8. **Early alpha** — expect breaking changes in 0.x.  
9. **Live updates** require watcher + WebSocket; first-run is still parse-then-view.  
10. **Issue tracker** may still contain historical agent-generated debt being triaged.
