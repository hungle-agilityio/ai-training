# Stack

| Part | Choice |
|---|---|
| Language | Python 3.11 |
| Framework | Django 5 (`>=5.0,<6.0`) |
| Database | SQLite in dev (hides N+1; assert query counts in tests) |
| Time zone | `Asia/Ho_Chi_Minh` |
| Tooling | `uv`, `ruff`, `mypy` (strict, `django-stubs`) |
| Tests | `pytest`, `pytest-django`, `pytest-mock`, `pytest-cov` (tests in `reviews/tests`); `playwright` (headless Chromium) for the browser check |
| CI | GitHub Actions `../.github/workflows/checks.yml` (runs inside `claude-code-training-lab/`): `ruff`, `mypy`, `pytest`, a 90% coverage gate on services and repositories, and the hook tests |
| Tracker | GitHub, through the `gh` command and the GitHub MCP server (`.mcp.json`; the token comes from the environment variable `GH_TOKEN`) |

Versions and settings come from `pyproject.toml` and the lock file `uv.lock` (install with `uv sync`); check them before relying on a version-specific feature.

## Commands

```
uv run ruff check .          # lint
uv run mypy .                # types (strict)
uv run pytest -q --no-cov    # tests (drop --no-cov for the coverage report)
uv run python manage.py runserver
```
