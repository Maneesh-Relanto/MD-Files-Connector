# Architecture Overview

This document describes the high-level architecture of Acme Platform.
It is intended for engineers joining the team and contributors making
structural changes.

## System Diagram

```
┌─────────────┐     REST/GraphQL      ┌──────────────────┐
│   Client    │ ───────────────────▶ │   API Gateway    │
└─────────────┘                       └────────┬─────────┘
                                               │
                          ┌────────────────────┼────────────────────┐
                          │                    │                    │
                   ┌──────▼──────┐    ┌───────▼──────┐    ┌────────▼───────┐
                   │  User Svc   │    │  Job Svc     │    │  Metrics Svc   │
                   └──────┬──────┘    └───────┬──────┘    └────────────────┘
                          │                   │
                   ┌──────▼──────────────────▼──────┐
                   │           PostgreSQL            │
                   └────────────────────────────────┘
```

## Components

### API Gateway

- Nginx reverse proxy + rate-limiter
- JWT validation via shared signing key
- Routes to downstream services by path prefix

### User Service

- CRUD for User, Organization, and Team entities
- Owns the authentication flow
- Written in Python / FastAPI

### Job Service

- Background task queue backed by Redis Streams
- Workers auto-scale via Kubernetes HPA
- Dead-letter queue for failed tasks after 3 retries

### Metrics Service

- Prometheus-compatible `/metrics` endpoint
- Aggregates counters from all other services via push gateway

## Data Model

Each service owns its own PostgreSQL schema (logical multi-tenancy).
Cross-service data access goes through the service's REST API — never
direct DB joins.

## Deployment

All services are deployed as Docker containers on Kubernetes.
See the deployment runbook at `scripts/deployment/DEPLOY.md` for step-by-step
production deployment instructions.
