# Artifact 11: Analytics, Metrics & Instrumentation Audit

**Date of audit:** July 2026  
**Repo scan:** no product analytics SDKs found (no PostHog, Plausible, GA, Sentry, Mixpanel in app code; `rg` for analytics terms only hit unrelated `queries.py` noise)

---

## Current State — what is measurable today

| Data source | Available? | Notes |
|-------------|------------|-------|
| GitHub stars/forks | Yes | Currently 0/0 |
| GitHub Traffic Insights (views, clones, referrers) | Yes for maintainers | 14-day windows; must check manually |
| GitHub Issues response time | Manual | No SLA tooling |
| Release download counts | N/A | No releases yet |
| Docs site analytics | **No docs site** | |
| Product analytics (UI) | **None** | |
| CLI/parser telemetry | **None** | |
| Backend metrics (Prometheus etc.) | **None found** | |
| Error tracking | **None** (structlog only) | |
| CI test pass rate | **CI present** (`.github/workflows/ci.yml` + security/lint workflows); track pass rate via Actions history | |

**Bottom line:** You cannot currently distinguish “nobody cares” from “nobody can install.” That is an existential instrumentation gap for a pre-launch tool.

---

## North Star metric candidates

Pick **one** primary; others are supporting.

| Candidate | Definition | Why | How to instrument |
|-----------|------------|-----|-------------------|
| **A. Weekly Active Repos Parsed (WARP)** | Distinct repos successfully parsed per week (non-maintainer if possible) | Closest to “tool is used” | Opt-in CLI ping **or** self-report survey; hard without telemetry |
| **B. Setup completion rate** | % of clones that reach first graph | Diagnoses activation | Proxy: demo script success counter opt-in; or user study |
| **C. README → Star conversion** | stars / unique repo visitors | Top-of-funnel message quality | GitHub Traffic views vs stars |
| **D. Weekly clones** | Clones per week | Interest intensity | GitHub Insights |
| **E. Expand actions / session** | Depth of exploration | Value moment | Frontend analytics (needs install) |

**Recommendation for next 90 days:**

- **Primary proxy North Star:** **Weekly clones + setup-related issue rate** (inverse).  
- **Aspirational North Star (after opt-in telemetry):** **WARP**.  
- **Do not use stars alone** as North Star (vanity; HN spikes mislead).

---

## Minimum instrumentation before launch

### Must-have (no privacy drama)

- [ ] **Weekly GitHub Insights log** (spreadsheet or `docs/metrics-log.md`): date, views, unique visitors, clones, top referrers, stars, open issues, median response hours. (Effort: **S**)
- [ ] **Issue labels** for funnel diagnosis: `setup`, `bug`, `enhancement`, `question`. (Effort: **S**)
- [ ] **CI status** as a reliability metric once CI exists. (Effort: **S** with Artifact 2)
- [ ] **Release tags** so adoption can attach to versions. (Effort: **S**)

### Should-have (low friction)

- [ ] **Docs/README “Was this successful?”** discussion poll post-launch. (Effort: **S**)
- [ ] **Sentry or similar on backend** only if you run a hosted demo (PII careful). (Effort: **M**)
- [ ] **Plausible/Umami on docs site** once hosted (cookie-lite). (Effort: **S**)

### Opt-in usage ping (ethical design)

If implementing CLI telemetry:

```
neurocode parse ... 
# prints: "Send anonymous success metric? [y/N]" 
# or env NEUROCODE_TELEMETRY=1
```

Payload suggestion: timestamp, neurocode version, python version, file_count_bucket (1–10, 11–100, 101–1000, 1000+), success bool, **no paths, no code, no usernames**.

- [ ] Document in README + SECURITY/privacy blurb. (Effort: **M**)
- [ ] Default **off**. (Effort: **S**)

**Verify:** event count in a simple endpoint or GitHub-discussion bot; zero PII in logs review.

### Frontend analytics

Defer until hosted demo; local OSS tools often skip. If added:

- [ ] Page load success, first expand, search used — **anonymous, opt-in**. (Effort: **M**)

---

## Metric definitions & instrumentation map

| Metric | Pre-launch | Launch week | Post-launch ongoing |
|--------|------------|-------------|---------------------|
| Stars / forks | Snapshot | Daily | Weekly |
| Views / clones | Baseline week | Daily | Weekly |
| Referrers | — | Daily | Weekly |
| Open issues + `setup` count | After triage | Daily | Weekly |
| Time to first maintainer reply | — | Track | Weekly median |
| CI green rate | After CI | — | Weekly |
| WARP (opt-in) | Design only | Optional | Weekly |
| Hosted demo uniques | If exists | Daily | Weekly |

---

## Gaps / Risks

1. **Without setup proxies, product decisions are guesswork.**  
2. Telemetry backlash if default-on—keep opt-in.  
3. GitHub Insights are short-retention—log externally.  
4. HN spike will dominate week 1; judge from **week 3+**.

---

## Checklist

### Pre-Launch
- [ ] Create `docs/metrics-log.md` template
- [ ] Record 1 week pre-launch baseline (even if zeros)
- [ ] Standardize issue labels including `setup`
- [ ] Decide: telemetry yes/no for v0.1 (recommend **no** code, **yes** process metrics)
- [ ] If hosted demo planned: privacy policy + Plausible + error tracking

### Launch
- [ ] Daily metrics capture for 7 days
- [ ] Tag issues from HN users
- [ ] Note star count at T+0, T+24h, T+7d (context only)

### Post-Launch
- [ ] Weekly metrics review (15 min) tied to Artifact 9 iteration loop
- [ ] At day 30: choose whether to implement opt-in CLI ping
- [ ] At day 90: evaluate if WARP is knowable; else run n=10 user interviews

### What can wait
- [ ] Full product analytics suite  
- [ ] Funnel heatmaps  
- [ ] Revenue metrics (Artifact 10 Stage 0)  
- [ ] Multi-dimensional A/B testing  
