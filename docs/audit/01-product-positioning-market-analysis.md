# Artifact 1: Product Positioning & Market Analysis

**Date of audit:** July 2026  
**Repo ground truth:** local clone of `mohitmishra786/neuro-code` + `gh` metadata  
**External claims:** verified via web search July 2026

---

## Current State

### What NeuroCode actually is (from code + docs)

NeuroCode is a **self-hosted Python codebase explorer** that:

1. Parses Python with **Tree-sitter + AST** (`backend/parser/`, 4-pass pipeline documented in `docs/ARCHITECTURE.md`)
2. Stores hierarchy and relationships in **Neo4j** (`backend/graph_db/`)
3. Detects incremental changes via a **Merkle-tree** layer (`backend/merkle/`)
4. Watches the filesystem (`backend/watcher/`) and exposes **FastAPI REST + WebSocket** (`backend/api/`)
5. Renders an interactive hierarchical graph in **React + ReactFlow + dagre** (`frontend/src/components/TreeGraph.tsx`)

**Important discrepancy:** The README Technology Stack claims **“Sigma.js v3 (WebGL)”**, but `frontend/package.json` depends on `reactflow` ^11.11.3 and `dagre`; `TreeGraph.tsx` imports ReactFlow exclusively. There is **no Sigma.js dependency**. Architecture docs correctly describe ReactFlow. Marketing copy that claims WebGL/Sigma is currently **false**.

**Version / maturity signals (repo + GitHub, July 2026):**

| Signal | Value | Source |
|--------|--------|--------|
| Stars / forks | 0 / 0 | `gh api repos/mohitmishra786/neuro-code` |
| Open issues | 123 | GitHub search API |
| Closed issues | 87 | GitHub search API |
| Open PRs | 1 (Dependabot rollup bump) | `gh pr list` |
| Releases | none | `gh release list` empty |
| GitHub description | `null` | API |
| Topics / homepage | empty / null | API |
| License file | **missing on disk**; README + `pyproject.toml` claim MIT | `find LICENSE*` empty; GitHub `license: null` |
| Contributors | essentially single human (`mohitmishra786` / Mohit Mishra) + Dependabot | `gh api .../contributors` |
| Created | 2026-01-13 | API |
| Last push (as of audit) | 2026-02-28 | API |

### How it is currently described

- **README H1 subtitle:** “Interactive Hierarchical Code Visualization System” — generic; no audience, no problem, no outcome.
- **README pitch:** “Transform Python codebases into explorable, hierarchical knowledge graphs with instant, smooth navigation.” — still feature-centric, not job-to-be-done.
- **GitHub About:** empty (no description, no website, no topics).
- **Clone URL in README:** `https://github.com/your-org/neurocode.git` — placeholder; wrong org/name vs real repo.
- **`pyproject.toml` URLs:** also `your-org/neurocode` placeholders.
- **No screenshots, GIFs, demo URL, or video** in README or `docs/`.

### Competitive landscape (verified July 2026)

Research sources: CodeLayers “Complete Guide to Code Visualization in 2026” (Feb 21, 2026); CodeSee/GitKraken acquisition coverage (May 2024, still referenced 2026); Sourcegraph product pages 2026; VS Code Marketplace CodeGraph Tools; CTO Club / RepoWise comparison roundups 2026.

| Tool | Status (2026) | Model | Overlap with NeuroCode | Key difference |
|------|---------------|-------|------------------------|----------------|
| **Sourcetrail** | Discontinued Dec 2021; archived; forks unmaintained | Local desktop, multi-lang | Closest historical “code graph explorer” UX | Market gap still searched; CodeLayers blog notes “Sourcetrail alternative” remains a high-intent query |
| **CodeSee** | Acquired by GitKraken (May 2024); standalone product shut down commercial ops; remnants inside GitKraken DevEx | Cloud SaaS → platform feature | Onboarding / map of code | Not a standalone OSS competitor anymore |
| **Sourcegraph** | Active; code search + intelligence + Cody AI; large enterprise | Search / nav / AI, not primary visual hierarchy graph | “Understand large codebases” job | Different product category: search-first, multi-repo, AI agents; not a hierarchical knowledge-graph UI |
| **GitHub code navigation** | Built-in | IDE/hosting | Go-to-def / refs | No architectural graph, no Neo4j-style exploration |
| **CodeLayers** | Active 2026; 3D/spatial, multi-lang, MCP for AI agents | Free public / Pro private (~$7.99/mo) | Visualization of structure + blast radius | 3D, multi-device, multi-lang, zero-knowledge sync, hosted explore UX |
| **CodeViz (YC S24)** | Active | VS Code extension | In-editor architecture maps / C4-ish | Editor-native; lower install friction |
| **CodeGraph Tools** | VS Code marketplace (low installs as of crawl) | VS Code + Python engine; GraphRAG; Neo4j Cypher export | Knowledge graph from code | Editor-first, AI query layer, multi-artifact (docs/binaries) |
| **dependency-cruiser / Madge** | Active OSS | CLI + static SVG | Dependency edges | JS/TS only; not interactive Neo4j explorer |
| **SciTools Understand** | Active enterprise | Desktop static analysis | Deep multi-lang analysis | Price/enterprise; not OSS self-host graph product |
| **Swimm** | Active (docs-as-code / continuous docs) | SaaS | Understanding legacy code | Content/docs, not live hierarchical graph |
| **Repowise / GitScape / similar 2025–26 entrants** | Active marketing sites | Hosted intelligence | “See the repo” narrative | Often AI + ownership/history; less pure self-host graph DB |

