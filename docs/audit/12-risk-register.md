# Artifact 12: Risk Register

**Date of audit:** July 2026  
**Method:** consolidate risks from Artifacts 1–11; likelihood/impact as qualitative High/Med/Low for a pre-launch solo OSS project

**Scale:** Likelihood = chance of materializing in 90 days without mitigation. Impact = damage to adoption, trust, or ability to operate.

---

## Current State

Risk management is **implicit only**. No SECURITY.md, no bus-factor docs, no launch runbook in-repo prior to this audit pack. Highest risks cluster around **discoverability**, **activation friction**, and **trust optics**—not around missing niche features.

---

## Prioritized risk table

| ID | Risk | L | I | Source Artifact(s) | Mitigation | Owner-type |
|----|------|---|---|-------------------|------------|------------|
| R01 | **No visuals in README** → visitors bounce; visualization product invisible | H | H | 3, 5, 6 | Hero GIF + screenshots before any launch | Maintainer (Design/Growth) |
| R02 | **7-step multi-service setup** → near-zero activation | H | H | 4, 7 | Compose-first + demo package + `make demo` | Maintainer (Product/Eng) |
| R03 | **Empty GitHub About/topics** → zero in-platform discovery | H | M | 1, 5 | Fill description + topics day 1 | Maintainer (Growth) |
| R04 | **123 agent-generated issues / 1 PR** → looks abandoned or unhealthy under launch scrutiny | H | H | 2, 6, 8 | Triage to &lt;25; prepared HN reply | Maintainer (Eng) |
| R05 | **Tech claim mismatch (Sigma.js vs ReactFlow)** → credibility hit | M | H | 1, 2, 3 | Fix README immediately | Maintainer (Eng) |
| R06 | **Unproven performance targets presented as fact** → HN pile-on | M | H | 2, 6 | Relabel as goals or publish benchmarks | Maintainer (Eng) |
| R07 | **No CI** → regressions; unsafe external PRs | H | M | 2, 9 | Add Actions for test/lint | Maintainer (Eng) |
| R08 | **Missing LICENSE file** despite MIT claim → corporate cannot use | H | M | 2, 10 | Add LICENSE; verify GitHub detects | Maintainer (Legal hygiene) |
| R09 | **Single-maintainer bus factor** | H | H | 2, 9, 10 | Docs, CONTRIBUTING, triage process; avoid personal heroics | Maintainer |
| R10 | **Neo4j heavy dependency** → casual users refuse install | H | H | 4, 10 | Demo path; later optional lighter store or hosted | Maintainer (Product) |
| R11 | **Scope creep from 123 issues + feature asks** | H | M | 2, 9 | Milestone discipline; close nits | Maintainer (Product) |
| R12 | **Open API, no general auth** → catastrophic if naively hosted | M | H | 2, 10, 12 | Never expose parse/clear publicly without auth/sandbox; SECURITY.md | Maintainer (Security) |
| R13 | **Default/hardcoded Neo4j passwords in compose** copied to prod | M | M | 2 | Docs warnings; force env override in prod compose | Maintainer (Eng) |
| R14 | **Parse path / filesystem access** abuse if API exposed | M | H | 2 | Enforce `allowed_parse_paths`; audit parse routes | Maintainer (Security) |
| R15 | **WebSocket/live update incomplete** → overpromised “real-time” | M | M | 2, 4 | Wire UI or remove claim | Maintainer (Eng) |
| R16 | **Python-only vs multi-lang expectations** | M | M | 1 | Position as Python-first depth | Maintainer (Product) |
| R17 | **Category competition (CodeLayers, VS Code tools, Sourcegraph)** | H | M | 1 | Differentiate local hierarchical + Neo4j ownership | Maintainer (Product/Growth) |
| R18 | **Show HN without demo** → flat launch, hard to re-do | M | H | 6, 7, 8 | Gate launch on Artifact 7 Phase D | Maintainer (Growth) |
| R19 | **React 18 / FastAPI pin drift** (Neo4j image pinned to **5.26-community** LTS — mitigated for Neo4j) | M | L–M | 2 | Track React 19 / FastAPI upgrades after launch | Maintainer (Eng) |
| R20 | **No metrics → cannot learn** | H | M | 11, 9 | Metrics log + labels; opt-in later | Maintainer (Growth) |
| R21 | **Name collision / weak brand “NeuroCode”** | M | L | 5 | Quick search; accept or rename early | Maintainer (Product) |
| R22 | **Placeholder `your-org` URLs** → broken first clone | H | M | 1, 4 | Fix all references | Maintainer (Eng) |
| R23 | **Monetization distraction at 0 users** | M | M | 10 | Explicit Stage 0: no paid build | Maintainer (CEO-mode) |
| R24 | **Dependabot-only open PR optics** | L | L | 2 | Merge or close; human roadmap PR | Maintainer (Eng) |
| R25 | **Mobile/touch UX broken if claimed** | M | L | 3 | Document desktop-first | Maintainer (Design) |

---

## Top 5 risks to address before launch (ordered)

1. **R01** Visual proof  
2. **R02** Setup / time-to-graph  
3. **R04** Issue tracker optics  
4. **R05 + R06 + R22** Truthfulness of README  
5. **R03 + R08** GitHub metadata + LICENSE  

Security risks **R12–R14** become #1 if and only if a public hosted demo is attempted.

---

## Gaps / Risks (meta)

- Likelihood/impact are expert estimates, **not actuarial**.  
- Runtime security audit (pentest) **not performed**.  
- Competitive moves (new free explore tools) can change R17 quickly—revisit quarterly.

---

## Checklist

### Pre-Launch risk burn-down
- [ ] Mitigate R01 (GIF)
- [ ] Mitigate R02 (demo path)
- [ ] Mitigate R04 (issue triage)
- [ ] Mitigate R05/R06/R22 (README truth)
- [ ] Mitigate R03/R08 (About + LICENSE)
- [ ] Mitigate R07 (CI)
- [ ] Explicit decision: no public unauthenticated API (R12)

### Launch
- [ ] Monitoring + hotfix plan (Artifact 8) covers residual R18
- [ ] Prepared responses for R04/R06

### Post-Launch
- [ ] Monthly risk review (15 min): update L/I
- [ ] Bus factor doc: “if I’m hit by a bus” (R09)
- [ ] Reassess R10 (Neo4j friction) from setup issues data
- [ ] Reassess R17 from win/loss notes vs alternatives users mention
