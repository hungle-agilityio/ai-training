# Architecture rules

```
reviewradar/        Django project (settings, urls)
reviews/            the app: models, repositories, services, forms, views, templates
  tests/unit        fast tests, no database where possible
  tests/integration views and queries, with the test database
```

Layers, from the HTTP edge inward: `views.py` → `forms.py` / `services.py` → `repositories.py` → `models.py`. A page: request → view → form validates → service applies the rules → repository reads → service returns plain frozen dataclasses (for example `BranchScore`) → view renders.

- **Models:** data definition only.
- **Repositories:** the only place that builds queries. Use `select_related` / `prefetch_related`; an N+1 query is a blocker.
- **Services:** business logic and rules. No HTTP objects, no request.
- **Forms:** validate every input (page number, filters) before it reaches a service.
- **Views:** thin. Parse the request, call a service, render. No logic, no queries.
- Dependencies point inward only: a repository never imports a service, a service never imports a view.

Why: rules live in one place so the dashboard and the review list cannot disagree; queries live in repositories so the query count is easy to assert.
