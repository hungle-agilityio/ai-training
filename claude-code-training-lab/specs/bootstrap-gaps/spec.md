# Spec: bootstrap-gaps

## Summary

`ops/bootstrap.py` fixes the six gaps found in its test run, so a new project needs no hand fixes
after the printed steps. Nothing visible to users. Extends `specs/flow-bootstrap/spec.md`
(AC21 to AC31); every AC there still holds unless one below says otherwise.

## Acceptance criteria

**pyproject**

- **AC1.** When `<app-dir>/pyproject.toml` does not exist in the target, bootstrap writes one from
  `ops/bootstrap_stubs/pyproject.toml`: `name` = the slug, `requires-python = ">=3.11"`, no
  runtime dependencies, a `dev` dependency group with `pytest`, `ruff` and `mypy`,
  `[tool.uv] package = false`, ruff line length 100 with rules `E F I UP B`, mypy `strict = true`,
  pytest `testpaths = ["tests"]`.
- **AC2.** It also writes `<app-dir>/tests/__init__.py` and `<app-dir>/tests/test_flow_config.py`,
  a test that loads `ops/flow.toml` with `ops.flow_config.load()` and asserts its repo equals
  `--repo`, so `pytest` is never empty (an empty run exits 5 and turns CI red).
- **AC3.** When `<app-dir>/pyproject.toml` already exists, bootstrap does not write the files of
  AC1 and AC2, does not count it as a file that stops the run (AC28 of flow-bootstrap), and prints
  a step: add `pytest`, `ruff` and `mypy` to the dev dependencies and make sure `uv run pytest -q`
  finds at least one test.
- **AC4.** The step "Run uv sync, then make the first commit and push of main yourself" also says
  to commit the `uv.lock` that `uv sync` creates.

**Root CLAUDE.md**

- **AC5.** In the copied root `CLAUDE.md` the first heading is `# <repo name>` (the part of
  `--repo` after the slash), the first line names the app folder and the display name without the
  words "Django app", and every `@<path>` import line whose file bootstrap does not write is
  removed (today `rules/python.md`). Every other line is copied with the renames of AC24.

**Settings**

- **AC6.** The copied `.claude/settings.json` keeps no allow rule that names ReviewRadar's app:
  `Edit(./reviews/**)`, `Edit(./reviewradar/**)`, `Bash(uv run python manage.py:*)`, the two
  `.claude/skills/...` script rules and `Edit(//**/render.yaml)`. Every other rule is kept.
- **AC7.** The copied `env` has no `FLOW_COVERAGE_INCLUDE` and no `FLOW_COVERAGE_FAIL_UNDER` (the
  coverage step is already removed by AC25; the test-runner then reports the gate as not
  configured).
- **AC8.** A new optional flag `--code-dirs <a,b,...>` adds `Edit(./<dir>/**)` for each folder,
  in the given order. Each folder must be a relative path inside the app folder without `..`;
  otherwise bootstrap stops before writing anything and says why. `tests` is always added, even
  without the flag.
- **AC9.** Without `--code-dirs`, bootstrap prints a step: add an `Edit(./<folder>/**)` rule to
  `.claude/settings.json` for each code folder, or new issues will get `agent:needs-permission`.

**CI**

- **AC10.** `ops/tests/` is not copied (it checks ai-training's own values; 15 of its tests fail
  in a copy).
- **AC11.** The copied `.github/workflows/checks.yml` has no "Hook and skill tests" step. The other
  steps stay as AC24 and AC25 of flow-bootstrap leave them.

**Plugin paths**

- **AC12.** In the copied `.claude/project-instructions.md` and `.claude/rules/security.md`, no
  text contains `../plugins/`. The `route_issue.py` command reads: run `route_issue.py` of the
  installed agent-flow plugin's `create-issue` skill, from the skill's base directory, as one plain
  command (as PR #232 says in the SKILL.md files). The two other paths name the file inside the
  installed agent-flow plugin (`skills/share-report/rules.md`, `hooks/README.md`).
- **AC13.** In the copied `.claude/project-instructions.md`, `reviews/tests/` becomes `tests/`.

**Install step**

- **AC14.** The printed install step is
  `claude plugin install agent-flow@ai-training --scope project`; `ops/BOOTSTRAP.md` says the same.

**Proof**

- **AC15.** New tests in `ops/tests/test_bootstrap_gaps.py` cover AC1 to AC14 with temporary
  folders, a fake `gh` and a fake `HOME`, as AC31 of flow-bootstrap; they never use the network.
  The one assertion in `ops/tests/test_bootstrap.py` that expects "Hook and skill tests" in the
  copied workflow (`test_coverage_step_is_removed_from_the_checks_workflow`) is changed to expect
  it absent; no other existing test changes.
- **AC16.** The verify report shows one manual run on the Mac mini: bootstrap into a fresh
  temporary clone (`--app-dir .` and `--code-dirs src`), then in that folder `uv sync`,
  `uv run ruff check .`, `uv run mypy .`, `uv run pytest -q` all pass, and
  `route_issue.py` on a body that lists `src/app.py` prints `agent:ready`.

## Edge cases

- Empty: a target with only `.git` gets AC1 and AC2; a target with its own `pyproject.toml` keeps
  it (AC3).
- Large data: not applicable.
- Permissions: unchanged; labels still need the repo on the Mac mini token.
- `--app-dir web`: the files of AC1, AC2 and the `Edit` rules of AC8 are relative to `web/`.
- Running twice: still stops at AC28, now naming the stubbed `pyproject.toml` too.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Edit rules for the new project's code | optional `--code-dirs`, `tests` always, printed step otherwise | `Edit(./**)`; only remove and add by hand | Narrow rules keep `agent:needs-permission` meaningful; the flag saves a hand edit |
| Q2 `ops/tests` in a new project | not copied, "Hook and skill tests" step removed, one assertion of `test_bootstrap.py` changed | copy and make 15 tests pass in a copy | The flow is maintained in ai-training; its tests check ai-training's values |
| Q3 Target already has `pyproject.toml` | keep it, print a step | stop like any existing file | An existing Python project can still take the flow |
| Fix the source texts or the copy (AC12) | rewrite in the copy | edit `.claude/` here | Keeps the task out of `.claude/`, so the loop can build it |

## Design

Nothing visible to users.

## Open questions
