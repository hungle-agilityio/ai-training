---
description: Run lint, types and tests and report the result
---

Run, in this order, and report each result:

```
uv run ruff check .
uv run mypy .
uv run pytest -q --no-cov
```

- Show the failing tests with the reason in one line each.
- Failing tests that belong to open bug tickets are expected: say which ticket, do not hide them.
- Do not change code in this step unless I ask. See the `write-tests` skill for writing tests.
