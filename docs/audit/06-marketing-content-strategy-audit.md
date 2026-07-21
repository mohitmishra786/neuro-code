# Artifact 6: Marketing & Content Strategy Audit

**Date of audit:** July 2026  
**Context:** Pre-launch OSS Python developer tool, 0 stars, technical audience

---

## Current State

- **No marketing assets:** no blog, no X/Twitter presence documented in repo, no newsletter, no demo video, no Product Hunt listing observed.
- **No launch post drafts** in repository.
- **No community channel** (Discussions disabled state not checked as primary; GitHub Discussions field available via API was not enabled as a content hub in-repo).
- **Content inventory today:** README + 3 docs markdown files only.

This is a pure cold-start launch problem.

---

## Channel research (2026, search-verified)

| Channel | Fit for NeuroCode | What’s working / saturated | Sources |
|---------|-------------------|----------------------------|---------|
| **Hacker News Show HN** | **Primary** — technical OSS, local tools, graph/infra | Still best for eng tools; success depends on demo + first 60–90 min replies. Timing consensus 2025–26: **Tue–Thu ~8–10am ET** (some analyses say 8–11 UTC for points). Avoid weekend-only reliance. | flowjam HN playbook Nov 2025; okara.ai Jul 2026; smollaunch PH vs HN; myriade / Reddit 1200-launch scrapes |
| **Product Hunt** | Secondary | Better for broader SaaS; HN often wins pure devtools. Launch **Tue–Thu 12:01am PT** conventional. | smollaunch 2026 comparison |
| **Reddit** | High for niche | `r/Python`, `r/programming`, `r/neo4j`, `r/selfhosted` — value-first posts; pure promo banned often. | Standard sub rules (verify before post) |
| **Lobsters** | Medium | Smaller, high-signal; invite culture; quality bar. | Community norms |
| **dev.to / Hashnode** | Medium | Evergreen SEO; cross-post Show HN writeup | Common 2026 OSS practice |
| **X/Twitter** | Medium if consistent | Dev graph demos as short video; algorithmic video favor | Platform-dependent |
| **YouTube** | High leverage, high effort | “I visualized Django/Flask/CPython with X” walkthroughs work for this category | Category pattern (CodeLayers-style blast radius series) |
| **Neo4j community** | High adjacency | Official blog / Discord / community.neo4j.com | Natural distribution for Neo4j-backed tools |
| **VS Code Marketplace** | N/A until extension exists | Lowest friction installs dominate mindshare | Marketplace competitors 2026 |

**Honest note:** Without a **clickable demo or strong GIF**, Show HN conversion collapses. Marketing is blocked on Artifacts 3–4 deliverables.

---

## Positioning-aligned narrative

From Artifact 1 persona:

> “I joined a Python monorepo and spent a week reconstructing architecture from imports. NeuroCode gives me a hierarchical map in minutes—on my machine.”

Avoid: AI hype, unmeasured 100k-file claims, Sigma/WebGL.

---

## Content calendar concepts (NeuroCode-specific)

### Recurring format: “Architecture in Graph”

Each episode: pick a popular OSS Python repo → parse → 3–5 screenshots/GIF → 400–800 words on surprising structure (god modules, inheritance depth, call hubs).

| # | Suggested subject | Angle |
|---|-------------------|-------|
| 1 | Flask or FastAPI itself | “The framework’s own package graph” |
| 2 | Django | Apps vs models density |
| 3 | Requests / httpx | Small-codebase clarity demo |
| 4 | Home Assistant or Airflow (large) | Stress narrative—only after perf honesty |
| 5 | Your own neuro-code repo | Dogfood transparency |

### Other content types

- **Setup screencast** (3 min): Docker → graph  
- **Comparison post:** “Sourcetrail is gone—what’s left for Python?” (careful, factual)  
- **Technical deep dive:** Merkle + Tree-sitter 4-pass (for HN audience)  
- **Neo4j Cypher recipes** over the code graph (attract graph DB audience)

