# ReviewRadar

Online reputation management for businesses with several locations: collect customer reviews, see how each location is rated, and respond faster.

**Status:** MVP in progress. The dashboard and the reviews page work on demo data; review import, sentiment analysis with the Claude API and reply suggestions are planned.

## Overview

Clinics, spas, salons and similar businesses lose revenue to bad reviews and slow replies, and a manager of many locations cannot see at a glance which location needs attention. ReviewRadar gathers the reviews of every location in one place, scores each location, and (planned) suggests replies.

The project is also the vehicle of a 15-day Claude Code training lab (see [Training lab](#training-lab)).

## Features

| Feature | Status |
|---|---|
| Dashboard: key numbers, location scores, rating breakdown, latest reviews | Done |
| Reviews page: table of all reviews, newest first, 20 per page, full text on hover or focus | Done |
| JSON API for location scores (`/api/dashboard/`) | Done |
| Demo data command | Done |
| Filter reviews by good or bad and by week | Planned (#4) |
| Import reviews from CSV or a mock API | Planned |
| Sentiment classification with the Claude API | Planned (today sentiment is derived from the stars) |
| Reply drafts in the language of the review | Planned (#5) |
| Score trend per location | Planned |

## Tech stack

- Python 3.11+, Django 5.2, SQLite
- `uv` for the environment and dependencies
- `pytest` (with `pytest-django`, `pytest-mock`, `pytest-cov`), `ruff`, `mypy` (strict) with `django-stubs`
- Automatic checks: a GitHub workflow is added in a later task (the old pipeline file `.gitlab-ci.yml` is legacy)

## Getting started

### Prerequisites

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)

### Install and run

```bash
uv venv
uv pip install -r requirements.txt
uv run python manage.py migrate
uv run python manage.py seed_demo_data
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/. If port 8000 is busy, use `runserver 8800`.

`seed_demo_data` **deletes the local data** and creates 1 business, 3 locations (Airport, Downtown, Riverside) and 10 reviews. Options:

| Option | Effect |
|---|---|
| `--branches N` | Add N extra locations with 3 reviews each (for example `--branches 597` gives about 1,800 reviews) |
| `--with-new-branch` | Add a location without reviews (reproduces issue #3) |

### Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure development key | Secret key. Always set it outside development. |
| `DJANGO_DEBUG` | `1` | Set to `0` in production. |

Time zone is `Asia/Ho_Chi_Minh`. Never commit `.env` or secrets.

## Usage

| Address | What it shows |
|---|---|
| `/` | Redirects to the dashboard |
| `/dashboard/` | Key numbers, score per location, rating breakdown, latest reviews |
| `/reviews/` | All reviews in a table with pagination (`?page=N`) |
| `/api/dashboard/` | JSON: review count and average rating per location |

## Project structure

```
reviewradar/            Django project (settings, urls)
reviews/                Django app
  models.py             Data definitions only
  repositories.py       Data access (queries)
  services.py           Business logic
  forms.py              Input validation
  views.py              Thin HTTP layer
  templates/, static/   Pages and stylesheet
  management/commands/  seed_demo_data
  tests/unit/           Unit tests
  tests/integration/    Integration tests
docs/
  issues/               Issues by type: bugs/, features/, tasks/ (index in README.md)
  templates/            Issue and README templates
  journal/, courses/    Training notes
.claude/                Claude Code skills and agents shared by the team
.gitlab/                Legacy issue templates, replaced by `.github/` in a later task
```

## Architecture

Clean architecture with the logic in the service layer:

- **Views** only read the request, call a service and render. No business logic.
- **Services** hold the business rules and return plain data objects.
- **Repositories** own the database queries.
- **Models** define data only.

Rules: type hints on every function and strict `mypy`; validate input with Django Forms; no `*` imports; no Django signals for business logic; no N+1 queries (`select_related`, `prefetch_related` or one aggregate query); never log personal data or credentials.

## Development

### Quality checks

```bash
uv run ruff check .    # lint
uv run mypy .          # types (strict)
uv run pytest          # tests with coverage
```

Target: 90% coverage on the service layer. Mock external APIs; tests never use the network. The automatic checks (lint, types, tests) move to a GitHub workflow in a later task.

### Workflow

- Work is tracked as GitHub issues; the drafts and the index are in `docs/app/issues/`. The issue number is the GitHub issue number (`#6`).
- Branch: `<kind>/<number>-<description>`, for example `bug/1-dashboard-wrong-score`.
- Commit: title, blank line, detail, blank line, `Part of #<number>`.
- Pull request into `main`: title `[type] title`, for example `[FEAT] Reviews page to show all reviews`, description ends with `Closes #<number>`. A human reviews and merges it.
- The rules are in [`.claude/CLAUDE.md`](.claude/CLAUDE.md) and [`.claude/rules/`](.claude/rules); the skills and agents that apply them are in `.claude/`.

## Known issues and roadmap

| # | Issue | State |
|---|---|---|
| 1 | Dashboard numbers look wrong (rounding) | Fixed |
| 2 | Dashboard is very slow with many locations (one query per location) | Open, failing test in place |
| 3 | A location without reviews breaks the dashboard | Open, failing test in place |
| 4 | Filter reviews by good or bad and by week | Open |
| 5 | Reply drafts in the wrong language | Open, feature not built yet |
| 6 | Reviews page | Built, issue still to confirm |

Two tests fail on purpose until #2 and #3 are fixed.

Limitations: there is no login and data is not limited per business, so the dashboard and the reviews page show the reviews of every business. Do not use real customer data until access control is added.

## Documentation

- [`docs/app/issues/README.md`](docs/app/issues/README.md): index of issues
- [`docs/app/reviewradar-project-context-2026-10.md`](docs/app/reviewradar-project-context-2026-10.md): project context and standards
- [`docs/app/templates/`](docs/app/templates/): issue templates and the README template

## Training lab

ReviewRadar is built as part of a **15-day Claude Code training lab**: each day adds a Claude Code skill to the real project (issues, tests, sub-agents, skills, hooks) instead of a toy exercise.

> [!NOTE]
> **Progress: 1 of 15 days done, Day 2 in progress.** Skills, sub-agents and `CLAUDE.md` were started early, during Day 2.

| Day | Topic | Practice | Status | Notes |
|:---:|---|---|:---:|:---:|
| 1 | Setup and Claude 101 | Project skeleton, first conversations with Claude | ✅ | [journal](docs/learning/journal/day-01.md) |
| 2 | Issue analysis, reproduce and understand | Analyse issues, reproduce bugs, write failing tests, `git pull --rebase`, merge conflict | 🟨 | [journal](docs/learning/journal/day-02.md) |
| 3 | To be defined | | ⬜ | [journal](docs/learning/journal/day-03.md) |
| 4 | The `.claude/` folder | | ⬜ | [journal](docs/learning/journal/day-04.md) |
| 5 | `CLAUDE.md` | | ⬜ | [journal](docs/learning/journal/day-05.md) |
| 6 | Sub-agents | | ⬜ | [journal](docs/learning/journal/day-06.md) |
| 7 | Slash commands and skills | | ⬜ | [journal](docs/learning/journal/day-07.md) |
| 8 | MCP | | ⬜ | [journal](docs/learning/journal/day-08.md) |
| 9 | Hooks | | ⬜ | [journal](docs/learning/journal/day-09.md) |
| 10-11 | To be defined | | ⬜ | [10](docs/learning/journal/day-10.md), [11](docs/learning/journal/day-11.md) |
| 12-15 | Capstone | | ⬜ | [12](docs/learning/journal/day-12.md), [13](docs/learning/journal/day-13.md), [14](docs/learning/journal/day-14.md), [15](docs/learning/journal/day-15.md) |

✅ done · 🟨 in progress · ⬜ not started

<details>
<summary>What the lab has produced so far</summary>

- **Skills** (`.claude/skills/`): `write-issue` (one complete issue file), `create-commit` (branches and commits that follow the project rules), `create-issue` and `create-pull-request` (publish on GitHub with the `gh` command), `review-pull-request`, `write-tests`, `diagnose-bug` and `grill-me`.
- **Sub-agents** (`.claude/agents/`): `analyst` (analyses an issue against the code), `planner` (turns the analysis into a step-by-step plan), `implementer` and `reviewer`.
- **Templates** (`docs/app/templates/`): issue templates and the README template.
- **Issues** (`docs/app/issues/`): five seeded issues analysed and reproduced, and the reviews page (#6), built and tested.
- **Rules** (`.claude/CLAUDE.md` and `.claude/rules/`): issue, branch, commit and pull request formats, the workflow by difficulty (easy, medium, hard) and lessons learned.

</details>
