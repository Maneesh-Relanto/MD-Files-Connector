# Test Coverage Report

## Overview

Current test coverage across Acme Platform services.

| Service | Line Coverage | Branch Coverage | Target |
|---------|--------------|-----------------|--------|
| User Service | 94.2% | 88.7% | ≥ 90% |
| Job Service | 91.5% | 85.1% | ≥ 90% |
| API Gateway | 87.3% | 79.4% | ≥ 90% ⚠️ |
| Metrics Service | 96.1% | 91.0% | ≥ 90% |

API Gateway is currently below target. See open issues tagged `coverage-gap`.

## Running Tests

```bash
pytest --cov=acme --cov-report=term-missing
```

## Coverage Exclusions

Lines excluded from coverage measurement:

- `if TYPE_CHECKING:` blocks (type-only imports)
- `raise NotImplementedError` in abstract base methods
- `__repr__` and `__str__` methods
- Platform-specific branches (Windows-only code paths)

## Flaky Tests

Tests marked `@pytest.mark.flaky` are known intermittent failures under CI load.
Do not mark a test as flaky without raising an issue to investigate root cause.
