# NeuroCode Audit Implementation Log

**Started:** 2026-07-21  
**Status:** IN PROGRESS  
**Priority order:** Master index 90-day queue + Phase A→D dependency chain (Art 7)

---

## Final Summary (fill when complete)

- **Total items implemented:** —
- **Total deferred:** —
- **Needs Human Decision:** —
- **Still risky before launch:** —

---

## Needs Human Decision

| ID | Question | Blocks |
|----|----------|--------|
| H1 | Confirm GitHub Sponsors username for optional FUNDING.yml (or skip until Stage 1) | Optional FUNDING.yml |
| H2 | Security contact email for SECURITY.md (defaulting to GitHub private vulnerability reporting) | Prefer real email if available |
| H3 | Authorize public Show HN / Product Hunt / Reddit posts (do not publish without confirmation) | Art 6/8 launch execute |
| H4 | Authorize bulk close of ~100 agent-generated GitHub issues via `gh` | Art 2 issue triage optics |
| H5 | GitHub Discussions enable (repo setting) | Launch Q&A channel |
| H6 | Launch calendar date for Show HN | Art 8 execute |
| H7 | Day-90 monetization go/no-go (after adoption data) | Art 10 Stage 1+ |

---

## Work order (execution sequence)

1. **Art 1** Positioning content (unblocks README/SEO)  
2. **Art 2** LICENSE, SECURITY, CI, Dependabot, Neo4j pin, path auth, CLI/WS, CHANGELOG, goals  
3. **Art 4** Demo package, first_run, empty/health UI, ports docs  
4. **Art 3** Legend, tokens, contrast, visuals (SVG/PNG placeholders + capture script), README visuals  
5. **Art 5** SEO README structure, llms.txt, docs SEO notes  
6. **Art 11** metrics-log, issue label docs  
7. **Art 6** Launch drafts (content only, no publish)  
8. **Art 7/8/9** Runbooks as repo docs (no calendar commits)  
9. **Art 10** LICENSE only + Stage 0 note  
10. **Art 12** Residual risk mitigations not covered above  

---

## Skills installed per audit file

| Audit file | Skills | Notes |
|------------|--------|-------|
| (pending) | — | Will log after find-skills per file |

---

## Artifact 01 — Product Positioning & Market Analysis

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 01.01 | Lock persona in README + CONTRIBUTING | Content | [ ] | Recommended persona |
| 01.02 | Lock tagline (recommended) | Content | [ ] | |
| 01.03 | One-sentence + one-paragraph pitch in README | Content | [ ] | |
| 01.04 | Set GitHub About description via `gh` | Config | [ ] | |
| 01.05 | Set GitHub topics via `gh` | Config | [ ] | |
| 01.06 | Fix README stack: ReactFlow not Sigma | Content | [ ] | |
| 01.07 | Fix clone URLs to mohitmishra786/neuro-code | Content | [ ] | |
| 01.08 | Competitor comparison table in README | Content | [ ] | |
| 01.09 | Do not claim unmeasured perf; Goals language | Content | [ ] | |
| 01.10 | Fix pyproject.toml URLs | Config | [ ] | |
| 01.11 | Show HN copy lead with persona | Content | [ ] | With Art 6 |
| 01.12 | Post-launch persona revalidation | Process | [-] | After 50 stars |
| 01.13 | Multi-language decision | Process | [-] | Strategy later |

---

## Artifact 02 — Development & Technical Health

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 02.01 | Add `.github/workflows/ci.yml` | Config | [ ] | |
| 02.02 | Add MIT LICENSE | Content | [ ] | |
| 02.03 | Add SECURITY.md | Content | [ ] | |
| 02.04 | Triage GitHub issues to &lt;25 | Process/Config | [ ] | Needs H4 for bulk close |
| 02.05 | Pin Neo4j to 5.26-community LTS | Config | [ ] | Verify image exists |
| 02.06 | Run benchmarks → docs/BENCHMARKS.md | Content | [ ] | Or goals if Neo4j unavailable |
| 02.07 | Demote Performance Targets to Goals | Content | [ ] | |
| 02.08 | Fix Sigma→ReactFlow (stack) | Content | [ ] | Dup 01.06 |
| 02.09 | Wire WebSocket in App OR remove real-time claims | Code | [ ] | Wire if WS works |
| 02.10 | Fix/remove dead CLI entrypoint | Code | [ ] | Implement minimal CLI or remove |
| 02.11 | Commit dependabot.yml | Config | [ ] | |
| 02.12 | Enforce allowed_parse_paths on parse API | Code | [ ] | Security R14 |
| 02.13 | Empty/Neo4j-down error paths | Code | [ ] | With Art 4 |
| 02.14 | Search rate limiting verification | Code | [ ] | |
| 02.15 | CHANGELOG.md Keep-a-Changelog | Content | [ ] | |
| 02.16 | CONTRIBUTING.md with issue SLA | Content | [ ] | |
| 02.17 | Release process docs (semver 0.x) | Content | [ ] | |
| 02.18 | pre-commit config (optional hygiene) | Config | [ ] | |
| 02.19 | Docker prod password warnings | Content | [ ] | |

---

