# Spec: no-manual-label

## Summary

`agent:manual` and `agent:needs-permission` leave the flow. Every issue is `agent:ready`. The tick passes the issue's listed files to the build, and the plugin hook `before-edit-check` lets the build edit exactly those files, guarded files included. Settings that would switch guards off stay refused. Pull requests show which guarded files they change. Recorded in ADR-023. Nothing visible to users of the app.

Guarded files (today refused in loop mode): anything in a `.claude` or `.github` folder, `.mcp.json`, the plugin source (`plugins/`, `.claude-plugin/` at the git root), the gate files (`GATE_FILES` in `before-edit-check.py`) and an existing test under `checks.protected_test_dirs`.

## Acceptance criteria

**The hook lets a build edit what its issue lists (plugin)**

- **AC1.** In loop mode, `before-edit-check` reads `FLOW_ALLOWED_EDITS`: one path per line, relative to the project folder (`../` for the git root), compared without regard to letter case. An Edit, Write, MultiEdit or NotebookEdit on a listed path is allowed even when the path is guarded, and the hook answers `permissionDecision: allow`, so no `Edit(...)` allow rule in `.claude/settings.json` is needed.
- **AC2.** A guarded path that is not listed is refused with the same messages as today. An unguarded path that is not listed is left to the permission rules, as today. `FLOW_TEST_EDITS` keeps working as today.
- **AC3.** Always refused in loop mode, even when listed: a path inside `.git/`, and an edit to a `settings.json` or `settings.local.json` in a `.claude` folder whose result adds, removes or changes any of the keys `disableAllHooks`, `enabledPlugins`, `extraKnownMarketplaces`, `hooks`, `permissions.deny`. The hook works out the result from the tool input (Write: the content; Edit and MultiEdit: the edits applied to the file on disk). When it cannot (the old text is missing, or the result is not valid JSON) it refuses (fail closed). Message: `<name>: the loop never changes the keys that turn guards off (<keys>); ask the user`.
- **AC4.** `route_issue.py` prints the area label and `agent:ready` for every issue whose paths stay inside the git repository. It never prints `agent:manual` or `agent:needs-permission`. A path that leaves the repository (more `../` than the app folder depth) prints `NOT ROUTED: <path> is outside the repository` and exits 1. Its `--settings` option is kept and ignored.
- **AC5.** The work-queue skill says that the build may change the guarded files its issue lists, and nothing else that is guarded. The plugin version goes to `1.0.14`.

**The tick passes the list and stops skipping (ops)**

- **AC6.** For every build of an issue, the tick writes `allowed-edits` in the run folder: every path of `## Files likely touched` and of `## Existing tests that change` (without `::test`), one per line, relative to the project folder, and starts `claude -p` with `FLOW_ALLOWED_EDITS` set to that text. An issue with no listed path gets an empty value. A pull request run (change request) uses the list of the issue it closes.
- **AC7.** `agent:manual` leaves `SKIP_LABELS`; the tick no longer reads `agent:manual` or `agent:needs-permission` anywhere. An open issue with `agent:ready` is taken whatever other `agent:` label it has besides the status labels `agent:running`, `agent:review`, `agent:failed`, `agent:in-epic`.
- **AC8.** When the tick first labels a loop pull request `pr:ready-for-review`, it adds a section `## Guard files changed` above `Closes #` in its body: one backticked path per bullet for every guarded file in the pull request's changed files, or the line `None.`. The epic pull request (ADR-022) gets the same section for the whole epic branch against `main`. When the list is not empty, the ntfy message for that pull request ends with ` (changes guard files)`.
- **AC9.** `ops/bootstrap_manifest.toml` no longer creates `agent:manual` or `agent:needs-permission` for a new project, and bootstrap no longer prints the `agent:needs-permission` warning. Labels that already exist on GitHub are not touched.
- **AC10.** `ops/README.md` describes AC6 to AC8 and no longer names `agent:manual`.

**The record and the rules (by hand)**

- **AC11.** ADR-023 records the decision and the grill-me table. ADR-012, ADR-019 and ADR-020 each get one line under their status: `Superseded in part by ADR-023 (no agent:manual)`. Their text is otherwise unchanged.
- **AC12.** `.claude/project-instructions.md`, `.claude/CLAUDE.md` (the Two halves paragraph and a "Removed, and why" row dated 2026-11-09) and `docs/app/templates/spec/tasks.md` no longer offer `agent:manual` or `agent:needs-permission`; every issue is `agent:ready`, and an issue lists every file it will change, guarded ones included.
- **AC13.** Before T2 is merged, the Mac mini pushes a throw-away branch `task/probe-workflow-push` that changes one comment line in `.github/workflows/checks.yml`, with the same git remote and credentials the loop uses, then deletes it (no pull request). ADR-023 records the result. If GitHub refuses it, ADR-023 says that the token needs the Workflows permission, and the owner is told in the thread.
- **AC14.** Every test on `main` passes unchanged, except the tests listed under "Existing tests that change" in each task, which change only to expect `agent:ready` or to drop the skip of `agent:manual`. `uv run ruff check .`, `uv run mypy .`, `uv run pytest -q` and the plugin's tests pass.

## Edge cases

- Empty: an issue with no `## Files likely touched` section gets no extra file; guarded files stay refused.
- Large data: an issue that lists 50 paths passes 50 lines; there is no limit.
- Permissions: an interactive session is not affected (the hook does nothing outside loop mode). A listed path does not open `.git/` or the guard keys of AC3.
- A change request on a pull request whose issue was edited after the build reads the issue as it is now.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Scope | The loop builds everything, but edits only the files the issue lists; other guarded files stay refused | Open everything (hook guards nothing); only existing tests | Drops the label and keeps the safety net |
| Q2 Settings that turn guards off | Always refused, even when listed | Allowed, caught in review | A build could switch off its own hooks mid-run |
| Q3 `agent:needs-permission` | Removed too; the hook allows the listed files | Keep it | Same cause, same fix |
| Q4 Review | `## Guard files changed` in task and epic pull requests | Nothing extra | The owner sees at once what touches the flow |
| Q5 First build | By hand once on the Mac mini (owner clicks Merge), with a probe of pushing a workflow file | Split for the loop | The loop cannot unlock its own guards |

## Design

Nothing visible to users.

## Open questions
