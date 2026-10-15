# Known pitfalls

Reproducible gotchas. Add one entry per pitfall with the symptom, the cause and the fix. Not auto-loaded: `/plan` and `/review` read it.

## Rounding

- **Symptom:** an average of 2.25 shows 2.2; 11 / 3 shows 3.
- **Cause:** Python `round()` rounds half to even, but Excel and the business round half up. A `-> float` annotation does not stop `//` from returning an `int`, and mypy does not catch it.
- **Fix:** use `rounded_average` in `reviews/services.py` (Decimal, `ROUND_HALF_UP`) and test the type of the result.

## Pagination

- **Symptom:** the same review appears on two pages, or page 0 shows the last page.
- **Cause:** seed data has many reviews with the same timestamp; `Paginator.get_page(0)` returns the last page.
- **Fix:** order by a unique tiebreaker (`-created_at`, `-id`) and validate the page number with a form first.

## Time zone

- **Symptom:** dates shown a day early for Vietnam.
- **Cause:** without `TIME_ZONE`, Django used America/Chicago.
- **Fix:** `TIME_ZONE = "Asia/Ho_Chi_Minh"`.

## N+1 queries

- **Symptom:** slow dashboard in production, fine in dev.
- **Cause:** dev SQLite makes each query nearly free, so N+1 stays hidden.
- **Fix:** assert the query count in tests (`django_assert_max_num_queries`) and use `select_related` / `prefetch_related`.

## Markdown placeholders

- **Symptom:** a template preview looks empty or shows `[]`.
- **Cause:** `<title>` is read as an HTML tag and hidden.
- **Fix:** write `\<title>`.