## Artifact 03 — UI Design

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 03.01 | Hero GIF/MP4 or high-quality visual | Content | [ ] | SVG sequence if runtime hard |
| 03.02 | 3 still screenshots / diagrams | Content | [ ] | |
| 03.03 | README visual section above fold | Content | [ ] | |
| 03.04 | Empty-state CTA with commands | Code | [ ] | |
| 03.05 | Legend component in-app + README | Code | [ ] | |
| 03.06 | Contrast improvements for edges/text | Code | [ ] | |
| 03.07 | Desktop recommended note | Content | [ ] | |
| 03.08 | NODE_COLORS single source of truth | Code | [ ] | |
| 03.09 | docs/UI.md design tokens | Content | [ ] | |
| 03.10 | Expand hint in UI | Code | [ ] | |
| 03.11 | Social/OG image asset | Content | [ ] | |
| 03.12 | Keyboard nav | Deferred | [-] | Post-launch EDGE |
| 03.13 | Density modes | Deferred | [-] | Post-launch |

---

## Artifact 04 — UX / User Workflow

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 04.01 | Rewrite Quick Start ≤4 steps Compose-first | Content | [ ] | |
| 04.02 | examples/demo_pkg sample project | Code | [ ] | |
| 04.03 | scripts/first_run.sh + Makefile demo | Code | [ ] | |
| 04.04 | Empty state commands | Code | [ ] | Dup 03.04 |
| 04.05 | Double-click expand hint | Code | [ ] | Dup 03.10 |
| 04.06 | Health-aware UI (Neo4j disconnected) | Code | [ ] | |
| 04.07 | Ports/credentials table in docs | Content | [ ] | |
| 04.08 | Align Node version (20+) | Content | [ ] | |
| 04.09 | Show HN fastest path (draft) | Content | [ ] | Art 6 |
| 04.10 | Hosted public demo | Deferred | [-] | Needs auth design + human |
| 04.11 | One-binary distribution | Deferred | [-] | Strategic L |

---

## Artifact 05 — SEO

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 05.01 | GitHub description/topics | Config | [ ] | Dup 01.04/01.05 |
| 05.02 | README SEO H2 structure | Content | [ ] | |
| 05.03 | Fix your-org links | Content | [ ] | |
| 05.04 | llms.txt at repo root | Content | [ ] | |
| 05.05 | Name collision research note | Content | [ ] | |
| 05.06 | Awesome-list PR drafts (not submit without H3) | Content | [ ] | |
| 05.07 | Hosted docs site | Deferred | [-] | Post traffic |
| 05.08 | Social preview image | Content | [ ] | 03.11 |

---

## Artifact 06 — Marketing

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 06.01 | docs/launch/SHOW_HN.md draft | Content | [ ] | No publish |
| 06.02 | docs/launch/LIMITATIONS.md | Content | [ ] | |
| 06.03 | docs/launch/X_THREAD.md | Content | [ ] | |
| 06.04 | docs/launch/REDDIT_DRAFTS.md | Content | [ ] | |
| 06.05 | Content calendar outline | Content | [ ] | |
| 06.06 | Execute Show HN | Process | [-] | Needs H3/H6 |
| 06.07 | Architecture in Graph posts | Deferred | [-] | Post-launch cadence |

---

## Artifact 07 — Pre-Launch Checklist

**File status:** [ ] not complete  

Items largely covered by 01–06; track exit criteria here.

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 07.01 | Phase A exit criteria met | Process | [ ] | Checklist verification |
| 07.02 | Phase B exit criteria met | Process | [ ] | |
| 07.03 | Phase C exit criteria met | Process | [ ] | |
| 07.04 | Phase D assets (release notes draft, not tag push) | Content | [ ] | Tag needs human |
| 07.05 | docs/launch/PRE_LAUNCH_EXIT.md status | Content | [ ] | |

---

## Artifact 08 — Launch Day

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 08.01 | docs/launch/LAUNCH_DAY_RUNBOOK.md | Content | [ ] | From audit |
| 08.02 | Prepared HN reply for issue count | Content | [ ] | |
| 08.03 | Execute launch | Process | [-] | H3/H6 |

---

## Artifact 09 — Post-Launch

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 09.01 | CONTRIBUTING.md (SLA) | Content | [ ] | Dup 02.16 |
| 09.02 | CODE_OF_CONDUCT.md | Content | [ ] | Contributor Covenant |
| 09.03 | docs/POST_LAUNCH_CADENCE.md | Content | [ ] | |
| 09.04 | Execute post-launch activities | Process | [-] | After launch |

---

## Artifact 10 — Monetization

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 10.01 | LICENSE (Stage 0) | Content | [ ] | Dup 02.02 |
| 10.02 | docs/MONETIZATION_STAGE0.md | Content | [ ] | Explicit no-pay wall |
| 10.03 | FUNDING.yml | Process | [-] | H1 optional |
| 10.04 | Cloud/enterprise | Deferred | [-] | After gates |

---

## Artifact 11 — Analytics & Metrics

**File status:** [ ] not complete

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 11.01 | docs/metrics-log.md template + baseline row | Content | [ ] | |
| 11.02 | docs/ISSUE_LABELS.md for setup/bug/etc | Content | [ ] | |
| 11.03 | Telemetry default off (no code for v0.1) | Process | [-] | Document decision |
| 11.04 | Opt-in CLI telemetry | Deferred | [-] | Day 30 decision |

---

## Artifact 12 — Risk Register

**File status:** [ ] not complete  

Mitigations map to items above; residual:

| ID | Item | Type | Status | Notes |
|----|------|------|--------|-------|
| 12.01 | docs/BUS_FACTOR.md | Content | [ ] | |
| 12.02 | API local-only warning in DEPLOYMENT | Content | [ ] | R12 |
| 12.03 | Parse path enforcement tests | Code | [ ] | R14 |
| 12.04 | Prod compose password warning | Content | [ ] | R13 |

---

## Discovered During Implementation

(none yet)

---

## Commit traceability convention

`[audit:NN-slug] short description`
