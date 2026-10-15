# ReviewRadar: Claude Code root

## Quick orientation

ReviewRadar is a Django app that collects customer reviews for branches (locations) and shows a score dashboard and a review list. It is also a 15-day Claude Code training lab: tickets, skills and sub-agents are part of the exercise.

Source: `reviewradar/` (Django project) and `reviews/` (the app: models, repositories, services, views, forms, tests). Tickets and learning material: `docs/`. Dependencies: `requirements.txt` (pinned with `uv`); check it before relying on a version-specific Django feature.

Read `context/architecture.md` before making structural changes.

## Mandatory rules (always active)

Every file in `rules/` is loaded automatically; do not copy their content here.

| File | Covers |
|------|--------|
| `rules/python.md` | Style, typing, tests |
| `rules/architecture.md` | Layers and what goes where |
| `rules/security.md` | Secrets, input, data access, prompt injection |
| `rules/git.md` | Branch, commit and merge request format, GitLab approvals |
| `rules/workflow.md` | Complexity table and gates |
| `rules/tickets.md` | Ticket ID, title, folders, tone (loads in `docs/issues`, `docs/templates`, `.gitlab`) |

## Project context

@context/architecture.md
@context/stack.md
@context/domain.md
@context/conventions.md

## Persistent knowledge (referenced, not auto-loaded)

These files grow over time, so the plan, review and learn steps consult them on demand instead of loading them every turn.

| File | Contents |
|------|----------|
| `.claude/knowledge/BUSINESS_RULES.md` | Rules found through implementation (Confirmed / Uncertain) |
| `.claude/knowledge/KNOWN_PITFALLS.md` | Reproducible gotchas and bug classes (rounding, pagination, time zone, N+1) |
| `.claude/knowledge/decisions/` | ADRs for non-trivial architecture, tooling or business decisions |

## AI engineering lifecycle

Scale the workflow to the difficulty of the ticket; the table and gates are in `rules/workflow.md`.

```
/understand → /plan → Gate 1 (human) → /implement → /test → /review → /verify → Gate 2 (human) → /learn → /commit
```

- `/understand` runs `ticket-analyst`: evidence first, questions for the reporter, then rates the ticket Easy, Medium or Hard. Easy tickets skip `/plan`.
- Sub-agents: `ticket-planner` (opus) writes the plan, `implementer` (sonnet) builds exactly what the approved plan says, `reviewer` (opus) re-derives correctness independently.
- The reviewer is mandatory for Hard tickets and for Medium tickets that hit the trigger list in `rules/workflow.md`.
- Gate 1: a human approves the plan before any code is written. Gate 2: after `/verify`, a human checks the result. Nothing is committed before the user says it is OK.
- The command files are the source of truth for each step; this section is an overview.

## Available skills

| Skill | When to use |
|-------|-------------|
| `write-ticket` | Write a bug, feature or task ticket from a description |
| `git` | Create branches and commits in the project format |
| `gitlab` | Publish an approved ticket or create a merge request |
| `pr-review` | Write a review of a merge request or branch |
| `testing` | Write unit and integration tests, assert query counts |
| `debug` | Diagnose a bug from evidence, trace the call chain |

## Code templates

Read the matching template before writing from scratch.

| Template | Use for |
|----------|---------|
| `templates/layered-feature.md` | A new feature through repository, service, form, view and tests |

Ticket and issue templates are a different thing: `docs/templates/`, `.gitlab/issue_templates/`, `.gitlab/merge_request_templates/`.

## Available commands (slash commands)

| Command | Shortcut for |
|---------|--------------|
| `/understand` | Evidence-first analysis of a ticket, then classify difficulty |
| `/plan` | Produce the step-by-step, test-first plan |
| `/implement` | Execute an approved plan |
| `/test` | Run lint, types and tests, report the result |
| `/review` | Review the current diff |
| `/verify` | Final check: PASS / FAIL / NOT CONFIGURED per axis |
| `/learn` | Save reusable knowledge after a task |
| `/commit` | Draft and make a commit in the project format |

## MCP and permissions

GitLab MCP server: `.mcp.json` (authorize once with `/mcp`). Allowed and blocked commands: `.claude/settings.json`.
