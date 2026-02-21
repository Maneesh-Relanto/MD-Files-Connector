# Future Roadmap — v2 and Beyond

This document captures ideas and planned work beyond the current release cycle.
Nothing here is committed. Items graduate from here into the project backlog when
they have a champion, an estimated effort, and a target quarter.

## Planned for v2.0

### Multi-region support

Allow deployments to span two or more AWS regions with active-active failover.
Primary blocker: PostgreSQL replication strategy (logical vs physical).
Owner: Infrastructure Team.

### SAML / SSO integration

Enterprise customers require SAML 2.0 IdP integration for single sign-on.
Target IdPs: Okta, Azure AD, Google Workspace.
Required before any Fortune-500 deals can close.

### Audit log API

Expose a queryable audit trail of all platform actions (create, update, delete,
login, logout, permission change) via a dedicated `/audit` REST endpoint.
Required for SOC 2 Type II compliance.

## Under Investigation

### WebAssembly plugin runtime

Allow third-party plugins to run in a sandboxed WASM environment so they
cannot access host resources directly. Exploratory spike planned for Q3 2026.

### Edge deployment

Run lightweight API Gateway nodes at CDN PoPs to cut latency for global
customers. Depends on multi-region work above.

## Icebox (no active work)

- Desktop app (Electron) — insufficient demand
- Mobile SDK — deferred until API is stable
- On-premise / self-hosted edition — requires significant packaging work
