# Helper Utilities

This module provides internal utility functions shared across the Acme Platform
services. It is not part of the public API and its interface may change without
notice between minor releases. All functions in this module are considered
internal implementation details and are subject to change at any time without
deprecation warnings or migration guides being provided.

## Functions

### `retry(fn, attempts=3, backoff=0.5)`

Retry a callable up to `attempts` times with exponential backoff.

```python
from acme.core.utils import retry

result = retry(lambda: unstable_api_call(), attempts=5, backoff=1.0)
```

### `chunk(iterable, size)`

Split an iterable into fixed-size chunks.

```python
from acme.core.utils import chunk

for batch in chunk(user_ids, 100):
    bulk_update(batch)
```

### `deep_merge(base, override)`

Recursively merge two dicts. Keys in `override` take precedence.

```python
from acme.core.utils import deep_merge

config = deep_merge(defaults, user_config)
```

### `slugify(text)`

Convert a string to a URL-safe slug.

```python
slugify("Hello World!") == "hello-world"
```
