# Intent: starter-refresh

## Problem

New projects start from the template repository `hungle-agilityio/agent-flow-starter`. The template was filled on 2026-11-11 from `ops/bootstrap.py --stack` and has not changed since. The flow of this repository moved on: ADR-026 to ADR-033 (issue pack and test matrix, build trust, member assignment, `/code-review`, the app prototype, security checks before a release, post-release checks, card tap approval). A project made from the template today starts with the flow of 2026-11-11.

Running `ops/bootstrap.py --stack` again does not fix it on its own:

- the manifest copies the decision records ADR-008 to ADR-019 only (the template's ADR-020 to ADR-025 were added by hand), while the copied texts cite ADR-020 to ADR-033;
- the copied index `docs/decisions/README.md` lists ADR-001 to ADR-033, also the ones that are not copied;
- the copied Project instructions put the prototype in `design/app/prototype.html`, but say the spec pull request changes only `docs/intent/` and `docs/specs/`, so the prototype cannot go in the spec pull request of a new project.

## Goal

`ops/bootstrap.py --stack` writes a project with today's flow, complete on its own: every cited decision record, an index of exactly the copied records, and the prototype in `docs/design/prototype.html` inside the spec pull request. The template repository is then refreshed from that output, and the kickoff gets a Prototype step.

## Users

The owner, who starts every new project from the template; the loop and the Project threads of those projects.

## Out of scope

- Changing ReviewRadar's own layout or flow.
- The accessibility check and the browser regression screens in new projects (they need the app's screens; ADR-029, ADR-032 keep them out).
- Rewriting the decision records as generic texts: they are copied as they are on `main`, with the paths moved by the bootstrap (owner's Q3).
- Labels: the tick and the build create `agent:in-epic` and `agent:plan-review` when missing.
