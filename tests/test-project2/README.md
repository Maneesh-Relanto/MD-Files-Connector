# Acme Platform

A fictional multi-service platform used to exercise every link and discovery
edge case in MD Files Connector.

---

## Quick Links

- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- <a href="LICENSE.md">License</a>
- [REST API Reference](docs/api/REST.md)
- [Quickstart Guide](docs/guides/quickstart.md)
- [Architecture Overview](./docs/internal/ARCHITECTURE.md)

<!-- Duplicate link — should count REST.md only once -->
- [REST API Reference (mirror)](docs/api/REST.md)

<!-- Dangling link — file does not exist on disk -->
- [Deprecated API v1](docs/deprecated/OLD_API.md)

---

## Installation

```bash
pip install acme-platform
```

---

## Usage

```bash
acme start --config config.yml
```

---

## API Examples

```bash
# Fetch all users
curl -H "Authorization: Bearer $TOKEN" https://api.acme.example.com/v2/users

# Submit a background job
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -d '{"type":"report","params":{"month":"2026-01"}}' \
  https://api.acme.example.com/v2/jobs
```

> **GraphQL:** A GraphQL API is available alongside REST. See the internal
> team wiki for schema details (not yet public-facing documentation).

---

## External Resources

- [Official Python Docs](https://docs.python.org/3/)
- [PyPI](https://pypi.org/project/acme-platform/)
- Hosted API spec at https://acme.example.com/openapi.md

---

## License

© 2026 Acme Corp — see <a href="LICENSE.md">LICENSE.md</a> for details.
