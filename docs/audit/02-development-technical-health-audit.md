# Artifact 2: Development & Technical Health Audit

**Date of audit:** July 2026  
**Scope:** structure, tests, lint, CI/CD, performance claims, issues, dependencies, security

---

## Current State

### Repo structure (verified)

```
neuro-code/
├── backend/     # FastAPI, parser, graph_db, merkle, watcher, tests, utils
├── frontend/    # React 18 + Vite + Zustand + ReactFlow
├── docker/      # docker-compose (neo4j + backend + frontend), Dockerfiles
├── docs/        # API.md, ARCHITECTURE.md, DEPLOYMENT.md
├── scripts/     # parse_codebase.py, parse_deep.py, init_database.py, benchmark.py
└── AGENTS.md    # agent conventions (build/lint/test)
```

Structure is coherent and modular. Backend packages map cleanly to documented architecture. Frontend follows components / hooks / stores / services / types.

### Tests

| Area | Present | Notes |
|------|---------|-------|
| Backend pytest | Yes — 12 `test_*.py` files under `backend/tests/` | Covers parser, merkle, neo4j lifecycle/validation, API, logging, request id, streaming |
| Frontend vitest | Yes — 11 `*.test.*` files | TreeGraph, SearchBar, ErrorBoundary, treeStore, cache, api-config, types |
| Coverage reporting | Scripts exist (`pytest-cov`, `vitest --coverage`) | **No coverage thresholds or published coverage % found** |
| E2E / integration | Partial | API tests present; no Playwright/Cypress found; full stack path not clearly automated |

**Unverified without running:** whether all tests pass on a clean machine today. This audit did not execute the full suite against a live Neo4j.

### Linting / typing

| Tool | Documented | Config present | CI enforced? |
|------|------------|----------------|--------------|
| ruff | README + AGENTS.md | `backend/pyproject.toml` `[tool.ruff]` | **No CI found** |
| mypy | README + AGENTS.md | Expected via dev deps | **No CI** |
| black | in requirements/pyproject | listed | **No CI** |
| pre-commit | in dev deps | package listed | **No `.pre-commit-config.yaml` found in tree** |
| eslint | `npm run lint` | package.json | **No CI** |
| tsc strict | `type-check` script; commits mention strict TS | tsconfig present | **No CI** |

### CI/CD

- **Local clone:** no `.github/` directory at repo root (`ls .github` → none).
- **Remote:** Dependabot PR `#220` (rollup bump, opened 2026-02-28) proves **some** dependency automation exists, but **workflow YAML is not in this tree** (API `contents/.github` → 404). Possible causes: Dependabot enabled via UI without workflows checked in; workflows never added; or directory not present on `main`.
- **Conclusion:** There is **no evidence of GitHub Actions running pytest/eslint/type-check on every PR**. Quality gates are documentation-only.

### Performance targets — aspirational vs proven

From README and `docs/ARCHITECTURE.md`:

