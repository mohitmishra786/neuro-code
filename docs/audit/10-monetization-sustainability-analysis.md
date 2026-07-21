# Artifact 10: Monetization & Sustainability Analysis

**Date of audit:** July 2026  
**Research:** OSS monetization models 2025–2026 (GitHub Sponsors pages, open-core/SaaS guides, lemonade-stand taxonomy, Medium/LinkedIn 2026 OSS revenue posts)

---

## Current State

- **License claim:** MIT (README + `pyproject.toml`); **LICENSE file missing** → corporate buyers cannot diligence easily.
- **Distribution:** free clone; no paid tier; no Sponsors button verified in repo funding files (`FUNDING.yml` not present in tree).
- **Architecture fit for paid hosting:** FastAPI + Neo4j + React is **naturally multi-tenant-awkward** (Neo4j per customer or noisy multi-db) but **naturally suited to “we host your graph”** single-tenant containers.
- **Traction:** 0 stars, 0 forks, no customers, no waitlist.
- **Cost base today:** maintainer time + optional cloud if demo hosted.

---

## Models that work for similar devtools (2026)

| Model | How it works | Fit for NeuroCode | Notes / sources |
|-------|--------------|-------------------|-----------------|
| **Adoption first, monetize later** | Grow OSS, defer revenue | **Best now** | Standard for 0-traction tools |
| **GitHub Sponsors / donations** | Tips from users/cos | Weak until useful & visible | GitHub Sponsors program; low ARPU |
| **Hosted SaaS** | Pay for managed instance | **Strong architectural fit later** | lemonade-stand SaaS section; open-source monetization roundups 2026 |
| **Open core** | OSS explore; paid SSO, RBAC, scale, multi-repo | Medium | Common 2026 pattern (PowerUpSkills Medium 2026) |
| **Enterprise support / license** | Annual support on self-host | Medium after logos | Needs sales time |
| **Sponsorware** | Features free after $ goal | Poor fit for infra graph | Niche |
| **AI upsell (Sourcegraph Cody-style)** | Chat over code graph | Adjacent but **not in product today** | Would be net-new R&D |
| **Marketplace extension paid** | N/A without extension | Future | |

CodeLayers’ 2026 public pricing example (free public / Pro ~$8/mo private) shows the market accepts **low-price Pro** for visualization—but they already have product polish + multi-lang + mobile.

---

## Honest recommendation

### Monetization is **premature** as a primary goal at 0 stars

**Reasoning:**

1. **No demand signal.** Revenue models need users who already rely on the tool. Sponsors at 0 stars is cosplay.
2. **Activation is broken.** Multi-service setup means even free users churn before value—paid conversion would be near zero.
3. **Category competition** includes free explore URLs and free VS Code extensions. Price is not the barrier; **time-to-graph** is.
4. **Single maintainer** cannot support enterprise SLAs yet.
5. **MIT without LICENSE file** blocks even the early design-partner conversations.

**Priority order:**  
**Adoption (Artifacts 3–7) → reliability (2, 9) → optional Sponsors → hosted beta → open-core enterprise.**

---

## Staged plan (when—not if—adoption appears)

### Stage 0 — Now through first 500 stars / 50 weekly clones (whichever first)

**Monetization checklist: none required.**

Do:

- [ ] Add proper `LICENSE`
- [ ] Optional `FUNDING.yml` pointing to GitHub Sponsors **after** v0.1 works (vanity is fine; don’t expect income)
- [ ] Track costs of any demo hosting

**Gate to Stage 1:** repeated external usage (issues from strangers, third-party blog posts, or organic clones &gt;100/week for 4 weeks). **Unverified until metrics exist.**

### Stage 1 — Sustainability lite

- [ ] GitHub Sponsors tiers ($5 / $20 / $100 “company”) with honest perks (priority triage, logo in README). (Effort: **S**)
- [ ] “Buy me coffee” only if Sponsors unavailable. (Effort: **S**)

**Verify:** any recurring sponsor count &gt;0 after 90 days of real use—not launch week spikes.

### Stage 2 — Hosted tier (“NeuroCode Cloud”)

Fit: docker-compose already defines three services → package as single-tenant deploy per user/org.

- [ ] Security model: auth, private networking, no arbitrary path parse from internet. (Effort: **L**)
- [ ] Pricing sketch (illustrative only): free OSS self-host; Cloud $20–40/user/mo or $99/workspace flat—**validate with 5 interviews**, do not ship prices from this doc. (Effort: **M**)
- [ ] Free public demo graphs (read-only famous repos) as funnel. (Effort: **L**)

**Verify:** paid conversion rate; churn; support load hours/week.

### Stage 3 — Open core / enterprise

Paid features that don’t poison OSS core:

- SSO/SAML, RBAC, audit log  
- Multi-repo org workspace  
- SLAs + support  
- Air-gapped install assistance  
- Optional: SOC2-oriented deployment guides  

Keep parser + basic UI MIT.

**Verify:** ≥1 design partner LOI before building SSO.

---

## What not to do early

- Don’t dual-license surprise after people adopt MIT.  
- Don’t gate core hierarchical graph behind paywall if marketing said OSS.  
- Don’t sell “AI” that doesn’t exist.  
- Don’t take enterprise contracts you can’t staff.

---

## Gaps / Risks

| Risk | Note |
|------|------|
| Neo4j ops cost | Hosted margin depends on memory-heavy graphs |
| Commoditization | VS Code free tools may cap WTP for simple maps |
| Support burden | Graph products attract “parse my monorepo” tickets |

---

## Checklist

### Pre-Launch / Launch
- [ ] **No paid product work required**
- [ ] LICENSE file for future commercial clarity
- [ ] Do not promise Cloud on Show HN unless build date exists

### Post-Launch (only after Stage 0 gate)
- [ ] FUNDING.yml / Sponsors
- [ ] 5 customer discovery calls before Cloud
- [ ] Security design for hosted parse
- [ ] Written pricing hypothesis + kill criteria

### Explicit statement

**Monetization checklist for the next 90 days: effectively none beyond legal hygiene (LICENSE) and optional Sponsors plumbing.** The highest-ROI “sustainability” investment is **reducing time-to-first-graph** so the project earns the right to charge later.
