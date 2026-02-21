# Quickstart Guide

Get Acme Platform running in under 5 minutes.

## Prerequisites

- Python 3.11 or later
- An active Acme account (free tier available)
- Docker (optional, for the local dev stack)

## Step 1 — Install

```bash
pip install acme-platform
```

## Step 2 — Authenticate

```bash
acme login
# Enter your email and password when prompted
# An API token is stored at ~/.acme/credentials
```

## Step 3 — Create a project

```bash
acme init my-first-project
cd my-first-project
```

## Step 4 — Start the local dev server

```bash
acme dev
# Server running at http://localhost:8080
```

## Step 5 — Deploy

```bash
acme deploy --env production
```

You'll receive a deployment URL once the build finishes (usually 60–90 seconds).

## What's next?

- Read the [REST API Reference](../api/REST.md) to call the API programmatically
- Explore the advanced configuration options in the Advanced Guide
- Join the community forum for tips and examples
