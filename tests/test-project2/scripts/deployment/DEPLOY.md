# Production Deployment Runbook

This runbook covers deploying Acme Platform to the production Kubernetes cluster.
Follow every step in order. Do not skip verification steps.

**Required access:** AWS console, kubectl prod context, GitHub Actions.
**On-call required:** Yes — keep the primary and secondary on-call engineers
available throughout the deployment window.

---

## Pre-deployment Checklist

- [ ] All CI checks passing on the release branch
- [ ] Staging deploy completed and smoke tests passing
- [ ] Database migration reviewed by at least one additional engineer
- [ ] Rollback plan documented (see Step 6 below)
- [ ] Incident channel open and team notified of deployment window

---

## Step 1 — Create the release tag

```bash
git tag -a v2.1.0 -m "Release v2.1.0"
git push origin v2.1.0
```

This triggers the production GitHub Actions pipeline automatically.

---

## Step 2 — Monitor the build

Open the Actions tab and watch the `deploy-production` workflow.
Expected duration: 4–8 minutes.

---

## Step 3 — Run database migrations

```bash
kubectl --context=prod exec -it deploy/api-gateway -- alembic upgrade head
```

Verify output ends with `Done.` — any error is a blocking issue.

---

## Step 4 — Verify pod rollout

```bash
kubectl --context=prod rollout status deployment/user-service
kubectl --context=prod rollout status deployment/job-service
kubectl --context=prod rollout status deployment/api-gateway
```

All three must report `successfully rolled out`.

---

## Step 5 — Smoke test

```bash
curl -sf https://api.acme.example.com/healthz | jq .
# Expected: {"status":"ok","version":"2.1.0"}
```

---

## Step 6 — Rollback Procedure

If any step fails:

```bash
# Roll back to previous image version
kubectl --context=prod rollout undo deployment/api-gateway
kubectl --context=prod rollout undo deployment/user-service
kubectl --context=prod rollout undo deployment/job-service
```

Then revert the migration if it was applied:

```bash
kubectl --context=prod exec -it deploy/api-gateway -- alembic downgrade -1
```

---

## Post-deployment

- Update the GitHub release with release notes from `CHANGELOG.md`
- Close the deployment tracking issue
- Post a summary in the `#deployments` Slack channel
