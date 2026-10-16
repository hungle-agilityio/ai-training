---
name: write-tests
description: Write or fix unit and integration tests for ReviewRadar (pytest, pytest-django). Use when adding tests for a ticket, reproducing a bug with a failing test, or checking query counts, number types and coverage of services and repositories.
---

# Write tests

Rules: `rules/python.md`. Pitfalls to cover: `knowledge/KNOWN_PITFALLS.md`.

1. **Reproduce first.** For a bug, write the test that fails with the symptom from the ticket, run it, see it fail for the right reason, then fix the code.
2. **Place it.** Rules and calculations: `reviews/tests/unit`. Views, forms and queries: `reviews/tests/integration`.
3. **Assert what the business sees.** Exact values (3.67, not "a number"), the type of numbers (`float`, not `int`), the empty case, and ordering with ties.
4. **Assert the query count** on every list or dashboard page: `django_assert_max_num_queries`. Dev SQLite hides N+1.
5. **No network.** Mock external APIs with `pytest-mock`.
6. **Run:** `uv run pytest -q --no-cov` for a quick result, `uv run pytest` for coverage (target 90% on services and repositories). Failing tests that belong to open bug tickets are expected: say so in the report.
