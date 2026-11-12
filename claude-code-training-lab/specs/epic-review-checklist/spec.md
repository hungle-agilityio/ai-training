# Spec: epic-review-checklist

## Summary

(1) `ops/epic_pull_request.py` adds a `## Review checklist` section with four unticked boxes to every epic pull request it opens. (2) The Release paragraph of `.claude/project-instructions.md` adds a live AC check after `ops/live_check.py` passes. Nothing visible to users of the app.

## User story

As the owner, I want a short checklist for the epic review and a live AC check after each release, so that gaps become same-day issues.

## Acceptance criteria

- **AC1.** `ops/epic_pull_request.py` `body_for` puts this section directly after the task table (before `## Tests changed by the tasks`, `## Self-decided fixes` and `## Guard files changed`), exactly:

  ```
  ## Review checklist

  - [ ] Every task meets its ACs (open each verify report in the table above)
  - [ ] Guard files changed: each listed file is expected
  - [ ] Query budget: each page of the epic stays within the `## Query budget` of its `tasks.md`
  - [ ] Self-decided fixes: each fix is acceptable
  ```
- **AC2.** Given epic #600 whose pull request body has the checklist with the first box ticked by the owner (`- [x] Every task meets ...`), when the tick later rewrites the body (a new task line, the tests changed by the tasks, the self-decided fixes or the guard files section), then the checklist stays in place with the same ticks.
- **AC3.** An epic pull request opened before this change (no `## Review checklist`) is not given one; the tick never adds the section to an existing body.
- **AC4.** New tests in `ops/tests/test_epic_review_checklist.py` for AC1 to AC3 (no network, a fake `gh` as in `ops/tests/test_epic_pull_request.py`). `ops/tests/test_tick_allowed_edits.py::test_the_epic_body_has_the_section_above_closes` and the other tests on `main` that read `body_for` output keep passing unchanged.
- **AC5.** `.claude/project-instructions.md`, Release paragraph: after `ops/live_check.py` prints `result: pass` (post-release epic, AC27 of `specs/post-release/spec.md`), the release thread on the Mac mini lists the epic pull requests in the release (titles starting `[EPIC]` in the `release.py` output), reads each epic's `specs/<feature>/spec.md` on `main`, and checks every AC written Given/When/Then on the live site (`[live] url` of `ops/flow.toml`), signed in as `demo` in a headless browser, keeping no screenshot and no page text beyond the AC's own expected text. It reports one table per epic: AC, `pass`, `fail: <what it saw>` or `n/a: <why>` (for example the Given data is not in the live demo data). For each `fail` it drafts a fast-lane issue (Summary with the user story, the failed AC as AC1, the steps it took, `Part of the epic #<N>` removed, labels `risk:low` plus `needs-ui` when users see it) and shows it on a choice card: A "Đăng issue (đề xuất)", B "Bỏ qua". It posts only after A. On `result: fail` of the live check this step does not run.
- **AC6.** After AC5 merges, the thread gives the owner the exact new Release paragraph to paste into Project settings.

## Edge cases

- Empty: a release with no epic pull request: the thread says `No epic in this release; no live AC check.`
- Large data: one table per epic; no limit on ACs.
- Permissions: only the demo account is used; the live database is the demo seed (ADR-032), so no customer data is seen.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Who fills the epic checklist? | The tick writes four empty boxes; the owner ticks them | Claude's epic review ticks them | One file changes and the owner stays the reviewer (ADR-022) (owner, 2026-11-12) |
| Q2 Live AC check after a release? | Yes, after `live_check.py` passes; each gap becomes a draft fast-lane issue the owner approves | `live_check.py` is enough | `live_check.py` checks that screens load, not the behaviour of each AC (owner, 2026-11-12) |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users.

## Open questions
