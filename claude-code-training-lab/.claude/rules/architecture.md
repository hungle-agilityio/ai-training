# Architecture rules

Layers, from the HTTP edge inward: `views.py` → `forms.py` / `services.py` → `repositories.py` → `models.py`.

- **Models:** data definition only.
- **Repositories:** the only place that builds queries. Use `select_related` / `prefetch_related`; an N+1 query is a blocker.
- **Services:** business logic and rules. No HTTP objects, no request.
- **Forms:** validate every input (page number, filters) before it reaches a service.
- **Views:** thin. Parse the request, call a service, render. No logic, no queries.
- Dependencies point inward only: a repository never imports a service, a service never imports a view.
- Full picture and reasons: `context/architecture.md`.
