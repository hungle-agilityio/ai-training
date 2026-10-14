# ReviewRadar: project rules

## Tickets

- **Ticket ID:** a plain number (`1`, `4`, `6`), shared by bugs, features and tasks, in the order the tickets are created (the same number the issue gets on GitHub, written `#6` in text). The type is shown by the title (`[BUG]`) and by the branch prefix, never by the ID.
- Issues live in `docs/issues/`, grouped by type: `bugs/`, `features/` and `tasks/`. Each issue is a folder named after it, for example `docs/issues/bugs/dashboard-wrong-score/` or `docs/issues/features/reviews-page/`, where the name is the short lowercase description also used in the branch name (`bug/1-dashboard-wrong-score`). `docs/issues/README.md` is the index of ID, type, folder and title; add a row for every new issue. The skill `write-ticket` creates **one** file in it: `04-final.md`, the complete standalone ticket built from `docs/templates/04-final-bug.md`, `04-final-feature.md` or `04-final-task.md`. It is posted as a GitHub issue, so it must not refer to any other file.
- `01-reported.md`, `02-analysis.md` and `03-discussion.md` (templates in `docs/templates/`) are learning material for the training: the report as received, our analysis and questions, and the conversation with the reporter. The skill does not create or change them.
- **Title format:** `[type] title`, where type is `BUG`, `FEAT` or `TASK`. Example: `[BUG] dashboard show wrong score number`.
- The ticket number is not part of the title or the folder name; it is in the index.
- Tickets are written in plain language for QA, BA and clients: no code, commits, branches or technical terms. Use the skill `write-ticket` (bug, feature or task).

## Branches

- **Format:** `<kind>/<id>-<short-description>`, with the ticket number and a short lowercase description separated by dashes.
  - Bug: `bug/<id>-...`, for example `bug/1-dashboard-wrong-score`
  - Feature: `feat/<id>-...`, for example `feat/4-filter-reviews`
  - Task: `task/<id>-...`, for example `task/6-cleanup-demo-data`
- One branch per ticket. Never commit directly to `main`.
- Use the skill `git` to create branches, commits and pull requests that follow these rules.

## Commits

Every commit message has three parts separated by a blank line:

```
<title>

<detail>

Part of <id>
```

- **title:** short, imperative, says what changed (no ticket ID needed in the title).
- **detail:** what changed and why. Wrap lines at about 72 characters.
- **Part of `<id>`:** the ticket ID, for example `Part of #1`. If a commit touches several tickets, add one `Part of` line per ticket.

Example:

```
Fix average score rounding on dashboard

The average was calculated with whole-number division, so 11 / 3
showed as 3. It now keeps the decimals (3.67).

Part of #1
```

## Pull requests

- PR title uses the same format as tickets: `[type] title`, for example `[BUG] dashboard show wrong score number`.
- The PR description follows `.github/pull_request_template.md` and ends with `Part of <id>`.

## Workflow for a ticket

Start with `ticket-analyst` (sub-agent in `.claude/agents/`): it analyses the ticket against the code and business logic, lists the questions, and after the answers rates the difficulty and suggests the workflow. For Medium and Hard tickets, `ticket-planner` then turns the analysis into a test-first, step-by-step plan for the implementer (Easy tickets need no plan).

```
Easy:    ✅ Analyse → ⬜ Plan → 🟩 Code → 🟩 Verify → 🟩 Commit → ⬜ Learn
Medium:  ✅ Analyse → 🟩 Plan → 🟩 Implement → 🟩 Verify + Review → 🟩 Commit → ⬜ Learn
Hard:    ✅ Analyse → 🟩 Plan (detailed, maybe split) → 🟩 Implement → 🟩 Verify + Review (tests, security) → 🟩 Commit → 🟩 Learn
```

Legend: ✅ done · 🟩 do · 🟨 optional · ⬜ skip · 🚧 not built yet

Full workflow: analyse ticket (`ticket-analyst`) -> plan -> implement -> verify and review (can include a test skill) -> commit -> learn. The implement, verify and review, commit and learn steps are added in later days.

## Lessons learned

- **Rounding:** Python `round()` rounds half to even (2.25 gives 2.2) but Excel and the business round half up. Use `rounded_average` in `reviews/services.py` (Decimal with `ROUND_HALF_UP`). A `-> float` annotation does not stop `//` from returning an `int`, and mypy does not catch it, so test the type.
- **Pagination:** order by a unique tiebreaker (`-created_at`, `-id`), because seed data has many reviews with the same timestamp. `Paginator.get_page(0)` returns the last page, so validate the page number with a form first.
- **Time zone:** `TIME_ZONE` is `Asia/Ho_Chi_Minh`; without it Django used America/Chicago and dates were shown a day early for Vietnam.
- **N+1:** the dev SQLite database hides it (each query is nearly free). Assert the query count in tests (`django_assert_max_num_queries`).
