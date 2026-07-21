# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues using one of:

1. **GitHub Private Vulnerability Reporting** — repository **Security** tab → **Report a vulnerability** (preferred when enabled).
2. **GitHub Security Advisories** for this repository if private reporting is unavailable.

Include:

- Description of the issue and impact
- Steps to reproduce (proof of concept if possible)
- Affected component (API, parser, Docker, frontend)
- Your contact for follow-up

We aim to acknowledge reports within **72 hours** and provide a status update within **7 days**.

## Security model (important)

NeuroCode is designed for **local / self-hosted** use on trusted networks:

- The HTTP API has **no general authentication** in development mode.
- The `POST /graph/parse` endpoint can read filesystem paths within configured allowlists.
- `DELETE /graph/clear` may require an API key when `API_KEY` is set.

**Do not expose the API or Neo4j ports to the public internet without additional authentication, network isolation, and a locked-down parse path allowlist.**

## Secrets and defaults

- Change default Neo4j passwords before any non-local deployment.
- Never commit real `.env` files or credentials.
- Prefer environment variables over hardcoding secrets in Compose for production.

## Dependency updates

Dependabot (or equivalent) is configured for npm and pip where possible. Review and merge security updates promptly.
