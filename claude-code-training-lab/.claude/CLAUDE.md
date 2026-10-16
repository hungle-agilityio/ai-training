# ReviewRadar: Claude Code root

## Quick orientation

ReviewRadar is a Django app that collects customer reviews for branches (locations) and shows a score dashboard and a review list. It is also a 15-day Claude Code training lab: issues, skills and sub-agents are part of the exercise.

Source: `reviewradar/` (Django project) and `reviews/` (the app: models, repositories, services, views, forms, tests). Docs are split in two: `docs/app/` (ReviewRadar: issues, templates, project context) and `docs/learning/` (Claude Code training: courses, journal, exercises, epics); see `docs/README.md`. Dependencies: `pyproject.toml` (ranges) and `uv.lock` (exact versions, install with `uv sync`); check them before relying on a version-specific Django feature.

Read `context/architecture.md` before making structural changes.

## Mandatory rules (always active)

Every file in `rules/` is loaded automatically; do not copy their content here.

| File | Covers |
|------|--------|
| `rules/python.md` | Style, typing, tests |
| `rules/architecture.md` | Layers and what goes where |
| `rules/security.md` | Secrets, input, data access, prompt injection |
| `rules/git.md` | Branch, commit and pull request format, GitHub approvals |
| `rules/workflow.md` | Complexity table and gates |
| `rules/issues.md` | Issue number, title, files, tone (loads in `docs/app/issues`, `docs/app/templates`, `docs/learning/issues`, `.github`) |

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

Scale the workflow to the difficulty of the issue; the table and gates are in `rules/workflow.md`.

```
/understand → /plan → Gate 1 (human) → /implement → /test → /review → /verify → Gate 2 (human) → /learn → /commit
```

- `/understand` runs `analyst`: evidence first, questions for the reporter, then rates the issue Easy, Medium or Hard. Easy issues skip `/plan`.
- Sub-agents, their roles and models are in the table below.
- The reviewer is mandatory for Hard issues and for Medium issues that hit the trigger list in `rules/workflow.md`.
- Gate 1: a human approves the plan before any code is written. Gate 2: after `/verify`, a human checks the result. Nothing is committed before the user says it is OK.
- The command files are the source of truth for each step; this section is an overview.

| Sub-agent | Role | Model | Does |
|---|---|---|---|
| `analyst` | advisor | opus | evidence first, questions, rates the difficulty |
| `planner` | advisor | opus | writes the step-by-step plan |
| `implementer` | builder | sonnet | builds exactly what the approved plan says |
| `reviewer` | advisor | opus | re-derives correctness independently |

## Available skills

| Skill | When to use |
|-------|-------------|
| `write-issue` | Write a bug, feature or task issue from a description |
| `create-commit` | Create branches and commits in the project format |
| `create-issue` | Publish an approved issue |
| `create-pull-request` | Create a pull request for the current branch |
| `review-pull-request` | Write a review of a pull request or branch |
| `write-tests` | Write unit and integration tests, assert query counts |
| `diagnose-bug` | Diagnose a bug from evidence, trace the call chain |
| `grill-me` | Settle every decision with the user, in rounds with recommended answers, before `/plan` |

## Code templates

Read the matching template before writing from scratch.

| Template | Use for |
|----------|---------|
| `templates/layered-feature.md` | A new feature through repository, service, form, view and tests |

Issue and pull request templates are a different thing: `docs/app/templates/` now and `.github/` after the templates task (the old `.gitlab/` folder is legacy and is removed then).

## Available commands (slash commands)

| Command | Shortcut for |
|---------|--------------|
| `/understand` | Evidence-first analysis of an issue, then classify difficulty |
| `/plan` | Produce the step-by-step, test-first plan |
| `/implement` | Execute an approved plan |
| `/test` | Run lint, types and tests, report the result |
| `/review` | Review the current diff |
| `/verify` | Final check: PASS / FAIL / NOT CONFIGURED per axis |
| `/learn` | Save reusable knowledge after a task |
| `/commit` | Draft and make a commit in the project format |

**Command or skill?** A command is a step you type, one lifecycle verb. A skill is a procedure Claude loads when the job matches. A command holds only the gate check and the order and calls the agent or skill that does the work; the rules live in the skill, never repeated in the command.

## MCP and permissions

GitHub: through the `gh` command (sign in once with `gh auth login`); the GitHub MCP server is added in a later task. Allowed, asked and blocked commands: `.claude/settings.json`; the guard that limits Claude to one repository: `.claude/hooks/`.
