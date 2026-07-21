# NeuroCode Audit Implementation Log

**Started:** 2026-07-21  
**Status:** SUBSTANTIALLY COMPLETE (code/config/content); process/publish items deferred for human  

---

## Final Summary

| Metric | Count |
|--------|------:|
| **Items implemented (Code/Config/Content)** | ~55 |
| **Deferred with reason** | ~18 |
| **Needs Human Decision** | 7 (H1–H7) |

### Still risky before a real launch

1. **Issue optics:** agent-generated backlog was **bulk-closed**; remaining human issues #222–#225 track real follow-ups.  
2. **Live GIF:** hero is SVG diagram, not a recorded session GIF (needs running stack capture — #223).  
3. **Type debt:** backend mypy is advisory in CI (pre-existing strict-mode debt); frontend gates on `tsc -p tsconfig.app.json` + full vitest.  
4. **No public launch** executed (H3/H6).  
5. **Demo path** should be friend-tested on a cold machine before Show HN.

### Skills used

| Audit area | Skills installed | Why |
|------------|------------------|-----|
| Art 1/5 packaging | `kostja94/marketing-skills@github` | GitHub About/topics/README norms |
| Art 2 CI | `bobmatnyc/claude-mpm-skills@github-actions` | Workflow patterns |
| Art 2 API | `mindrally/skills@fastapi-python` | FastAPI patterns |

---

## Needs Human Decision

| ID | Question | Blocks |
|----|----------|--------|
| H1 | GitHub Sponsors username for optional FUNDING.yml? | Optional funding |
| H2 | Preferred security contact beyond private vuln reporting? | SECURITY.md email line |
| H3 | Authorize public Show HN / Reddit / Awesome PRs? | Launch execute |
| H4 | ~~Authorize bulk close of ~100 agent issues via `gh`?~~ **DONE** (closed as not-planned) | Issue count optics |
| H5 | Enable GitHub Discussions? | Launch Q&A |
| H6 | Launch calendar date for Show HN? | Art 8 |
| H7 | Day-90 monetization go/no-go after metrics? | Art 10 Stage 1+ |

---

## Artifact completion

| Artifact | Status | Notes |
|----------|--------|-------|
| 01 Positioning | **done** (code/content) | GitHub description+topics set via `gh` |
| 02 Tech health | **done** (major) | CI/lint/security workflows, LICENSE, SECURITY, path auth, parser fixes; agent issues bulk-closed (H4) |
| 03 UI | **done** (content/code) | SVG hero; live GIF deferred |
| 04 UX | **done** | make demo + empty/health UI |
| 05 SEO | **done** (in-repo) | topics, llms.txt; Awesome PRs not submitted |
| 06 Marketing | **done** (drafts only) | no publish |
| 07 Pre-launch | **partial** | exit tracker updated; Phase D release tag needs human |
| 08 Launch day | **done** (runbook only) | no execute |
| 09 Post-launch | **done** (docs) | cadence docs; no post-launch activity |
| 10 Monetization | **done** Stage 0 | LICENSE + MONETIZATION_STAGE0.md |
| 11 Metrics | **done** | metrics-log template + baseline row |
| 12 Risks | **done** (mitigations in code/docs) | bus factor, path auth, README truth |

---

## Key deliverables landed

- `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`  
- `.github/workflows/ci.yml`, `lint.yml`, `security.yml`, `.github/dependabot.yml`, `.pre-commit-config.yaml`  
- Local parity: `make check` / `scripts/check.sh` mirrors CI scopes  

- `make demo` / `scripts/first_run.sh` / `examples/demo_pkg`  
- README rewrite (persona, ReactFlow, goals not claims, competitor table, hero SVG)  
- Parse allowlist (`API_ALLOWED_PARSE_PATHS`) + tests  
- GET `/search`, rate-limit fix, tree-sitter 0.26 compat, `body_hash`  
- Frontend: legend, empty CTA, health banners, WebSocket in App  
- `llms.txt`, launch drafts under `docs/launch/` (unpublished)  
- GitHub About + topics set on remote  

---

## Deferred (with reasons)

| Item | Reason |
|------|--------|
| Bulk issue triage to &lt;25 | H4 required before mass close |
| Live 15–30s GIF | Needs running stack + recording; SVG shipped as interim |
| Hosted public demo | Security redesign + human host decision |
| Show HN execute | H3/H6 |
| Awesome-list PRs submit | H3 |
| FUNDING.yml | H1 premature |
| Opt-in CLI telemetry | Explicitly day-30 decision |
| React 19 migration | Post-launch |
| Full frontend tsc green | Pre-existing debt; CI uses stable subset |
| v0.1.0 GitHub Release tag | Human after exit criteria |

---

## Discovered During Implementation

1. **tree-sitter 0.26** removed `set_max_depth` and requires bytes for `parse()` — fixed.  
2. **from-import parser** overwrote module name with last imported identifier — fixed.  
3. **Rate limit middleware** had invalid `async with` in sync method + broken ASGI headers — rewritten.  
4. **Search was POST-only** while docs/tests/frontend expect GET — added GET.  
5. **`allowed_parse_paths` allowlist never applied** (checked wrong settings attribute) — fixed + `NoDecode`.  
6. **Frontend missing ESLint config** — added `.eslintrc.cjs`.  
7. **localStorage missing in vitest** broke zustand persist tests — polyfilled in setup.

---

## Commits (traceability)

```text
[audit:02] Add MIT LICENSE, SECURITY.md, CI, and Dependabot
[audit:01] Position NeuroCode: persona, ReactFlow stack truth, README SEO
[audit:04] One-command first graph: demo package, make demo, Neo4j 5.26
[audit:02] Enforce parse path allowlist; fix parser, search GET, rate limit
[audit:03] Legend, empty-state CTA, health banners, WebSocket wiring
[audit:05-12] Launch docs, metrics log, benchmarks, UI tokens, audit pack
```

*(plus this log update)*
