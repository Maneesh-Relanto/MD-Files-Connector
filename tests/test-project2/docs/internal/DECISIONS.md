# Decisions Log

This document records informal design decisions and trade-offs made during
development that do not warrant a full ADR. For formal architectural decisions
see the ADR index in `docs/adr/`.

---

## 2026-02-10 — Rate limiting strategy

**Decision:** Implement rate limiting at the gateway level (Nginx) rather than
inside each microservice.

**Reason:** Centralised enforcement, no code duplication, easier to adjust
limits without redeploying services.

---

## 2026-01-22 — Pagination style

**Decision:** Use cursor-based pagination for all list endpoints.

**Reason:** Offset pagination is unreliable on rapidly changing datasets
(items can be skipped or duplicated when pages shift as rows are inserted/deleted).

---

## 2025-12-05 — Error response format

**Decision:** All errors return `{"error": {"code": "...", "message": "..."}}`.

**Reason:** Consistent shape makes client error handling simpler. HTTP status
carries the severity; the body carries the machine-readable code.

---

## 2025-11-18 — Database migrations

**Decision:** Use Alembic for schema migrations with auto-generation disabled.

**Reason:** Auto-generated migrations have caused production incidents in the
past (dropped columns detected too late). All migrations are written by hand
and reviewed in PR.

---

## Note on deployment procedures

For production deployment steps refer to the deployment runbook. That document
is maintained by the infrastructure team and covers rollback procedures,
environment variable rotation, and post-deploy smoke tests.
