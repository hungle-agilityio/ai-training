# Spec: fail-fix

## Summary

Nothing visible to users of ReviewRadar. Three changes to the flow: (1) `ops/pinned_tests.py` sees every query-cap test and lists only the tests the issue really touches; (2) the Project thread must run it and settle every hit before `agent:ready`, and the tick runs it again before each build; (3) a build that would stop with `needs-decision` for a technical reason fixes the issue itself (one round per issue), and the tick starts that issue first. One written exception to team principle 1 (ADR-024).

## Acceptance criteria

**The planning check (T1)**

- **AC1.** `ops/pinned_tests.py` counts a test as a query-cap test when it uses `django_assert_num_queries`, `django_assert_max_num_queries`, `assertNumQueries` or `CaptureQueriesContext`.
- **AC2.** A query-cap test is listed when the issue touches query code (`is_query_code`, as today). When the issue body names URLs in backticks (for example `/settings/` or `/locations/<id>/`, matched on the part before the first `<`), only the query-cap tests that request one of those URLs are listed; with no URL named, every query-cap test is listed as today. Its line says `query cap N` with the number from the test (or `query cap` when the number is not a literal).
- **AC3.** A name match no longer counts for the common file names `views.py`, `services.py`, `repositories.py`, `models.py`, `urls.py`, `forms.py` and `app.css`; tests under `../plugins/` are skipped when the issue lists at least one path under `## Files likely touched` and every one of them is under `reviews/` or `reviewradar/`. Other names match as today.
- **AC4.** `--unlisted` prints only the hits that are not already under `## Existing tests that change` and exits 1 when there is at least one, 0 otherwise.
- **AC5.** Run on the bodies of #397 and #399 as first posted (fixtures in the new test file), it lists `test_settings_page.py::test_get_makes_at_most_two_queries`, `test_settings_suggestions.py::test_settings_page_makes_at_most_two_queries`, and for #399 the three `test_page_needs_at_most_*_queries` tests of `test_location_page.py`, `test_location_trend.py`, `test_location_topics.py`; each of those runs prints at most 15 lines.

**The tick (T2)**

- **AC6.** Before it starts a build for an issue, the tick runs the AC4 check on the issue body. With unlisted hits it still starts the build, and the build prompt gets one extra line: `Pinned tests not listed: <path::test, ...>. Settle them with the self-fix step before you write code.` The check runs through the tick's host, so the tick tests can replace it, and an issue that touches no query code adds no line; the existing tick tests stay unchanged.
- **AC7.** An issue that carries a self-fix comment (first lines `<!-- work-queue -->` and `<!-- self-fix -->`) newer than its last build start and the label `agent:ready` is started before every other ready issue, oldest self-fix first. Dependencies, the file-overlap guard and the concurrency limit still apply.
- **AC8.** A `needs-decision` stop on an issue that already has a self-fix comment is a decision stop as today (no retry, one ntfy message). Every other rule of `retry_reason` is unchanged.

**The build (T3)**

- **AC9.** The work-queue skill, step 4 Decide, gets a self-fix branch: when the only reasons to stop are technical, the build fixes the issue instead of stopping. Technical means only:
  - an existing test pins a fixed number or a literal that an AC changes (for example a query cap, a count, a text set by an AC); the test goes under `## Existing tests that change` with old → new;
  - a file the plan needs is missing from `## Files likely touched` and is not a guarded file (`.claude/`, `.github/`, `plugins/`, `pyproject.toml`, `uv.lock`, `.mcp.json`);
  - an AC can be met with no extra cost by a narrower technical reading (for example reading a field in an existing query instead of adding one); the AC wording is tightened, never widened;
  - a decision the issue leaves open has a recommended option in the spec.
- **AC10.** A self-fix never deletes, skips or weakens a test beyond the new number the AC needs, never accepts a query count that grows with the data, never changes a text, page, business rule, permission, migration or data, and never adds a guarded file. Anything else stops with `needs-decision` as today.
- **AC11.** The self-fix edits the issue body, posts one comment whose first lines are `<!-- work-queue -->` and `<!-- self-fix -->` followed by a `## Decisions` table (what stopped, what changed, why it is technical), sets `agent:ready` and removes `agent:running`, and ends the run without a pull request. One self-fix per issue (AC8).
- **AC12.** The epic pull request body (`ops/epic_pull_request.py`) gets a section `## Self-decided fixes` listing each task issue with a self-fix comment and a link to that comment; with none, the section says `None.`. A loop pull request outside an epic gets the same section in its body.

**The rules (T4, built by hand)**

- **AC13.** ADR-024 records the exception to team principle 1 for the cases of AC9 and AC10; `rules/workflow.md` principle 1 points to it; `decisions/README.md` lists ADR-022, ADR-023 and ADR-024.
- **AC14.** `.claude/project-instructions.md`: before an issue gets `agent:ready`, the Project thread runs `uv run python ops/pinned_tests.py --unlisted <body file>` and settles every hit (list it under `## Existing tests that change`, or change the plan so it is not touched); an epic's `tasks.md` has a `## Query budget` table (page, queries on `main`, queries after each task) and a later task lists the query-cap tests an earlier task of the epic adds.
- **AC15.** Every test on `main` passes unchanged (`ops/pinned_tests.py` checked against these ACs: no existing test pins them); `uv run ruff check .`, `uv run mypy .` and `uv run pytest -q` pass. Each task puts its tests in the new test file it names. The plugin version goes up by one patch when plugin files change.

## Edge cases

- Empty: an issue with no query code and no named URL gets no query-cap line.
- Large data: AC10 refuses a limit that grows with the data.
- Permissions: the self-fix may not add guarded files; those still go to the owner.
- A self-fix that fails again goes to the owner (one round).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| What may the loop decide alone | Technical fixes only (AC9, AC10) | Everything, reviewed in the epic pull request; planning check only | Both real stops were technical; the owner keeps every change users see (owner, card 2026-11-10) |
| Rounds of self-fix | One per issue | Up to three | A second stop means the first reading was wrong; the owner decides |
| Who does the fix | The build that would stop, then the tick restarts it first | A separate fix build | No extra build; the tick reads the new issue body (test and file lists) at the next start |
| Where the owner sees it | `Decisions` comment on the issue and `## Self-decided fixes` in the pull request | Comment only | The owner reviews once, in the epic pull request |

## Design

Nothing visible to users.

## Open questions
