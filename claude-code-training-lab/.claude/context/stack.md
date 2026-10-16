# Stack

| Part | Choice |
|---|---|
| Language | Python 3.11 |
| Framework | Django 5 (`>=5.0,<6.0`) |
| Database | SQLite in dev (hides N+1; assert query counts in tests) |
| Time zone | `Asia/Ho_Chi_Minh` |
| Tooling | `uv`, `ruff`, `mypy` (strict, `django-stubs`) |
| Tests | `pytest`, `pytest-django`, `pytest-mock`, `pytest-cov` (tests in `reviews/tests`) |
| CI | none yet: a GitHub workflow (lint, types, tests) is added in the checks task |
| Tracker | GitHub, through the `gh` command (the MCP server comes later) |

Versions and settings come from `pyproject.toml` and the lock file `uv.lock` (install with `uv sync`); check them before relying on a version-specific feature.

## Commands

```
uv run ruff check .          # lint
uv run mypy .                # types (strict)
uv run pytest -q --no-cov    # tests (drop --no-cov for the coverage report)
uv run python manage.py runserver
```
