# Workflow: difficulty and gates

`analyst` rates every issue after the reporter's questions are answered. The rating decides the steps.

| Difficulty | Typical issue | Plan | Reviewer sub-agent | Learn |
|---|---|---|---|---|
| Easy | One layer, clear rule, a few lines | skip | no | skip |
| Medium | Several layers or one new rule | `/plan` | only if a trigger below applies | optional |
| Hard | New feature, migration, cross-cutting rule, unclear scope | `/plan`, detailed, maybe split | yes | yes |

## Triggers (a Medium issue gets the reviewer when it touches)

- Rounding, averages or any number the business reads
- Pagination, ordering or filters
- Time zone or dates
- Queries on a list or dashboard (N+1 risk)
- Migrations or data changes
- Anything that handles secrets, input from users or external services

## Gates

- **Gate 1 (human check, after `/plan`):** Claude shows the plan and stops. The user reads it and says OK or asks for changes. Do not implement before that answer.
- **Gate 2 (human check, after `/verify`):** Claude reports the evidence (lint, types, tests, issue checks, review findings) and stops. The user checks the result, in the running app when the issue is visible, and says OK or asks for changes. Claude does not commit, `/learn` or move on before that answer. Tests that belong to open bug issues are expected to fail; say so.
- **Gate 3 (before push, issue or pull request):** the user approves that exact item.

Gates 1 and 2 are always a human decision, never assumed. Gate 2 applies to every difficulty. Easy issues also stop for the human check after `/test`.

## Rules of the flow

- Tests first: write or update the test that shows the problem, then the code.
- The implementer builds only what the approved plan says. A change of scope goes back to `/plan`.
- **grill-me before the plan (proposed, never automatic):** after `/understand`, if the issue is Medium or Hard, or any decision is still open, Claude says how many decisions are open and asks whether to run `grill-me` before `/plan`, then waits. Only the user can skip it. Easy issues do not get the question.
- One branch and one issue at a time.
- Review happens locally before the pull request; on GitHub the checks run and a human reviews and merges.
