# Advanced Guide

This guide covers advanced configuration and operational topics for Acme
Platform. It assumes you have completed the Quickstart Guide.

## Custom Configuration File

By default, Acme looks for `acme.yml` in the project root.
You can specify an alternative with `--config`:

```bash
acme start --config infra/production.yml
```

### Configuration Schema

```yaml
server:
  port: 8080
  workers: 4
  timeout: 60

database:
  url: postgresql://user:pass@localhost:5432/acme
  pool_size: 10
  max_overflow: 5

cache:
  backend: redis
  url: redis://localhost:6379/0
  default_ttl: 300

logging:
  level: INFO
  format: json
  output: stdout
```

## Environment Variables

All configuration keys can be overridden via environment variables using the
`ACME_` prefix with `__` as the delimiter for nested keys:

```bash
export ACME_SERVER__PORT=9090
export ACME_DATABASE__POOL_SIZE=20
export ACME_LOGGING__LEVEL=DEBUG
```

## Horizontal Scaling

Run multiple instances behind a load balancer. All instances must share:

1. The same `DATABASE_URL` (or a read replica)
2. The same Redis instance for cache and job queue
3. A shared secret key (set `ACME_SECRET_KEY` identically on all nodes)

## Plugin System

Acme supports first-party and community plugins loaded at startup.

```python
# acme_plugin.py
from acme.plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "my-plugin"

    def on_startup(self, app):
        app.register_route("/health-ext", self.health_check)

    async def health_check(self, request):
        return {"status": "ok", "plugin": self.name}
```

Register in `acme.yml`:

```yaml
plugins:
  - acme_plugin.MyPlugin
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ConnectionRefusedError` on start | DB not reachable | Check `DATABASE_URL` and firewall rules |
| Jobs stuck in `pending` | Redis not running | Start Redis: `redis-server` |
| 401 on all requests | Token expired or wrong secret | Rotate `ACME_SECRET_KEY` and re-issue tokens |
| High memory on workers | Large job payloads | Set `MAX_PAYLOAD_BYTES` in config |
