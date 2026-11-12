# Design

The design of ReviewRadar is one clickable prototype of the whole app: [`app/prototype.html`](app/README.md), published as a private Artifact (ADR-030). Every screen and state is there, on demo data, with the app's actions and animations. A request that changes what users see updates the prototype first; the owner approves it with "Prototype ổn" before the work is split into epics and tasks. Screens, texts and numbers here are demo data only, never customer data.

A needs-ui issue names the prototype state its build must match (`"design"` on a step of `## Screens to capture`); the verify report shows the design next to the built screen. A difference is reported for the owner, never fixed by changing the prototype.

The `design/<feature>/` folders hold the design cards made before 2026-11-12 (ADR-012); they are history.
