# Conventions

- **Language:** code, commits and reviews in English. Issues in plain English for non-technical readers.
- **Naming:** functions and modules `snake_case`; constants `UPPER_CASE` at the top of the module (for example `REVIEWS_PER_PAGE`); results returned as frozen dataclasses.
- **Docstrings:** one line saying the rule, not what the code does (see `rounded_average`).
- **Tests:** name says the behaviour (`test_average_rounds_half_up`); assert the type of numbers, and the query count for list pages.
- **Ordering:** always add a unique tiebreaker (`-created_at`, `-id`).
- **Issues, branches, commits:** `rules/issues.md` and `rules/git.md`.