| Metric | Target | Evidence in repo |
|--------|--------|------------------|
| Initial page load | &lt; 2s | Design intent (load roots only) — **no published numbers** |
| Node expansion | &lt; 50ms | Design intent — **no published numbers** |
| Rendering FPS | 60 FPS | Claimed for ReactFlow virtualization — **unmeasured publicly**; ReactFlow is not WebGL Sigma |
| Parse 1000 files | &lt; 30s | `scripts/benchmark.py` exists — **no checked-in results / CI benchmark** |
| Incremental update | &lt; 1s | Design — **unverified** |
| Max codebase | 100,000 files | Stated max — **no load test artifacts** |
| Search | &lt; 200ms (Architecture only) | **unverified**; open P0 on fuzzy search bottleneck (#102) |

**Flag explicitly:** Treat the Performance Targets table as **product goals / design constraints**, not as measured claims. Shipping them in README as if achieved is a credibility risk under launch scrutiny.

### Open issues (123) — categorization

All open issues returned by `gh` share labels of the form `priority:p0|p1|p2` and `category:*`. Title prefixes:

| Prefix / theme | Approx count | Nature |
|----------------|--------------|--------|
| PERFORMANCE-P* | ~39 labeled category:performance | Agent-generated perf debt |
| BOTTLENECK-P* | ~25 | Agent-generated bottlenecks |
| MEMORY-P* | ~24 | Memory concerns |
| ASYNC-P* | ~22 | Async/concurrency |
| TYPESCRIPT-P* | ~11 | TS style/type hygiene |
| EDGE-P* | ~11 | UX edge cases (tooltips, mobile, keyboard) |

**Priority split (labels):** p2≈58, p1≈42, p0≈23.

**Sample P0 titles (real issues):**  
#102 Search fuzzy matching, #101 Global lock on ChangeDetector, #98 Dagre layout on main thread, #71 ReactFlow internal state accumulation, #42 No rate limiting on search, #10 O(N²) reference extraction, #9 UI blocking layout, #3/#4 batch DB writes, etc.

**Critical observation:** Issue bodies are stamped *“Created by OpenCode Agent”* — this is **not a community backlog**. It is an **internal automated tech-debt dump** from a single day (2026-02-07).  

**Issue-to-PR ratio:** 123 open issues vs **1 open PR** (Dependabot only). Human feature/bug PRs from outsiders: **0**. That ratio is a **red flag for launch optics** (looks abandoned/unmaintained) even if many issues are low-value style nits.

**Closed issues:** 87 — also largely agent-style `[BACKEND-P2]` hygiene items, not external bug reports.

### Dependency health (July 2026 research)

| Dependency | In project | Current ecosystem note (July 2026) | Risk |
|------------|------------|-------------------------------------|------|
| **React** | ^18.3.1 | React 19 is current (docs list 19.2.x as of mid-2026). React 18 active support ended when 19 shipped (Dec 2024); security-only / EOL discussions in 2025–26 (endoflife.date/react, community posts). | Medium — still widely used; plan React 19 migration post-launch |
| **ReactFlow** | ^11.11.3 | Active (library rebranded toward “xyflow” ecosystem historically). | Low–medium — stick to supported majors |
| **Vite** | ^7.3.1 | Modern; keep patched | Low |
| **Zustand** | ^4.5.0 | Mature | Low |
| **Neo4j** | Docker `neo4j:5.15-community`; driver `neo4j==5.17.0` | Neo4j moved to calendar versions 2025.x/2026.x; **5.26 LTS** supported to **June 2028** (Neo4j blog/KB). 5.15 is behind LTS. | Medium — pin to **5.26-community** for LTS |
| **FastAPI** | pinned 0.109.2 in pyproject | Ecosystem has advanced; 0.109 is old by mid-2026 standards | Medium — upgrade path needed |
| **tree-sitter** | 0.21.x | Fine for Python grammar use | Low |
| **Python** | 3.11+ required | Appropriate | Low |

### Security basics

| Control | Status | Evidence |
|---------|--------|----------|
| SECURITY.md | **Missing** | no file |
| LICENSE file | **Missing** (claim MIT in README/pyproject) | GitHub license null |
| Dependabot | Partial (PR exists) | #220; no local `.github/dependabot.yml` |
| Secrets handling | `.env.example` for Neo4j password; docker-compose hardcodes `neo4j/neurocode_password` | Expected for local, bad if demos use same |
| API auth | **No general auth**; docs: “Currently no authentication required (development mode)” | `docs/API.md` |
| API key | Optional only for `DELETE /graph/clear` if `API_KEY` set | `graph.py` + `config.py` |
| Parse endpoint | Accepts filesystem path; path allowlist exists in settings (`allowed_parse_paths`) — **must verify enforced on all parse paths before any hosted deploy** | `config.py`; partial checks in graph routes |
| Rate limiting | Implemented middleware; default enabled | `rate_limit.py`, `main.py` |
| CORS | Dev defaults localhost:3000; production empty unless set | `config.py` |
| OpenAPI docs | Disabled outside development | `main.py` |

**If ever hosted without auth, anyone who can reach the API can parse paths / mutate graph (subject to rate limits and path policy).** Treat as local-dev security model only.

### Other technical gaps

- `pyproject.toml` defines console script `neurocode = "neurocode.cli:main"` but **no `neurocode` package / CLI module** was found as described — dead packaging surface.
- Homepage URLs in packaging still `your-org/neurocode`.
- Realtime: `useWebSocket` exported but **not used in `App.tsx`** — live updates incomplete product-wise.

---

## Gaps / Risks

1. **No CI** → regressions likely under contributor load; launch-day PR spam unguarded.
2. **123 agent issues** look like neglect; will scare external contributors during Show HN.
3. **Unproven performance table** in README.
4. **React 18 / Neo4j 5.15 / FastAPI 0.109** drift from 2026 baselines.
5. **Missing LICENSE file** despite MIT claim — legal clarity blocker for companies.
6. **Security model is local-only** — fine for OSS self-host, fatal if “hosted demo” is bolted on without redesign.
7. **Single maintainer bus factor** (see Risk Register).

---

## Checklist

### Pre-Launch (tech debt burn-down)

- [ ] **Add `.github/workflows/ci.yml`:** backend `pytest`, frontend `npm test` + `lint` + `type-check`, on push/PR. (Effort: **M**). *Verify:* green check on a dummy PR.
- [ ] **Add root `LICENSE` MIT file** matching claim. (Effort: **S**). *Verify:* GitHub shows MIT badge.
- [ ] **Add `SECURITY.md`** with private report email/process. (Effort: **S**)
- [ ] **Triage 123 issues in one pass** (Effort: **M**, ~half day):
  - Close pure style nits with reason “tracked offline / won’t fix pre-v1”
  - Keep true P0 functional risks in a milestone `v0.1-launch`
  - Label `agent-generated` vs `user-reported`
  - Target: **&lt;25 open issues** before launch
  - *Verify:* open issue count &lt;25; ratio issues:active-PRs improved
- [ ] **Pin Neo4j image to 5.26-community (LTS)** in docker-compose. (Effort: **S**). *Source:* Neo4j 5.26 LTS hotfixes until June 2028.
- [ ] **Run `scripts/benchmark.py` on a known repo** (e.g. Flask or requests), paste results into `docs/BENCHMARKS.md`. (Effort: **M**). *Verify:* doc exists with date + hardware.
- [ ] **Demote README Performance Targets** to “Goals” or replace with measured numbers only. (Effort: **S**)
- [ ] **Fix stack claim:** ReactFlow not Sigma. (Effort: **S**)
- [ ] **Wire or remove dead surfaces:** CLI entrypoint claim, unused WebSocket hook in UI. (Effort: **M**)
- [ ] **Commit Dependabot config** explicitly if using it. (Effort: **S**)

### Launch-blocking bugs (recommended gate)

Treat as launch-blockers only if reproducible on the **demo path** (parse sample repo → expand 3 levels → search):

- [ ] Parse of demo repo succeeds end-to-end. (Effort: **M** if broken)
- [ ] Empty state + Neo4j-down error paths are non-silent. (Effort: **S–M**)
- [ ] Search does not lock up UI/DB under light use (related to #102/#42). (Effort: **M**)
- [ ] No path that allows remote RCE-style “parse any path” on a public demo host. (Effort: **L** if hosting; **N/A** if demo is local-only screenshots)

### Post-Launch maintenance cadence

- [ ] **Release schedule:** tag `v0.1.0` at launch; then **biweekly** patch tags or “when something user-visible ships.” (Effort: **S** process)
- [ ] **SemVer:** 0.x until multi-user API stability; breaking changes OK with CHANGELOG. (Effort: **S**)
- [ ] **CHANGELOG.md** Keep-a-Changelog format. (Effort: **S**)
- [ ] **Issue SLA (solo maintainer):** acknowledge within 72h; no guarantee of fix time; document in CONTRIBUTING. (Effort: **S**)
- [ ] **Monthly dependency review** (or Dependabot weekly + human merge). (Effort: **S** ongoing)
- [ ] **Quarterly React 19 / Neo4j LTS upgrade evaluation.** (Effort: **M** each)

### Recommended issue triage process

1. Close as **not planned** anything that is style-only pre-v1.
2. Milestone **launch-blockers** (demo path only).
3. Milestone **v0.2** for real perf work (batch writes, worker parse, layout off main thread).
4. Require **repro steps** for any new issue after launch.
5. Prefer PRs over issue spam; add `good first issue` only for 2–3 real tasks with acceptance criteria.
