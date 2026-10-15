# Architecture

```
reviewradar/        Django project (settings, urls)
reviews/            Django app
  models.py         data definitions only (Branch, Review)
  repositories.py   data access; one place for queries
  services.py       business logic (scores, pagination, filters)
  forms.py          input validation
  views.py          thin HTTP layer
  templates/        HTML
  tests/unit        fast tests, no database where possible
  tests/integration views and queries, with the test database
```

## Data flow of a page

request → view → form validates the input → service applies rules → repository reads the data → service returns plain dataclasses (for example `BranchScore`) → view renders the template.

## Why

- Rules live in one place (services), so the dashboard and the review list cannot disagree.
- Queries live in repositories, so query count is easy to assert and N+1 is easy to spot.
- Rules for each layer: `rules/architecture.md`.
