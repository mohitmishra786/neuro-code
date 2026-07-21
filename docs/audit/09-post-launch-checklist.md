# Artifact 9: Post-Launch Checklist

**Date of audit:** July 2026  
**Horizon:** 30 / 60 / 90 days after Show HN (or first public announcement)  
**Ties to:** Artifact 11 metrics, Artifact 2 maintenance cadence, Artifact 6 content

---

## Current State

Post-launch operations are **undefined** in-repo: no CONTRIBUTING.md, no CODE_OF_CONDUCT, no release cadence doc, no community SLA, no metrics dashboard. Default path for a solo maintainer is silence → perceived abandonment.

---

## Gaps / Risks

- Star spike without response → toxic issue tracker.
- No release rhythm → Dependabot-only PR history looks dead.
- Content vacuum after launch week → zero residual SEO.
- Scope creep from re-opened agent issues + feature asks.

---

## 30-day checklist (stabilize)

### Community & issues
- [ ] Publish `CONTRIBUTING.md` (setup, PR rules, “how we triage”). (Effort: **S**)
- [ ] Issue SLA: acknowledge within **72 hours** (document it). (Effort: **S**)
- [ ] Weekly triage session (30 min): label, close dupes, milestone. (Effort: **S**/week)
- [ ] Keep `launch-day` / `setup` issues at zero open &gt;7 days. (Effort: **M**)
- [ ] Add 2–3 real `good first issue` items with acceptance criteria—or none (don’t fake). (Effort: **S**)

### Product
- [ ] Ship **v0.1.x** patches only for user-reported setup/crash bugs. (Effort: **M**)
- [ ] Freeze agent-style issue reopening. (Effort: **S** policy)
- [ ] Collect qualitative feedback (5 conversations). (Effort: **M**)

### Content & distribution
- [ ] Publish “Architecture in Graph” #1 within 7 days of launch. (Effort: **M**)
- [ ] Two more posts by day 30. (Effort: **M**)
- [ ] Submit 1–2 Awesome-list PRs if not done. (Effort: **S–M**)

### Metrics (Artifact 11)
- [ ] Weekly log: stars, forks, clones, unique visitors, open issues, median first-response hours. (Effort: **S**)
- [ ] Note top referrers from GitHub Traffic. (Effort: **S**)

**30-day success signals (directional, not vanity-only):**  
clones trending; &lt;10% of issues are “can’t install”; ≥1 external PR or substantive issue from non-maintainer.

---

## 60-day checklist (improve activation)

### Product bets (pick 1–2, not all)
- [ ] Hosted read-only demo **or** dramatically better one-command path (whichever feedback demands). (Effort: **L** or **M**)
- [ ] Wire WebSocket updates into UI if users expect live reload. (Effort: **M**)
- [ ] Search quality fix if search is top complaint. (Effort: **M**)
- [ ] Export (GraphML / Cypher dump) if Neo4j power users ask. (Effort: **M**)

### Engineering hygiene
- [ ] Dependency upgrades batch (FastAPI, Neo4j driver/image). (Effort: **M**)
- [ ] Coverage report published once; set a modest floor later. (Effort: **M**)
- [ ] CHANGELOG kept current. (Effort: **S**)

### Content
- [ ] Posts #4–5; one YouTube/screencast if energy allows. (Effort: **M–L**)
- [ ] Update comparison table from real user objections. (Effort: **S**)

### Community
- [ ] Decide Discussions vs Discord (recommend **Discussions only** until &gt;500 stars). (Effort: **S**)
- [ ] Highlight contributors in release notes. (Effort: **S**)

---

## 90-day checklist (direction)

- [ ] **Strategy review:** double down on Python hierarchical explorer vs pivot toward AI/MCP/multi-lang (Artifact 1). (Effort: **M** meeting-with-self, written)
- [ ] Tag **v0.2.0** only if user-visible value landed (not just refactors). (Effort: **M–L**)
- [ ] Revisit monetization gate (Artifact 10): only if adoption thresholds met. (Effort: **S**)
- [ ] React 19 migration evaluation. (Effort: **M**)
- [ ] Docs site (MkDocs/Docusaurus) if traffic justifies. (Effort: **M–L**)
- [ ] Write public 90-day retrospective (builds trust). (Effort: **S**)

**90-day North Star check:** Is weekly active parsing happening outside the maintainer’s machine? If unknown, instrument (Artifact 11). If no, activation still broken—do not expand scope.

---

## Recurring cadences (copy into calendar)

| Cadence | Activity |
|---------|----------|
| **Daily (week 1 only)** | Issue inbox zero for setup bugs |
| **Twice weekly (days 8–30)** | Issue triage + hotfix if needed |
| **Weekly (ongoing)** | Metrics log + 30m triage |
| **Biweekly** | Release if changes exist; else “no-release” note in Discussion |
| **Weekly ×8** | Content piece (then reassess) |
| **Monthly** | Dependency review; roadmap reorder |
| **Quarterly** | Major version / platform bet |

---

## Iteration loop (ties to Artifact 11)

```
Measure → top drop-off (setup vs empty graph vs expand vs search)
   → ship one fix
   → announce in release + short post
   → re-measure clones and setup-issue rate
```

Do **not** use star count alone as the iteration driver.

---

## Post-Launch checklist (flat)

### Days 0–30
- [ ] CONTRIBUTING.md
- [ ] 72h acknowledge SLA documented
- [ ] Weekly metrics log started
- [ ] Setup issue backlog clear
- [ ] 3 content pieces
- [ ] Patch releases as needed

### Days 31–60
- [ ] One major activation improvement shipped
- [ ] Deps refreshed
- [ ] Content continues
- [ ] Community home chosen

### Days 61–90
- [ ] Strategy written decision
- [ ] v0.2 only if earned
- [ ] Monetization reassess
- [ ] Public retrospective
