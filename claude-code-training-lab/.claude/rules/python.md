# Python rules

Extends the global Python standards in `~/.claude/CLAUDE.md`; only project specifics are listed here.

- Python 3.11, Django 5. `ruff` (line length 100, rules E F I UP B) and `mypy --strict` with the Django plugin must pass.
- All function signatures have type hints. No `*` imports.
- Money-like or score numbers: never trust `round()` or `//` (see `knowledge/KNOWN_PITFALLS.md`); use `rounded_average` in `reviews/services.py`.
- Tests: `pytest`, `pytest-django`, `pytest-mock`; unit tests in `reviews/tests/unit`, integration tests in `reviews/tests/integration`. Coverage target 90% on services and repositories. Never hit the network; mock external APIs.
- Prefer explicit service calls over Django signals for business logic.
