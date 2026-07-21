# Bus factor notes

NeuroCode is currently a **single primary maintainer** project.

## If the maintainer is unavailable

1. **Run locally:** `README.md` + `make demo` + `docs/DEPLOYMENT.md`  
2. **Architecture:** `docs/ARCHITECTURE.md`  
3. **Security model:** `SECURITY.md` — do not expose unauthenticated API  
4. **CI:** `.github/workflows/ci.yml`  
5. **Audit context:** `docs/audit/`  
6. **Implementation progress:** `docs/audit/IMPLEMENTATION_LOG.md`  

## Reduce bus factor

- Keep docs accurate with every behavior change  
- Prefer small PRs and `good first issue` with acceptance criteria  
- Avoid undocumented one-off production deploy scripts  
