# ReviewRadar: Claude Code root

## Quick orientation

ReviewRadar is a Django app that collects customer reviews for branches (locations) and shows a score dashboard and a review list. It is also a 15-day Claude Code training lab: issues, skills and sub-agents are part of the exercise.

Source: `reviewradar/` (Django project) and `reviews/` (the app: models, repositories, services, views, forms, tests). Docs are split in two: `docs/app/` (ReviewRadar: issues, templates, project context) and `docs/learning/` (Claude Code training: courses, journal, exercises, epics); see `docs/README.md`. Dependencies: `pyproject.toml` (ranges) and `uv.lock` (exact versions, install with `uv sync`); check them before relying on a version-specific Django feature.

Read `context/architecture.md` before making structural changes.

## Where things live

| Path | What it holds |
|---|---|
| `reviewradar/`, `reviews/` | The Django project and the app (tests in `reviews/tests/unit` and `reviews/tests/integration`) |
| `docs/app/` | ReviewRadar issues (`issues/`, index in its README), issue templates, project context |
| `docs/learning/` | Claude Code training: courses, journal, exercises, the epics and their working notes |
| `.claude/` | This folder: rules, context, knowledge, skills, agents, commands, hooks, settings |
| `../.github/` | Automatic checks (`workflows/`), issue forms, the pull request template, code owners and the dependency bot (GitHub reads it only at the repository root, one level above this folder) |
| `pyproject.toml`, `uv.lock` | Dependencies and their exact versions |
| `env.example` | Example settings; the real `.env` is never committed |

Remote: `origin` is the single GitHub repository named in `.claude/hooks/github-allowed-repo.txt`. Claude cannot reach any other repository (`rules/security.md`).

Never pushed: `db.sqlite3`, `.env`, `.venv`, caches, `.coverage`, `.claude/settings.local.json`, `CLAUDE.local.md`, anything with real customer data. A folder for imported customer files (`in/`) or generated output (`out/`) is created only when a feature needs it, and it is git-ignored.

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

## Where knowledge lives

| Channel | Holds | Reaches |
|---|---|---|
| This file and `.claude/rules/` | Project facts, conventions, must-follow rules | Everyone, through git |
| Memory (outside the repository) | The user's preferences and corrections | The user, every session |
| GitHub issues | Tasks and who claimed them | Every machine |
| Reports (an artifact, shared by private link) | Evidence and comment threads | Whoever the link is shared with |

If a second session needs it, it goes in a channel, not in one session's head. When the user corrects something that will come up again, save it as a memory (with why and how to apply); do not save what this repository already records. Explained it twice? A fact goes in this file, a procedure becomes a skill.

## When something becomes an artifact

| It is... | It goes to |
|---|---|
| Evidence of a change (verify report), a pull request review summary, before and after screenshots, a release note with an animation, a design card, a diagram of a mechanism | An artifact: one private link, updated in place as the work moves (`share-report`) |
| A short answer, a status, a question | The chat |
| A rule, a decision, an issue, an epic | A file in the repository |
| A deliverable for a client (Word, slides) | Rendered from its sources, not an artifact |

## AI engineering lifecycle

Scale the workflow to the difficulty of the issue; the table and gates are in `rules/workflow.md`.

```
/understand → /plan → Gate 1 (human) → /implement → /test → /review → /verify → Gate 2 (human) → /learn → /commit
```

