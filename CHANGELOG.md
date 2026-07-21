# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(0.x = early API may break).

## [Unreleased]

### Added

- MIT `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
- GitHub Actions CI (backend pytest/ruff, frontend lint/type-check/test)
- Dependabot config for npm, pip, and GitHub Actions
- `examples/demo_pkg` sample project for first-run
- `make demo` / `scripts/first_run.sh` one-command path to first graph
- Graph legend, empty-state setup CTA, health banners, WebSocket wiring in App
- Parse path allowlist enforcement (`API_ALLOWED_PARSE_PATHS`)
- CLI entrypoint `cli_main:main` (`neurocode`)
- Docs: `BENCHMARKS.md`, `UI.md`, `llms.txt`, launch drafts under `docs/launch/`
- Positioning README (persona, pitch, ReactFlow stack truth, competitor table)
- Neo4j Docker image pin to `5.26-community` LTS

### Fixed

- README claimed Sigma.js; actual renderer is ReactFlow
- Placeholder `your-org/neurocode` clone URLs
- `RelationshipType` TypeScript definition was corrupted

### Changed

- Performance table labeled as goals; measurements live in `docs/BENCHMARKS.md`
- Edge stroke contrast increased on dark canvas

## [0.1.0] — TBD

Initial public alpha tag when pre-launch exit criteria are met (see `docs/launch/PRE_LAUNCH_EXIT.md`).
