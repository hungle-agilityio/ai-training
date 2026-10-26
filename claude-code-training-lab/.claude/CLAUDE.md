# ReviewRadar

Django app that collects customer reviews per branch (location), shows a score dashboard and a review list. It is also a Claude Code training lab: the issues, skills and sub-agents are part of the exercise.

## Layout

- `reviewradar/`, `reviews/`: the code (layers in `rules/architecture.md`).
- `in/`: what a client gives us (not committed). `out/`: what we show outside (reports, exports; git-ignored). Both are created when a feature needs them.
- `docs/app/`: ReviewRadar issues, templates, project background. `docs/learning/`: the Claude Code training.
- `.claude/`: `rules/` (loaded automatically), `knowledge/` (business rules, pitfalls, ADRs; read when planning or reviewing), `skills/`, `agents/`, `commands/`, `hooks/`, `settings.json`.
- The git root is one level up (`../.github`). Open sessions in this folder (ADR-006).

## Commands

`uv sync`, then `uv run ruff check .`, `uv run mypy .`, `uv run pytest -q --no-cov`, `uv run python manage.py runserver`. Python 3.11, Django 5, SQLite in dev (it hides N+1: assert query counts). CI: `../.github/workflows/checks.yml`.

## Workflow

`/understand` → `/plan` → Gate 1 → `/implement` → `/test` → `/review` → `/verify` → Gate 2 → `/learn` → `/commit`. Difficulty, triggers and gates: `rules/workflow.md`. Sub-agents `analyst`, `planner`, `implementer`, `reviewer`, `test-runner`; send wide searches to `Explore`. A new feature starts from `templates/layered-feature.md`.

**Main way: a Claude Code Project** (claude.ai/code or the phone app, ADR-010). You talk to the project conversation; `grill-me`, the UI/UX confirmation, the issue and the pull request are done by its threads, following `.claude/project-instructions.md` and the root `../CLAUDE.md`. Cloud threads do not load skills, agents, hooks or `settings.json`, so those rules are text there. You press Merge it.

**CLI loop (kept until the Project path is proven):** `REVIEWRADAR_LOOP=1 claude`, then `/loop 30m use the work-queue skill`. It takes issues labelled `agent:ready`, opens the pull request and never merges. ADR-008, ADR-009.

## Where things go

A rule: `rules/`. A decision: an ADR. A gotcha: `knowledge/KNOWN_PITFALLS.md`. Your preferences: memory. Evidence of a change: a verify report shared as a private artifact (`share-report`). A fact explained twice goes here; a procedure becomes a skill. Keep this file short.

## Removed, and why

| Date | Removed | Why | Rebuild from |
|---|---|---|---|
| 2026-10-16 | GitLab: pipeline, templates, MCP entry | The project moved to GitHub | `.github/`, ADR-002 |
| 2026-10-16 | `requirements.txt` | A fresh clone could not run `uv run`; dependencies are now locked | `pyproject.toml`, `uv.lock`, ADR-005 |
| 2026-10-16 | Four-file issue folders for new issues | They were a learning exercise; one issue is one file | `docs/app/templates/`, ADR-003 |
| 2026-10-16 | The words "ticket" and "merge request"; old skill and helper names | One naming standard | `rules/naming.md`, ADR-001 |
| 2026-10-26 | `.claude/README.md`, `context/` (merged into `rules/` and this file), the skill, command, sub-agent and artifact tables, "Working with helpers", "A short request" | Repeated what the rules, the skills and the tool list already say | `rules/`, each `SKILL.md` |
