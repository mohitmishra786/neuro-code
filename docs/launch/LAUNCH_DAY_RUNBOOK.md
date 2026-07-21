# Launch day runbook

**Do not execute public posts without explicit human confirmation.**

Full hour-by-hour plan: audit Artifact 08. Summary:

## Pre-flight

- [ ] CI green on `main`
- [ ] `make demo` works twice
- [ ] Open issues triaged / optics acceptable
- [ ] Drafts open: SHOW_HN.md, first comment, X_THREAD.md
- [ ] Calendar block 08:00–12:00 ET for replies
- [ ] Hotfix via short-lived branches; no force-push mid-launch

## T+0

1. Submit Show HN  
2. First comment with setup + limitations  
3. Watch issues + thread  

## If asked “why so many issues?”

> Most historical tickets were auto-generated static analysis debt from an internal agent pass (not user reports). We closed that bulk backlog as not-planned for v0.1 and track real work in a small set of human-written issues. Please open a **new** issue with repro for anything user-facing.

## Hotfix

- README wrong → fix within 15m, comment on HN  
- Demo parse crash → patch + note commit  
- Security report → SECURITY.md process; do not debate in public thread  
