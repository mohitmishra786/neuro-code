# Artifact 4: UX / User Workflow Audit

**Date of audit:** July 2026  
**Ground truth:** README Quick Start, `docs/DEPLOYMENT.md`, `docker/docker-compose.yml`, frontend empty states

---

## Current State

### Documented happy path (README “Quick Start”)

| Step | Action | Terminal / context switch |
|------|--------|---------------------------|
| 1 | `git clone` (placeholder URL) | 1 |
| 2 | Python 3.11 venv + `pip install -r backend/requirements.txt` | 1 |
| 3 | Start Neo4j via docker-compose (neo4j only) | 1 + Docker required |
| 4 | `cd frontend && npm install && npm run dev` | 2nd terminal |
| 5 | `cd backend && uvicorn ...` | 3rd terminal |
| 6 | `python scripts/parse_codebase.py /path/to/project` | 4th terminal / same with venv |
| 7 | Open `http://localhost:3000` | Browser |

**Explicit count: 7 steps, ≥3 concurrent processes (Neo4j, API, Vite), Docker + Python 3.11 + Node 18+, and a separate parse before any graph appears.**

Additional friction points:

1. **Broken clone URL** (`your-org/neurocode`) — fails step 1 if copy-pasted.
2. **No `.env` creation** in README Quick Start (DEPLOYMENT mentions `cp .env.example .env`; password must match Neo4j).
3. **No `init_database.py` in Quick Start** though DEPLOYMENT lists it.
4. **Parse path is absolute-ish user knowledge** — user must already have a Python project.
5. **Empty UI** after server start if parse not run: “No Code Structure” without command cheat-sheet.
6. **Docker Compose full stack exists** (`docker/docker-compose.yml` for neo4j+backend+frontend) but is **not** the README Quick Start primary path — buried under “optional.”
7. **Even Compose does not auto-parse** a demo codebase — still zero nodes until a CLI/API parse.
8. **WebSocket live updates** not wired in App — “real-time” architecture story incomplete in UX.
9. **Python-only** — user may not know multi-lang fails silently / empty until they try.

### Alternate path (DEPLOYMENT.md)

“Docker Compose (Recommended)” is better: one `docker-compose up -d` for three services — but still requires host-side parse for data, and README undercuts this by teaching the hard path first.

### Friction vs competitor benchmarks (2026)

| Product pattern | Time to first value (typical) | Source of pattern |
|-----------------|-------------------------------|-------------------|
| VS Code extension install (CodeViz, CodeGraph) | 1–3 minutes | Marketplace one-click + command palette |
| `npx` / CLI one-liner + browser | 2–5 minutes | Common OSS devtools |
| Hosted “paste GitHub URL” explore (e.g. CodeLayers Explore, free public) | **Seconds** | CodeLayers blog Feb 2026 “no install, no account” |
| SciTools / heavy desktop | 15–60 min install + license | Enterprise |
| **NeuroCode today** | **30–90+ minutes** for a new user (estimate; not user-tested) | Multi-service + Neo4j + manual parse |

**Unverified:** actual median setup time — no instrumentation, no user tests in repo. The step count alone puts NeuroCode in the **worst quartile** of modern OSS developer tools for activation.

### Time-to-first-graph reduction plan

| Phase | Change | Target time to graph | Effort |
|-------|--------|----------------------|--------|
| **P0** | README leads with Compose; fix clone URL; add `.env` copy steps | 20–40 min | S |
| **P1** | Bundle `examples/tiny_demo/` Python package + `make demo` that compose-up + parses demo | **&lt;10 min** | M |
| **P2** | Single script `./scripts/first_run.sh` (checks docker, up, parse, prints URL) | **&lt;5 min** unattended | M |
| **P3** | Public read-only hosted demo of CPython subset / Flask | **&lt;10 sec** | L (hosting + security) |
| **P4** | Optional VS Code “open graph” later | competitive with extensions | L |

Recommended sequence: **P0 → P1 → P2 before any Show HN**. Hosted demo (P3) is highest growth leverage but requires security design (Artifact 2/12).

### Journey map (after first graph)

| Stage | Current UX | Gap |
|-------|------------|-----|
| Orient | Root packages appear | Legend? |
| Expand | Double-click node | Discoverability of double-click undocumented in UI |
| Inspect | NodeInfoPanel | Loading indicators incomplete (issue #141) |
| Search | SearchBar | Fuzzy search P0 bottleneck (#102) |
| Navigate | Breadcrumbs | Deep overflow issue (#146) |
| Update code | Watcher/Merkle/WS intended | WS not in App — user must re-parse mentally |

---

## Gaps / Risks

1. **7-step multi-terminal setup is the product’s main conversion killer.**
2. Compose exists but is not productized as “one command to graph.”
3. No demo dataset → parse step is abstract.
4. Double-click expand is easy to miss without onboarding.
5. Error states exist for graph load failure; **setup errors** (Neo4j down, wrong password) surface as empty/error strings without guided recovery in-app.
6. Cannot measure drop-off today (no analytics — Artifact 11).

---

## Checklist

### Pre-Launch

- [ ] **Rewrite Quick Start** to: (1) clone real repo, (2) `cd docker && docker compose up -d`, (3) run parse on demo, (4) open browser. (Effort: **S**). *Verify:* new user script follows 4 steps max in README.
- [ ] **Add `examples/demo_pkg/`** with 3–5 modules illustrating packages, inheritance, calls. (Effort: **S**)
- [ ] **`make demo` or `scripts/first_run.sh`** automating compose + parse demo + healthcheck. (Effort: **M**). *Verify:* cold machine → graph in &lt;10 min documented.
- [ ] **Empty state:** paste exact commands + link to DEPLOYMENT. (Effort: **S**)
- [ ] **In-UI hint:** “Double-click a node with children to expand.” (Effort: **S**)
- [ ] **Health-aware UI:** if `/health` neo4j disconnected, show “Start Neo4j” instructions. (Effort: **M**)
- [ ] **Document ports** 3000/8000/7474/7687 and password defaults in one table. (Effort: **S**)
- [ ] **Align Node version** claims (README 18+ vs DEPLOYMENT 20+). (Effort: **S**)

### Launch

- [ ] First comment on Show HN: **“Fastest path”** 4 lines of shell. (Effort: **S**)
- [ ] If no hosted demo, be explicit: “local only, Docker required.” (Effort: **S**)

### Post-Launch

- [ ] Watch GitHub issues for setup failures; create FAQ from top 5. (Effort: **M** ongoing)
- [ ] Interactive public demo when auth/sandbox ready. (Effort: **L**)
- [ ] Optional one-binary distribution later (e.g. embed lighter store) if Neo4j remains friction #1. (Effort: **L**, strategic)

### Success metrics (when measurable)

- Setup completion rate (survey or optional CLI ping)  
- Median time from clone to first expand (manual study n≥5)  
- % of issues tagged `setup` after launch  
