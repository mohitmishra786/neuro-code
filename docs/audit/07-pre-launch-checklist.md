# Artifact 7: Pre-Launch Checklist

**Date:** July 2026  
**Purpose:** Single sequenced punch list consolidating blocking items from Artifacts 1–6.  
**Rule:** Do not announce publicly until Phase D exit criteria are met.

---

## Current State

NeuroCode is **not launch-ready** for a high-visibility Show HN:

- 0 stars, empty GitHub About, no visuals, multi-step setup, 123 open agent issues, no CI, no LICENSE file, tech claim mismatch (Sigma vs ReactFlow), no release tag.

Dependencies between workstreams are real: **positioning copy → README → SEO topics**; **demo assets → marketing posts**; **setup reduction → conversion**; **issue triage → trust**.

---

## Gaps / Risks

Launching without Phase B–D creates a permanent first impression of an unfinished agent-generated repo. Cold re-launches on HN are harder than one solid first Show HN.

---

## Sequenced checklist

### Phase A — Positioning lock (Day 1–2)  
*Depends on: Artifact 1 decisions*  
*Effort total: S*

- [ ] Choose primary persona (recommended: Python engineer onboarding to large codebase)
- [ ] Lock tagline + one-sentence + one-paragraph pitch
- [ ] Set GitHub repository description
- [ ] Set GitHub topics (list in Artifact 5)
- [ ] Fix README clone URL to `mohitmishra786/neuro-code`
- [ ] Remove Sigma.js claim; document ReactFlow + dagre
- [ ] Fix `pyproject.toml` homepage/repository URLs
- [ ] Add root `LICENSE` (MIT)
- [ ] Add `SECURITY.md` stub

**Exit criteria:** `gh repo view` shows description + topics; README top matches pitch.

---

### Phase B — Trust & technical floor (Day 2–7)  
*Depends on: Phase A partially parallelizable*  
*Effort total: M*

- [ ] Add GitHub Actions CI: pytest + frontend test/lint/type-check
- [ ] Confirm green CI on main
- [ ] Triage open issues → target **&lt;25 open** (close agent style nits; milestone real P0s)
- [ ] Label remaining issues clearly (`launch-blocker` vs `later`)
- [ ] Pin Neo4j Docker image to 5.26 LTS (or document why 5.15)
- [ ] Run benchmark on a public repo; write `docs/BENCHMARKS.md` **or** relabel Performance Targets as “Goals”
- [ ] Verify demo path: compose up → parse → expand → search works on a clean machine
- [ ] Fix any launch-blocker bugs found in demo path only

**Exit criteria:** CI green; issue count &lt;25; demo path works twice in a row.

---

### Phase C — Time-to-value (Day 5–12)  
*Depends on: Phase B demo path green*  
*Effort total: M*

- [ ] Add `examples/demo_pkg/` sample Python project
- [ ] Add `scripts/first_run.sh` or `make demo` (compose + parse demo + health checks)
- [ ] Rewrite README Quick Start to **≤4 steps**, Compose-first
- [ ] Empty-state UI shows the same commands
- [ ] Align Node version requirements (18 vs 20)
- [ ] Document default credentials/ports table

**Exit criteria:** New machine (or friend) reaches first graph in **&lt;10 minutes** following README only.

---

### Phase D — Proof & narrative (Day 10–16)  
*Depends on: Phase C*  
*Effort total: M*

- [ ] Capture 15–30s hero GIF + 3 screenshots
- [ ] Place visuals above the fold in README
- [ ] Add in-UI “double-click to expand” hint + node/edge legend
- [ ] Tag GitHub Release `v0.1.0` with changelog
- [ ] Draft Show HN post + first comment (Artifact 6)
- [ ] Dry-run post with 2 engineers; fix setup complaints
- [ ] Prepare known-limitations blurb
- [ ] Optional: Product Hunt assets ready
- [ ] Optional: social OG image set

**Exit criteria:** README communicates value without running code; launch posts drafted; release tagged.

---

### Phase E — Soft warm-up (optional, Day 14–18)

- [ ] Soft share GIF with small audience (friends, Neo4j discord) — not full launch
- [ ] Fix last-mile setup issues discovered
- [ ] Schedule Show HN calendar block (Tue–Thu 8–10am ET, 2h reply window)

**Exit criteria:** Calendar hold confirmed; hotfix branch process known (Artifact 8).

---

## Explicit dependency graph

```
Positioning (A) ──► README/SEO copy
       │
       ▼
Tech floor (B) ──► Demo reliability
       │
       ▼
Setup reduction (C) ──► Friend test &lt;10 min
       │
       ▼
Visuals + launch copy (D) ──► Show HN eligible
       │
       ▼
Launch day (Artifact 8)
```

Marketing (Artifact 6) **must not** start public amplification before **D**.

---

## Pre-Launch checklist (flat copy-paste tracker)

### Positioning & GitHub
- [ ] Persona locked
- [ ] Tagline locked
- [ ] About description set
- [ ] Topics set
- [ ] Clone URL fixed
- [ ] Sigma claim removed
- [ ] LICENSE file present
- [ ] SECURITY.md present

### Engineering
- [ ] CI pipeline green
- [ ] Open issues &lt;25
- [ ] Launch-blocker milestone empty or accepted risks listed
- [ ] Benchmarks published **or** targets labeled goals
- [ ] Neo4j version decision documented
- [ ] Demo path verified twice

### Activation
- [ ] Demo package in repo
- [ ] One-command / make demo path
- [ ] README ≤4 steps
- [ ] Empty state has commands

### Proof & launch assets
- [ ] Hero GIF in README
- [ ] Screenshots in README
- [ ] v0.1.0 release
- [ ] Show HN draft ready
- [ ] Limitations list ready
- [ ] Launch calendar blocked