**What changed recently (2024–2026):**

1. **Sourcetrail gap is still open** but being filled by 3D tools (CodeLayers), VS Code extensions (CodeViz, CodeGraph), and AI-native graph products—not by many self-hosted Neo4j + hierarchical lazy-load explorers.
2. **CodeSee exit** removed a major SaaS “code map for onboarding” brand.
3. **AI agents** shifted the category: visualization tools now compete on MCP, GraphRAG, and “blast radius for PRs,” not only pretty graphs (CodeLayers guide, Feb 2026).
4. **Tree-sitter** became table stakes for parsers (same guide cites tree-sitter as the common parse layer).

### Differentiation: what NeuroCode’s tech can claim *if true*

| Claimed capability | In repo? | Differentiating for developers? |
|--------------------|----------|----------------------------------|
| Hierarchical lazy expansion (root → package → module → class → function) | Yes (`TreeStore.expandNode`, `/graph/expand`) | **Yes** — most tools dump full force-directed graphs; hierarchy matches mental model of Python packages |
| Neo4j-backed persistent graph | Yes | **Mixed** — powerful for query/power users; heavy for casual “just show me the map” users |
| Merkle incremental change detection | Yes (`backend/merkle/`) | **Yes for long-running watches** — but invisible until live-update works end-to-end |
| File watcher + WebSocket updates | Watcher + WS routes exist; **`useWebSocket` is not wired into `App.tsx`** | **Not currently a product differentiator** — infrastructure half-built |
| Sub-50ms expansion / 60 FPS / 100k files | Stated as **targets** in README/Architecture; **no published benchmark results** | **Do not lead with these until measured** — competitors will challenge |
| Python depth (CONTAINS, CALLS, IMPORTS, INHERITS) | Documented edge types | **Yes for Python specialists** — weaker if multi-lang is expected |
| Sigma.js WebGL 100k scale | **False in current stack** (ReactFlow) | Harmful if claimed |

**Honest differentiation thesis:** NeuroCode’s viable wedge is **“Sourcetrail-shaped, self-hosted, Python-first hierarchical explorer with a real graph DB you own”**—not “AI 3D blast radius,” not “VS Code one-click,” not “WebGL at 100k files.” That wedge is narrower than CodeLayers/Sourcegraph but still real for privacy-conscious Python teams and educators.

### Candidate target users

| Segment | Pain | Fit today | Launch viability |
|---------|------|-----------|------------------|
| **A. Engineers onboarding to large legacy Python monorepos** | Can’t see architecture | High if setup is simplified | **Primary** — classic Sourcetrail/CodeSee job |
| **B. Tech leads doing architecture reviews** | Need call/import structure | Medium (needs reliable CALLS edges + exports) | Secondary |
| **C. OSS Python maintainers** | Explain structure to contributors | Medium (needs public demo of famous repos) | Strong content engine |
| **D. Educators / CS courses** | Teach package structure | High for simple demos | Good early adopters; low willingness to pay |
| **E. AI agent / GraphRAG builders** | Need code graph as context | Adjacent (Neo4j is useful) | Not ready without APIs/docs polish + multi-lang |

**Recommended launch persona:** **Segment A** — mid-level Python engineer dropped into a 50k–500k LOC legacy service who wants a local graph without sending code to a SaaS. Design every first-run, README, and Show HN line around that job.

---

