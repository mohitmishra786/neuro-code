# Artifact 8: Launch Day Checklist

**Date of audit:** July 2026  
**Assumes:** Artifact 7 Phase D complete  
**Recommended window:** Tuesday–Thursday, **8:00–10:00 America/New_York** (2025–2026 HN timing consensus)

---

## Current State

No prior public launch. Single maintainer. One open Dependabot PR. Large historical issue list (must already be triaged). No analytics beyond GitHub Insights.

---

## Gaps / Risks

- Traffic spike exposes setup friction and any demo-path bugs.
- 123 untriaged issues (if not cleaned) become the story.
- Solo maintainer burnout in first 4 hours if unprepared.
- Hostile or pedantic HN comments on performance claims / ReactFlow vs Sigma if not fixed.

---

## Hour-by-hour plan (example: Wednesday)

### T−24h to T−1h (day before / morning)

- [ ] Confirm `main` is green on CI
- [ ] Confirm `v0.1.0` tag matches what README documents
- [ ] Re-run `make demo` / first_run on a clean environment
- [ ] Disable or merge Dependabot PR noise if it confuses visitors
- [ ] Pin a GitHub Discussion or issue: “Launch day Q&A”
- [ ] Clear calendar **08:00–12:00 ET** for replies
- [ ] Drafts open in tabs: Show HN body, first comment, X thread, r/Python post (hold), Neo4j community post
- [ ] Hotfix branch strategy: fix on `main` via short-lived `hotfix/*`; no force-push to `main` mid-launch
- [ ] Snapshot open issue count (should be &lt;25)

### T−15m

- [ ] Final health check: local demo still works
- [ ] Copy final Show HN title/body to clipboard
- [ ] Open HN submit page; stay logged in

### T+0 (submit)

- [ ] Submit **Show HN** with link to GitHub repo (or docs if stronger)
- [ ] Immediately post **first comment**: GIF, fastest setup, limitations, “I’ll be here for questions”
- [ ] Star your own repo? **No** — irrelevant; do ensure you’re watching issues
- [ ] Enable notifications for issues + HN thread

### T+0 to T+30m (critical ranking window)

- [ ] Reply to **every** substantive comment (HN ranks engagement in early window)
- [ ] If setup bug reported: reproduce → hotfix → comment with commit hash
- [ ] Do **not** ask for upvotes
- [ ] Post short **X/Twitter** thread with GIF + repo link (after HN is live, so HN is canonical)
- [ ] Share in **Neo4j community** with technical framing (not “please upvote”)

### T+30m to T+2h

- [ ] Continue HN replies
- [ ] Monitor GitHub Issues for `setup` / crash reports; label `launch-day`
- [ ] If traffic is high and Neo4j demo is self-hosted only: keep pointing to local Docker path
- [ ] **Do not** post Reddit yet if HN is still climbing (avoid vote-ring suspicion); prefer T+4h or next day with unique commentary

### T+2h to T+6h

- [ ] Write brief launch retrospective notes (what broke, FAQs)
- [ ] Merge any critical hotfixes; cut `v0.1.1` if needed
- [ ] Optional: Product Hunt submit if assets ready (not required)
- [ ] Update README FAQ with top 3 questions from HN

### T+24h

- [ ] `r/Python` or `r/selfhosted` value post (different angle: “how the 4-pass parser works” + link)
- [ ] dev.to long-form if not done
- [ ] Review GitHub Traffic Insights (views, clones, referrers)
- [ ] Close or answer all launch-day issues

### T+48–72h

- [ ] Thank contributors; label `good first issue` if any real ones
- [ ] Publish content piece #1 schedule (Artifact 6)
- [ ] Decide whether second-wave channels are worth energy

---

## Channel order (recommended)

1. **Hacker News Show HN** (primary)  
2. **First comment assets** on HN  
3. **X/Twitter** (amplify, don’t lead if HN is the goal)  
4. **Neo4j community**  
5. **Reddit** (next day, unique post)  
6. **dev.to** (evergreen)  
7. **Product Hunt** (optional, separate day OK)

---

## Monitoring plan

| Signal | Where | Action threshold |
|--------|-------|------------------|
| HN rank / comments | HN item page | Reply all for 2h |
| New GitHub issues | Issues tab + email | Respond &lt;1h on launch day for setup bugs |
| Stars / forks | Repo header | Observe only; not a hotfix trigger |
| Clones / views | Insights → Traffic | Note referrers for post-mortem |
| CI failures | Actions | Block merges that break demo path |
| Dependabot noise | PRs | Ignore unless security critical |

**No APM/product analytics exist** (Artifact 11) — GitHub + HN are the instruments.

---

## 123-issue backlog visibility response plan

If someone says “why 123 open issues?”:

**Prepared reply:**  
“Most of those were auto-generated static analysis tickets from an internal agent pass (perf/style). Before launch we triaged to N real tracking issues; the rest were closed as not planned for v0.1. Please open a new issue with repro for anything user-facing.”

If triage was **not** done (should not launch):

- [ ] Emergency: bulk-close with template comment **before** or **immediately at** T+0 (better before).

---

## Rollback / hotfix readiness

| Scenario | Response |
|----------|----------|
| README wrong command | Commit fix to main within 15m; reply on HN with correction |
| Parse crash on demo package | Hotfix parser or swap demo package; tag v0.1.1 |
| Security report (path traversal, etc.) | Take parse endpoint offline guidance; disable public anything; acknowledge in SECURITY process |
| CI red from hurried fix | Revert via PR; do not leave main broken |
| Overwhelm | Post “queueing issues; prioritizing setup blockers”; don’t ghost |

**There is no production multi-tenant service to “roll back”** if product is local-only — the “rollback” is **git tag + README truthfulness**.

---

## Launch Day checklist (flat)

### Pre-flight
- [ ] CI green
- [ ] Demo path works
- [ ] Issue count acceptable
- [ ] v0.1.0 live
- [ ] Drafts ready
- [ ] 2h reply block free

### Execute
- [ ] Show HN submitted
- [ ] First comment posted
- [ ] X thread posted
- [ ] Neo4j community posted
- [ ] All early comments answered

### Stabilize
- [ ] Launch issues labeled
- [ ] Hotfixes shipped if needed
- [ ] FAQ updated
- [ ] T+24 Reddit/dev.to
- [ ] Metrics notes saved
