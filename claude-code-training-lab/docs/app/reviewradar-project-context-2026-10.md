# ReviewRadar: Project Context (2026-10)

Upload this file to the Claude.ai Project "ReviewRadar Learning Lab". Update it when the project changes.

## What it is

ReviewRadar is a Django app for online reputation management. It collects customer reviews for businesses with multiple branches, classifies sentiment with the Claude API, suggests replies, and shows a score dashboard per branch.

Target customers: clinics, spas, salons and similar businesses that lose revenue to bad reviews and slow responses.

## MVP scope

- Import reviews from CSV or a mock API.
- Classify sentiment (positive, negative, neutral, mixed) using the Claude API.
- Suggest a reply draft for each review.
- Dashboard: average score and trend per branch.

## Learning focus

This repo is a 15-day training lab for Claude Code. ReviewRadar is the vehicle: real LLM integration, caching, and multi-branch business modeling.

## Planned entities (not implemented yet)

| Entity | Purpose |
|--------|---------|
| Business | A customer company, owns branches |
| Branch | One location of a business |
| Review | A customer review at a branch (source, rating, text, date) |
| Sentiment | Classification result for a review |
| ReplyDraft | A suggested reply for a review |

## Current code layout

```
reviewradar/        Django project (settings, urls)
reviews/            Django app
  models.py         data definitions only
  repositories.py   data access
  services.py       business logic
  views.py          thin HTTP layer
  tests/unit/       unit tests
  tests/integration/ integration tests
```

All modules are empty skeletons at this stage.

## Engineering standards

- Clean architecture and DDD: business logic lives in the service layer, never in views. Models hold data only.
- Explicit over implicit: no `*` imports, no Django signals for business logic. Call services explicitly.
- Type hints on every function signature, strict `mypy`.
- Validate all input with Pydantic or Django Forms.
- Avoid N+1 queries: use `select_related` / `prefetch_related`.
- Never log PII or credentials. Secrets go in `.env`.
- Tests: `pytest` with `pytest-mock`. 90% coverage on the service layer. Mock external APIs, never hit the network.

## Tooling

- Run: `uv venv`, `uv pip install -r requirements.txt`, `uv run python manage.py runserver`.
- Test: `uv run pytest`.
- Branch: `feat/claude-code-training-lab`.

## How I want Claude to help

- I am learning, so explain the reasoning briefly, then give a runnable example.
- Reply in Vietnamese. Keep technical terms and code in English.
