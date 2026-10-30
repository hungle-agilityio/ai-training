# ReviewRadar

Online reputation management for businesses with several locations: collect customer reviews, see how each location is rated, and respond faster.

**Status:** MVP in progress. The dashboard, the reviews page with filters and the JSON API work on demo data; review import, sentiment analysis with the Claude API and reply suggestions are planned.

## Overview

Clinics, spas, salons and similar businesses lose revenue to bad reviews and slow replies, and a manager of many locations cannot see at a glance which location needs attention. ReviewRadar gathers the reviews of every location in one place, scores each location, and (planned) suggests replies.

The project is also the vehicle of a 15-day Claude Code training lab (see [Training lab](#training-lab)).

## Features

| Feature | Status |
|---|---|
| Dashboard: key numbers, location scores, rating breakdown, latest reviews | Done |
| Reviews page: table of all reviews, newest first, 20 per page, full text on hover or focus | Done |
| Filter reviews by location, rating (good or bad) and week | Done |
| JSON API for location scores (`/api/dashboard/`) | Done |
| Demo data command | Done |
| Import reviews from CSV or a mock API | Planned |
| Sentiment classification with the Claude API | Planned (today sentiment is derived from the stars) |
| Reply drafts in the language of the review | Planned |
| Score trend per location | Planned |

## Tech stack

- Python 3.11+, Django 5.2, SQLite
- `uv` for the environment and dependencies
- `pytest` (with `pytest-django`, `pytest-mock`, `pytest-cov`), `ruff`, `mypy` (strict) with `django-stubs`
- Automatic checks: a GitHub workflow (`../.github/workflows/checks.yml`, at the repository root) runs lint, types, tests and a coverage gate

## Getting started

### Prerequisites

- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)

### Install and run

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed_demo_data
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/. If port 8000 is busy, use `runserver 8800`.

`seed_demo_data` **deletes the local data** and creates 1 business, 3 locations (Airport, Downtown, Riverside) and 10 reviews. Options:

| Option | Effect |
|---|---|
| `--branches N` | Add N extra locations with 3 reviews each (for example `--branches 597` gives about 1,800 reviews) |
| `--with-new-branch` | Add a location without reviews (the dashboard shows it without a score) |

### Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure development key | Secret key. Always set it outside development. |
| `DJANGO_DEBUG` | `1` | Set to `0` in production. |

Time zone is `Asia/Ho_Chi_Minh`. Never commit `.env` or secrets.

## Deploy

ReviewRadar is online at <https://reviewradar.onrender.com>, hosted on Render's free plan. `render.yaml` at the repository root describes the service.

- The site sleeps after 15 minutes without visits. The first visit then waits about a minute.
- Every start fills the database with the demo data again. Nothing typed online is kept.
- A merge to `main` does not change the live site. A release does: the owner asks for one in the Project, and the Mac mini creates the branch `release/sprint-N` and the tag `vYYYY.MM.DD` from the green `main` and moves the branch `deploy`. Render follows `deploy` and deploys it after the GitHub `Checks` are green.
- If a deploy fails, the previous version stays online.
- A bad release is undone with Render's Rollback button, then fixed on `main` and released again.

One-time steps for the owner:

1. Make the first release before creating the Blueprint: Render needs the branch `deploy` to exist.
2. Sign in to render.com with GitHub and let Render read only `hungle-agilityio/ai-training`.
3. New → Blueprint → choose this repository.
4. Keep the generated `DJANGO_SECRET_KEY`.
5. If the name `reviewradar` is taken, set `DJANGO_ALLOWED_HOSTS` to the address Render shows.

## Usage

| Address | What it shows |
|---|---|
| `/` | Redirects to the dashboard |
| `/dashboard/` | Key numbers, score per location, rating breakdown, latest reviews |
| `/reviews/` | All reviews in a table with pagination and filters (`?page=N&location=ID&rating=good` or `bad`, `&week=YYYY-MM-DD`) |
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
  app/                  The app: issues/ (index in README.md), templates/, project context
  learning/             Claude Code training: courses/, journal/, exercises/, epics/
.claude/                Claude Code skills and agents shared by the team
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
uv run coverage report --include="reviews/services.py,reviews/repositories.py" --fail-under=90   # coverage gate
uv run pytest .claude/hooks/tests .claude/skills --no-cov   # tests of the hooks and the skills' scripts
uv run python .claude/skills/check-in-browser/browser_check.py   # browser check (once: uv run playwright install chromium)
uv run python .claude/skills/build-verify-report/build_report.py --title "<issue>" --browser   # every axis in one report
uv run python .claude/skills/capture-before-after/before_after.py --base <ref>   # screenshots before and after a change
```

Target: 90% coverage on the service layer. Mock external APIs; tests never use the network. The GitHub workflow runs the same checks on every push to `main` and on every pull request.

### Workflow

- Work is tracked as GitHub issues; the drafts and the index are in `docs/app/issues/`. The issue number is the GitHub issue number (`#6`).
- Branch: `<kind>/<number>-<description>`, for example `bug/1-dashboard-wrong-score`.
- Commit: title, blank line, detail, blank line, `Part of #<number>` (left out while there is no issue number).
- Pull request into `main`: title `[type] title`, for example `[FEAT] Reviews page to show all reviews`, description ends with `Closes #<number>`. A human reviews and merges it.
- The rules are in [`.claude/CLAUDE.md`](.claude/CLAUDE.md) and [`.claude/rules/`](.claude/rules); the skills and agents that apply them are in `.claude/`.

## Known issues and roadmap

| Issue | State |
|---|---|
| Dashboard numbers look wrong (rounding) | Fixed |
| Dashboard is very slow with many locations (one query per location) | Fixed: the scores load in one query, and a test asserts the query count |
| A location without reviews breaks the dashboard | Fixed: the location is shown without a score |
| Reviews page, with filters by location, rating and week | Built and tested |
| Reply drafts in the wrong language | Open, the reply feature is not built yet |

All tests pass.

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
- **Issues** (`docs/app/issues/`): five seeded issues analysed and reproduced, and the reviews page, built and tested.
- **Rules** (`.claude/CLAUDE.md` and `.claude/rules/`): issue, branch, commit and pull request formats, the workflow by difficulty (easy, medium, hard) and lessons learned.

</details>
