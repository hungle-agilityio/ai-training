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

## GitHub token cannot see the repository

- **Symptom:** the GitHub MCP tool `get_me` works, but reading the repository fails with "Could not resolve to a Repository". `gh pr checks` fails with "Resource not accessible by personal access token".
- **Cause:** a fine-grained token only reaches the repositories chosen in its settings, and only with the permissions ticked. GitHub answers "not found" instead of "forbidden".
- **Fix:** in the token settings add the repository and the permissions (Issues, Pull requests, Contents, and Checks: Read to see checks). No restart is needed; try the call again.

## MCP tools missing in a session

- **Symptom:** the GitHub tools are not there although `.mcp.json` is committed.
- **Cause:** a project `.mcp.json` is read from the folder where the session is opened. Here it lives in `claude-code-training-lab/`, one level below the git root.
- **Fix:** open the session in `claude-code-training-lab/`. See ADR-006.

## Attaching a sub-issue

- **Symptom:** `gh issue create --parent` does not exist (gh 2.83); the MCP tool `sub_issue_write` rejects the issue number.
- **Cause:** `sub_issue_write` wants the internal issue id, not the number.
- **Fix:** for a new issue pass `parent_issue_number` to `issue_write` (create). For an existing one read its id with `gh api repos/<repository>/issues/<number> --jq .id` (this command always asks) and pass it as `sub_issue_id`.

## An issue with every box ticked cannot be published

- **Symptom:** the issue check says "Done when: it needs at least one checkbox item (- [ ])" for an issue that records finished work.
- **Cause:** the check requires an open box.
- **Fix:** add one real item that is still open (for example "the epics point to this issue"), publish, tick it and close the issue when it is true. Do not weaken the check.
