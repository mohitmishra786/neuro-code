# Artifact 5: SEO & Organic Discoverability Audit

**Date of audit:** July 2026  
**Research:** GitHub OSS SEO practices, Awesome lists, llms.txt / GEO guides (2025–2026)

---

## Current State

| Asset | Status | Impact |
|-------|--------|--------|
| GitHub repository description | **null** | No keyword surface in search/social cards |
| GitHub topics | **[]** | Invisible to topic browse / related repos |
| Homepage URL | **null** | No funnel off GitHub |
| GitHub Pages | **false** | No free docs host |
| README keywords | Generic title; no H2 keyword sections | Weak for Google + GitHub search |
| Docs | Plain markdown in `docs/` | Not indexed as a site; no meta titles |
| LICENSE file | Missing | Trust/SEO secondary; corporate filters |
| Social preview image | Default / none custom | Weak shares |
| `llms.txt` | Absent | Misses 2026 AI-agent + AI-search discovery layer |
| Backlinks | Effectively none at 0 stars | Cold start |
| Package indexes | Not on PyPI as installable product CLI (broken entrypoint) | No `pip install neurocode` discovery |

GitHub metadata (July 2026 API): `description: null`, `topics: []`, `homepage: null`, `has_pages: false`.

### What works for OSS discoverability in 2026 (verified themes)

1. **GitHub topics + description** — still primary in-ecosystem discovery; empty topics is free lost inventory (GitHub product behavior; standard OSS growth guides).
2. **README as landing page** — first screen must answer what/why/screenshot; keyword H2s (“Python codebase visualization”) help both humans and crawlers.
3. **Awesome-list backlinks** — remain a durable referral + PageRank-ish signal for niche tools.
4. **Show HN / Reddit / Lobsters** — burst indexing; Google often ranks the discussion thread.
5. **Hosted docs** (MkDocs, Docusaurus, Mintlify) — separate domain/subpath with titles, sitemap, canonical URLs.
6. **`llms.txt`** — 2025–2026 adoption for AI answer engines and coding agents (Cursor, etc. fetch docs maps). Guides from limy.ai (May 2026), llmpulse (Jul 2026), Search Engine Land (2025), Answer.ai origin. Not a traditional Google ranking factor (SearchSignal Jan 2026 caution), but relevant for **AI-mediated discovery** of devtools.

### Keyword targets (hypotheses — validate with tools)

**Do not invent volumes.** Use Google Keyword Planner, Ahrefs, or even GitHub search result counts as proxies.

| Candidate query | Intent | Fit | How to validate |
|-----------------|--------|-----|-----------------|
| `python codebase visualization` | Tool seeking | High | Search volume tool + GitHub code search |
| `code knowledge graph python` | Niche / Neo4j curious | High | Same |
| `Sourcetrail alternative` | Replacement | High (CodeLayers blog notes this demand, Feb 2026) | Rank track |
| `neo4j code analysis` | Graph DB + code | Medium | Same |
| `interactive code graph explorer` | Category | Medium | Same |
| `tree-sitter visualization` | Builder | Lower volume, high relevance | Same |
| `hierarchical code map` | Feature | Medium | Same |

**Brand:** `NeuroCode` / `neuro-code` — check collisions (neuro/ML products may compete for the name in Google). **Unverified:** trademark/name collision analysis not performed in this audit — do a quick search before heavy branding spend.

---

## Gaps / Risks

1. Zero GitHub SEO surface area (description/topics/website).
2. Docs not a site → no sitemap, no meta description, no long-tail pages.
3. No Awesome-list presence.
4. No `llms.txt` for AI-era discovery.
5. Placeholder `your-org` URLs harm crawl consistency.
6. Name ambiguity risk with other “Neuro*” products (needs check).

---

## Checklist

### Pre-Launch

- [ ] **Set GitHub About description** (Artifact 1 one-liner). (Effort: **S**). *Verify:* appears under repo name.
- [ ] **Add topics:** `python`, `code-visualization`, `neo4j`, `tree-sitter`, `developer-tools`, `fastapi`, `react`, `ast`, `knowledge-graph`, `code-intelligence`. (Effort: **S**)
- [ ] **README SEO structure:** H1 brand; first paragraph with primary keyword; H2 “Python codebase visualization”; H2 “Features”; H2 “Quick Start”; alt text on images. (Effort: **S**)
- [ ] **Fix all `your-org` links** for canonical URL consistency. (Effort: **S**)
- [ ] **Custom social preview** (repo Open Graph image settings). (Effort: **S**)
- [ ] **Validate keywords** in Ahrefs/GKP; drop any with zero realistic intent. (Effort: **S**)
- [ ] **Name collision search** for “NeuroCode” software. (Effort: **S**)

### Launch

- [ ] Submit PRs to curated lists (research-backed candidates below). (Effort: **M** each; expect review delays)
  - [ ] [vinta/awesome-python](https://github.com/vinta/awesome-python) — under Science/Data or appropriate “Code Analysis” if section fits; **only if maintainers’ contribution rules allow** (very selective).
  - [ ] [ml-tooling/best-of-python-dev](https://github.com/ml-tooling/best-of-python-dev) — ranked Python dev tools list.
  - [ ] Awesome lists for Neo4j / graph visualization (search `awesome-neo4j`, `awesome-graph`).
  - [ ] `awesome-tree-sitter` / static analysis lists if active.
- [ ] Cross-post launch writeup to **dev.to** with canonical link to GitHub (indexing + long-tail). (Effort: **S**)
- [ ] Ensure Show HN title contains plain language keywords, not only brand. (Effort: **S**)

### Post-Launch

- [ ] **Host docs site** (GitHub Pages + MkDocs Material or Docusaurus) with:
  - title templates, meta descriptions, sitemap.xml  
  - pages: Getting Started, Architecture, API, Comparison vs Sourcetrail/Sourcegraph  
  (Effort: **M–L**). *Verify:* Google Search Console property once domain exists.
- [ ] **Add `/llms.txt`** on docs host summarizing project + linking key markdown. (Effort: **S**). *Source:* llms.txt 2026 guides; useful for agents more than classic SEO.
- [ ] **Backlink plan (realistic):**  
  1. Awesome-list PRs  
  2. “Visualized X with NeuroCode” blog posts (Artifact 6)  
  3. Neo4j community blog / Discord share  
  4. HN/Reddit residual links  
  Avoid paid link schemes.
- [ ] Track GitHub **Traffic** Insights (clones, views, referrers) weekly. (Effort: **S**)

### Sample `llms.txt` outline (for future docs host)

```text
# NeuroCode
> Self-hosted hierarchical knowledge graph for Python codebases (Tree-sitter → Neo4j → React).

## Docs
- [Getting Started](https://example.com/docs/start)
- [Architecture](https://example.com/docs/architecture)
- [API](https://example.com/docs/api)

## Optional
- [GitHub Repository](https://github.com/mohitmishra786/neuro-code)
```
