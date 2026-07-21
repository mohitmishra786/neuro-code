# Contributing to NeuroCode

Thanks for your interest. NeuroCode is early (0.1.x); small, focused PRs are appreciated.

## Persona we optimize for

**Python engineers onboarding to large unfamiliar codebases** who want a local hierarchical knowledge graph—not multi-language AI SaaS.

## Development setup

See [README.md](README.md) Quick Start (`make demo`) and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

```bash
# Backend
cd backend && pip install -r requirements.txt
pytest tests/ -v
ruff check .

# Frontend
cd frontend && npm ci
npm run test -- --run
npm run lint
npm run type-check
```

## Pull requests

1. Fork and branch from `main`.  
2. Keep changes focused; reference audit items or issues when relevant (`[audit:02] …`).  
3. Add/update tests for code changes.  
4. Ensure CI is green.  
5. Update docs if behavior or setup changes.

## Issue triage

| Label | Meaning |
|-------|---------|
| `setup` | Cannot install / first graph |
| `bug` | Incorrect behavior with repro |
| `enhancement` | Feature request |
| `question` | Support / clarification |
| `agent-generated` | Auto static-analysis debt (may be closed as not planned for v0.1) |
| `launch-blocker` | Breaks demo path |
| `good first issue` | Scoped for newcomers |

### Maintainer SLA (solo)

- **Acknowledge** new user-facing issues within **72 hours** when possible.  
- No guaranteed fix timeline.  
- Style-only or speculative micro-optimizations may be closed as “not planned for v0.1”.

Please include: OS, Python/Node versions, steps to reproduce, and expected vs actual behavior.

## Code of conduct

Be respectful. Harassment or spam is not tolerated. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Report vulnerabilities privately—see [SECURITY.md](SECURITY.md).