Cadence proposal post-launch: **1 substantial piece / week** for 8 weeks, then biweekly if solo.

---

## Show HN draft outline

**Title pattern (factual, tryable):**  
`Show HN: NeuroCode – hierarchical knowledge graph for local Python codebases`

**Body structure:**

1. One-sentence problem  
2. What it does (parse → Neo4j → expand packages/classes)  
3. GIF / screenshot  
4. Why local / self-hosted  
5. Stack (honest: Tree-sitter, Neo4j, ReactFlow)  
6. Limits (Python only, Docker, early 0.1)  
7. Fastest path commands  
8. Ask for feedback on X  

**First comment (prepared):** architecture link, demo GIF, known issues, maintainer availability window.

**Timing (2026 consensus):** Tuesday–Thursday, ~8–10am America/New_York; block **2 hours** for replies. Sources: flowjam 2025 playbook; okara 2026; multiple HN timing posts.

---

## Gaps / Risks

1. Zero channel presence → all eggs in one Show HN basket without warm-up is riskier.
2. 123 open issues visible during launch scrutiny (Artifact 2) — marketing must not promise polished enterprise.
3. Name “NeuroCode” may underperform generic keyword titles on HN; A/B mentally with descriptive titles.
4. No email waitlist infrastructure — optional; for OSS, GitHub star is the waitlist.

---

## Checklist

### Pre-Launch (teaser / readiness)

- [ ] Ship GIF + 4-step setup (Artifacts 3–4) before any teaser. (Effort: **M**, blocking)
- [ ] Write Show HN body in a gist; dry-run with 2 engineer friends. (Effort: **S**)
- [ ] Optional: soft teaser on X/LinkedIn with GIF only, link “repo soon” or private. (Effort: **S**)
- [ ] Create GitHub Discussions or pin “Announce” issue for launch Q&A. (Effort: **S**)
- [ ] Prepare **known limitations** list to paste under criticism. (Effort: **S**)
- [ ] Reduce open issues optics (&lt;25) before launch day (Artifact 2). (Effort: **M**)
- [ ] Tag `v0.1.0` release with notes. (Effort: **S**)
- [ ] Optional Product Hunt draft + maker account ready. (Effort: **S**)
- [ ] Identify 3 subreddits + read rules; draft value-first posts (not cross-spam). (Effort: **S**)

### Launch

- [ ] **T-0:** Show HN at chosen window; stay online 2h. (Effort: **S** + calendar)
- [ ] **T+1h:** post to `r/Python` if HN is healthy (or wait to avoid brigading accusations—prefer sequential day 2). (Effort: **S**)
- [ ] **T+0:** share in Neo4j community channels with technical angle. (Effort: **S**)
- [ ] **T+0:** short X thread with GIF. (Effort: **S**)
- [ ] **T+24h:** Product Hunt if desired (not mandatory for OSS). (Effort: **S**)
- [ ] **T+48h:** dev.to long-form mirror. (Effort: **S**)
- [ ] Monitor issues for setup bugs; hotfix same day (Artifact 8). (Effort: **M**)

### Post-Launch

- [ ] Publish “Architecture in Graph” #1 within 7 days while attention residual. (Effort: **M**)
- [ ] Cadence: 1 post/week × 8 weeks. (Effort: **L** cumulative)
- [ ] Collect testimonials/screenshots from users (ask in issues). (Effort: **S**)
- [ ] Choose **one** community home (GitHub Discussions recommended for solo OSS). (Effort: **S**)
- [ ] Re-launch opportunities: v0.2 multi-feature, or “now with one-command demo.” (Effort: **M** each)

### What not to do

- Do not buy engagement on HN/PH.  
- Do not claim AI features NeuroCode doesn’t have.  
- Do not mass-post identical links to every subreddit in one hour.
