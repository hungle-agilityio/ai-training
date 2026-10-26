# Python rules

Extends `~/.claude/CLAUDE.md`; only project specifics are listed here.

- Python 3.11, Django 5. `ruff` (line length 100, rules E F I UP B) and `mypy --strict` with the Django plugin must pass. All signatures typed, no `*` imports.
- Score-like numbers: never trust `round()` or `//` (`knowledge/KNOWN_PITFALLS.md`); use `rounded_average` in `reviews/services.py`.
- Code, commits and reviews in English. `snake_case`; constants `UPPER_CASE` at the top of the module; results as frozen dataclasses. A docstring is one line saying the rule, not what the code does.
- Ordering always has a unique tiebreaker (`-created_at`, `-id`).
- Tests: `pytest`, `pytest-django`, `pytest-mock`. The name says the behaviour (`test_average_rounds_half_up`); assert the type of numbers and the query count of list pages. Coverage 90% on services and repositories. Never hit the network.
- Prefer explicit service calls over Django signals.
