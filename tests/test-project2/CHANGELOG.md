# Changelog

All notable changes to Acme Platform are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [2.1.0] — 2026-01-15

### Added
- New GraphQL subscription support for real-time events
- `acme watch` CLI command for live log tailing
- Prometheus metrics endpoint at `/metrics`

### Fixed
- Race condition in background job queue under high load
- Incorrect UTC offset in scheduled tasks running after DST change

### Changed
- Default timeout increased from 30s to 60s
- Log format now includes trace ID for distributed tracing

---

## [2.0.0] — 2025-09-01

### Breaking Changes
- Dropped Python 3.9 support; minimum is now 3.11
- Renamed `acme.utils.helpers` to `acme.core.utils`

### Added
- Complete REST API rewrite using FastAPI
- OpenAPI 3.1 spec auto-generated at `/openapi.json`
- First-class async support throughout

---

## [1.4.2] — 2025-06-10

### Fixed
- Memory leak in connection pool under sustained traffic
- Crash on empty config file
