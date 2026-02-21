# ADR 0001 — Initial Architecture and Tech Stack

**Date:** 2024-03-01
**Status:** Accepted
**Deciders:** Platform Team

---

## Context

We are building a new multi-tenant SaaS platform from scratch. We need to
choose the core technology stack, API style, data store, and deployment
approach before writing any product code.

## Decision

We will use the following stack:

- **Language:** Python 3.11+ (familiar to the whole team; strong async support)
- **API framework:** FastAPI (native async, auto-OpenAPI, Pydantic validation)
- **Database:** PostgreSQL 16 (battle-tested, rich feature set, full ACID)
- **Cache / queue:** Redis 7 (used for both ephemeral caching and job queues)
- **Deployment:** Docker + Kubernetes on AWS EKS
- **CI/CD:** GitHub Actions with multi-stage Docker builds

## Consequences

### Positive
- FastAPI's automatic OpenAPI generation eliminates manual spec maintenance
- PostgreSQL's JSONB support gives flexibility for semi-structured payloads
- Kubernetes enables zero-downtime deploys and auto-scaling

### Negative
- Kubernetes operational overhead; requires team upskilling on cluster management
- Python GIL limits CPU-bound parallelism; addressed by multi-process workers

## Alternatives Considered

- **Node.js / NestJS** — rejected; team is more fluent in Python
- **MongoDB** — rejected; relational data model is clearer for this domain
- **Serverless (Lambda)** — rejected; cold-start latency unacceptable for sync API

## Review Date

Revisit this decision when team size exceeds 20 engineers or annual request
volume exceeds 1 billion.