## Gaps / Risks

1. **No positioning on GitHub** → zero organic discovery via topics/description.
2. **Tech claim mismatch (Sigma vs ReactFlow)** → credibility risk on first technical read.
3. **Placeholder clone URLs** → broken first experience.
4. **Category crowded by zero-install tools** (CodeLayers Explore, VS Code extensions) while NeuroCode is multi-service local stack.
5. **No visual proof** → visualization product without visuals is self-defeating (see Artifact 3).
6. **Performance targets unproven** → do not use as primary pitch.
7. **Python-only** vs multi-lang competitors — must be framed as depth, not incompleteness.

---

## Checklist

### Pre-Launch

- [ ] **Lock primary persona:** “Python engineer onboarding to a large unfamiliar codebase” (Effort: **S**). *Verify:* one-sentence persona in README + CONTRIBUTING.
- [ ] **Choose tagline** (pick one; Effort: **S**):
  - Recommended: **“See the architecture of any Python codebase—locally, as a hierarchical knowledge graph.”**
  - Alt A: “Sourcetrail-style exploration for modern Python monorepos.”
  - Alt B: “Tree-sitter → Neo4j → interactive code map. Self-hosted.”
- [ ] **One-sentence pitch:** “NeuroCode parses your Python project into a Neo4j graph and lets you expand packages, classes, and calls in a hierarchical UI—fully local.” (Effort: **S**)
- [ ] **One-paragraph pitch** (for Show HN / README top): problem → approach → who → what’s free. (Effort: **S**)
- [ ] **GitHub About:** set description (≤350 chars) to the one-sentence pitch; homepage when demo exists. (Effort: **S**) *Verify:* `gh repo view` shows description.
- [ ] **GitHub topics** (Effort: **S**): `python`, `code-visualization`, `neo4j`, `tree-sitter`, `ast`, `code-intelligence`, `developer-tools`, `fastapi`, `react`, `knowledge-graph`. *Verify:* topics appear on repo page.
- [ ] **Fix README stack line:** ReactFlow + dagre (not Sigma.js). (Effort: **S**) *Verify:* no “Sigma” in README.
- [ ] **Fix clone URLs** to `mohitmishra786/neuro-code`. (Effort: **S**)
- [ ] **Competitor comparison table** (short) in README under “How NeuroCode compares” with honest columns: Local, Python-first, Hierarchical UI, Graph DB, Install friction. (Effort: **M**)
- [ ] **Do not claim** 50ms / 60 FPS / 100k files until Artifact 2 benchmarks exist. (Effort: **S** policy)

### Launch

- [ ] Lead Show HN / PH copy with **persona + local privacy + hierarchical expand**, not database brand names. (Effort: **S**)
- [ ] Name Sourcetrail explicitly as historical inspiration / gap-filler if accurate to product intent. (Effort: **S**)

### Post-Launch

- [ ] After 50 stars or first 10 real users, **re-validate persona** via issue labels / discussions (Effort: **M**). *Verify:* ≥5 qualitative user notes.
- [ ] Decide multi-language only after Python depth is trusted (Effort: **L** strategy).

### Suggested copy (ready to paste)

**GitHub About description:**  
`Local hierarchical knowledge graph for Python codebases. Tree-sitter → Neo4j → interactive React explorer. Self-hosted.`

**README hero (replace current subtitle):**  
`# NeuroCode`  
`See the architecture of any Python codebase—as a hierarchical knowledge graph you host yourself.`

---

## Competitor comparison (for README / site)

| | NeuroCode | Sourcegraph | CodeLayers | CodeViz / VS Code maps | dependency-cruiser |
|--|-----------|-------------|------------|------------------------|--------------------|
| Primary job | Hierarchical code graph | Search + AI code intel | 3D spatial deps | In-editor map | Dep rules + SVG |
| Languages | Python (today) | Multi | Multi (~10–12) | Multi | JS/TS |
| Hosting | Self-host (Neo4j) | Cloud/self | Cloud + local encrypt | Local IDE | Local CLI |
| Install friction | High (multi-service) | Medium | Low (explore URL) | Low | Low |
| Graph DB | Neo4j | Custom | Proprietary | Session | None |
| Open source | MIT-claimed (file missing—fix) | Mixed / product | Proprietary core | Varies | Yes |

*Sources: repo architecture docs; CodeLayers blog Feb 2026; Sourcegraph site 2026; CodeSee→GitKraken May 2024 coverage; Marketplace listings crawled July 2026.*
