# ReviewRadar: project rules

## Tickets

- Each ticket is a folder `docs/bugs/<ID>/` (`BUG-001/`, `FEAT-004/`, `TASK-006/`) with four files, one per stage:
  1. `01-reported.md`: the ticket as reported, not enough information yet. Never edited afterwards.
  2. `02-analysis.md`: our review: Analysis (3 sentences), what we found, numbered Questions for the reporter.
  3. `03-discussion.md`: the conversation between the reporter and the assignee: answers to our questions and any new information.
  4. `04-final.md`: the complete issue, built from the discussion. It is posted as a standalone GitHub issue, so it must not refer to any other file.
- Templates are in `docs/templates/` (`01-reported.md`, `02-analysis.md`, `03-discussion.md`, `04-final-bug.md`, `04-final-feature.md`, `04-final-task.md`).
- **Title format:** `[type] title`, where type is `BUG`, `FEAT` or `TASK`. Example: `[BUG] dashboard show wrong score number`.
- The ticket ID (`BUG-001`) is a separate field in the ticket, not part of the title.
- Tickets are written in plain language for QA, BA and clients: no code, commits, branches or technical terms. Use the skill `write-ticket` (bug, feature or task).

## Branches

- **Format:** `<kind>/<id>-<short-description>`, with the ticket ID and a short lowercase description separated by dashes.
  - Bug: `bug/<id>-...`, for example `bug/BUG-001-dashboard-wrong-score`
  - Feature: `feat/<id>-...`, for example `feat/FEAT-004-filter-reviews`
  - Task: `task/<id>-...`, for example `task/TASK-006-cleanup-demo-data`
- One branch per ticket. Never commit directly to `main`.

## Commits

Every commit message has three parts separated by a blank line:

```
<title>

<detail>

Part of <id>
```

- **title:** short, imperative, says what changed (no ticket ID needed in the title).
- **detail:** what changed and why. Wrap lines at about 72 characters.
- **Part of `<id>`:** the ticket ID, for example `Part of BUG-001`. If a commit touches several tickets, add one `Part of` line per ticket.

Example:

```
Fix average score rounding on dashboard

The average was calculated with whole-number division, so 11 / 3
showed as 3. It now keeps the decimals (3.67).

Part of BUG-001
```

## Pull requests

- PR title uses the same format as tickets: `[type] title`, for example `[BUG] dashboard show wrong score number`.
- The PR description follows `.github/pull_request_template.md` and ends with `Part of <id>`.

## Workflow for a ticket

Start with `ticket-analyst` (sub-agent in `.claude/agents/`): it analyses the ticket against the code and business logic, lists the questions, and after the answers rates the difficulty and suggests the workflow.

```
Easy:    ✅ Analyse → ⬜ Plan → 🟩 Code → 🟩 Verify → 🟩 Commit → ⬜ Learn
Medium:  ✅ Analyse → 🟩 Plan → 🟩 Implement → 🟩 Verify + Review → 🟩 Commit → ⬜ Learn
Hard:    ✅ Analyse → 🟩 Plan (detailed, maybe split) → 🟩 Implement → 🟩 Verify + Review (tests, security) → 🟩 Commit → 🟩 Learn
```

Legend: ✅ done · 🟩 do · 🟨 optional · ⬜ skip · 🚧 not built yet

Full workflow: analyse ticket (`ticket-analyst`) -> plan -> implement -> verify and review (can include a test skill) -> commit -> learn. The plan, implement, review and learn steps are added in later days.
