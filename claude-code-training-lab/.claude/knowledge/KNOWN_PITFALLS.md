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

## Case-insensitive search on SQLite

- **Symptom:** a search for `ĐAU CHÂN` does not find "Đau chân"; `NHÂN` does not find "nhân viên". `PARKING` finds "parking", so a test with plain English words passes.
- **Cause:** SQLite `LIKE` (Django `icontains`) and `lower()` fold the case of ASCII letters only. A letter written in a different Unicode form (NFC or NFD, common when text is copied from a Mac) does not match either.
- **Fix:** search a stored copy of the text made by `normalize_for_search` in `reviews/search_text.py` (NFC, casefold, NFC) and normalise the typed words the same way. Test with accented capital letters, not only English words. See ADR-007.

## A stored copy that is out of date

- **Symptom:** a review exists but a search never finds it.
- **Cause:** `Review.search_text` is filled only by `create_review` in `reviews/repositories.py`. A review made with `Review.objects.create`, `bulk_create` or changed with `update()` keeps an empty or old copy. `test_review_create_paths.py` catches only `create`, `bulk_create` and `Review(`, not `get_or_create`, `update_or_create` or an edit of `text`.
- **Fix:** create and change reviews only through the repository, and refresh `search_text` in any new edit path. Changing the normalisation rule needs a new backfill migration, because migration 0003 calls the live function.

## A browser-check step that clicks Export

- **Symptom:** a step fails with `net::ERR_ABORTED` and the expected text is not shown.
- **Cause:** the selector `a.button` matches the first link with that class, the Export CSV link, which starts a download instead of changing the page.
- **Fix:** scope the selector, for example `form.filters a.button` for Clear.