- `/understand` runs `analyst`: evidence first, questions for the reporter, then rates the issue Easy, Medium or Hard. Easy issues skip `/plan`.
- Sub-agents, their roles and models are in the table below.
- The reviewer is mandatory for Hard issues and for Medium issues that hit the trigger list in `rules/workflow.md`. The team principles (never change the requirement, never widen the scope, the reviewer does not rely on the implementer's reasoning, at most two rounds of fix and review) and the guardrails are in the same file.
- Gate 1: a human approves the plan before any code is written. Gate 2: after `/verify`, a human checks the result. Nothing is committed before the user says it is OK.
- The command files are the source of truth for each step; this section is an overview.

| Sub-agent | Role | Model | Does |
|---|---|---|---|
| `analyst` | advisor | opus | evidence first, questions, rates the difficulty |
| `planner` | advisor | opus | writes the step-by-step plan |
| `implementer` | builder | sonnet | builds exactly what the approved plan says |
| `reviewer` | advisor | opus | re-derives correctness independently |
| `test-runner` | runner | haiku | runs the checks and reports only what failed |

Send wide searching to the `Explore` sub-agent and ask for the conclusion with the file and line, not a dump.

## Available skills

| Skill | When to use |
|-------|-------------|
| `write-issue` | Write a bug, feature or task issue from a description |
| `create-commit` | Create branches and commits in the project format |
| `create-issue` | Publish an approved issue |
| `draft-pull-request` | Draft a pull request from the verify report and before and after images, and say if it is complete |
| `create-pull-request` | Create a pull request for the current branch, from the draft, after approval |
| `review-pull-request` | Write a review of a pull request or branch |
| `write-tests` | Write unit and integration tests, assert query counts |
| `diagnose-bug` | Diagnose a bug from evidence, trace the call chain |
| `grill-me` | Settle every decision with the user, in rounds with recommended answers, before `/plan` |
| `check-in-browser` | Drive the pages in a headless browser, take screenshots, report console and network errors (the browser axis of `/verify`) |
| `build-verify-report` | Run every verify axis and write one report page with the real numbers and screenshots, then open it (`/verify`) |
| `share-report` | Share a verify report as a private link, only when the sharing gate allows (masking clean, standing approval on) |
| `capture-before-after` | Capture the same browser steps before and after a change on the same demo data and pair the screenshots |
| `work-queue` | Loop mode: take the next `agent:ready` issue to a pull request with a verify report; merge on the owner's `/merge` |

How a skill is built, where rulebooks live and the test pattern: `.claude/skills/README.md` (a layout test checks every skill).

## Code templates

Read the matching template before writing from scratch.

| Template | Use for |
|----------|---------|
| `templates/layered-feature.md` | A new feature through repository, service, form, view and tests |

Issue and pull request templates are a different thing: `docs/app/templates/` (the files `write-issue` fills in) and `../.github/ISSUE_TEMPLATE/` plus `../.github/PULL_REQUEST_TEMPLATE.md` (the forms on GitHub).

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

## Loop mode (unattended)

New request: you send it, we run `grill-me` here, confirm the UI/UX if users will see a change, you say OK, then the issue is published with a `Decisions` comment (and a `Design` comment) and labelled `agent:ready` (`write-issue` section 7).

`REVIEWRADAR_LOOP=1 claude`, then `/loop 30m use the work-queue skill`. It takes issues labelled `agent:ready` one at a time: analyse, decide, build, test, review, verify, commit on the issue branch, push, open the pull request, report as an artifact. It never waits for an answer, and keeps going while pull requests wait for you (at most 5). Every open point is decided and listed in the report. You answer on the pull request: `/merge` and the loop merges it, `/redo <what>` sends it back. Labels: `agent:ready`, `agent:running`, `agent:review`, `agent:failed`. When the queue is empty you get one notification. Why: ADR-008, ADR-009.

## MCP and permissions

GitHub: through the `gh` command and the official GitHub MCP server (`.mcp.json`, token only in the environment variable `GH_TOKEN`, never written to a file; the server is limited by the token to the one repository). Allowed, asked and blocked commands: `.claude/settings.json`; the guards that run before shell commands (one repository only, commit checks, the token): `.claude/hooks/` (read its README for the limits).

## Removed, and why

Read this before bringing something back.

| Date | Removed | Why | Rebuild from |
|---|---|---|---|
| 2026-10-16 | GitLab: pipeline, templates, MCP entry | The project moved to GitHub | `.github/`, ADR-002 |
| 2026-10-16 | `requirements.txt` | A fresh clone could not run `uv run`; dependencies are now locked | `pyproject.toml`, `uv.lock`, ADR-005 |
| 2026-10-16 | Four-file issue folders for new issues | They were a learning exercise; one issue is one file | `docs/app/templates/`, ADR-003 |
| 2026-10-16 | The words "ticket" and "merge request" | GitHub says issue and pull request | `rules/naming.md`, ADR-001 |
| 2026-10-26 | Sections "Working with helpers" and "A short request" | Repeated what the rules and skills already say | `rules/workflow.md`, the skills |
| 2026-10-16 | Old names: skills `git`, `gitlab`, `testing`, `debug`, `pr-review`, `write-ticket`; helpers `ticket-analyst`, `ticket-planner` | One naming standard | `rules/naming.md`, ADR-001 |
