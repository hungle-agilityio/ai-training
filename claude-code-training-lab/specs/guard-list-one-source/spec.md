# Spec: guard-list-one-source

## Summary

A new module in the plugin, `plugins/agent-flow/hooks/guarded_paths.py`, holds the guarded-files rule. `before-edit-check.py` and `ops/epic_pull_request.py` both read it, so they cannot disagree. `flow.toml` (any folder) joins the guarded names. Nothing visible to users of the app.

## User story

As the owner, I want one source for the guarded-files rule, so that the hook and the epic pull request always agree.

## Acceptance criteria

- **AC1.** New module `../plugins/agent-flow/hooks/guarded_paths.py` (standard library only, no import from the project) defines the rule once: `PROTECTED_DIRS = {".github", ".claude"}`, `PROTECTED_FILES = {".mcp.json", "flow.toml"}`, `PLUGIN_DIRS = {"plugins", ".claude-plugin"}` (first folder from the git root) and `GATE_FILES` with exactly the 11 names of `main` (`pyproject.toml`, `uv.lock`, `conftest.py`, `ruff.toml`, `.ruff.toml`, `mypy.ini`, `.mypy.ini`, `setup.cfg`, `pytest.ini`, `tox.ini`, `.coveragerc`), and one function `guarded_kind(parts: tuple[str, ...]) -> str | None` that takes the casefolded path parts from the git root and returns `"rule"` (a part in `PROTECTED_DIRS`, or a last part in `PROTECTED_FILES`), `"plugin"` (first part in `PLUGIN_DIRS`), `"gate"` (last part in `GATE_FILES`), or `None`, checked in that order.
- **AC2.** `../plugins/agent-flow/hooks/before-edit-check.py` imports the four names and `guarded_kind` from `guarded_paths.py` in its own folder and defines none of them itself. Every refusal message, the `.claude/knowledge/` new-file exception, the `FLOW_ALLOWED_EDITS` allow and the protected-test rule stay as on `main`.
- **AC3.** `ops/epic_pull_request.py` loads `guarded_paths.py` from `paths.plugin_dir` of the flow config (relative to the app folder) and defines no guard list of its own (`GUARD_DIRS`, `GUARD_NAMES`, `PLUGIN_ROOTS`, `GATE_FILES` are gone). `guarded(status, path, test_dirs)` is True when `guarded_kind` returns a kind, or for a changed (not added) file under a protected test folder, as on `main`.
- **AC4.** When `guarded_paths.py` cannot be found or loaded, `ops/epic_pull_request.py` fails closed: `guarded` is True for every path, so `## Guard files changed` lists every changed file; it does not raise.
- **AC5.** Given a loop build (`FLOW_LOOP=1`) whose issue does not list `ops/flow.toml`, when it tries to edit `ops/flow.toml`, then the hook refuses with `flow.toml is a rule file; the loop never changes its own rules, ask the user`. Given the issue lists it (`FLOW_ALLOWED_EDITS`), the edit is allowed, as for every guarded file (ADR-023). The same holds for `.flow/flow.toml`.
- **AC6.** Given a pull request whose diff changes `claude-code-training-lab/ops/flow.toml`, when the tick writes its `## Guard files changed` section, then the section lists that path.
- **AC7.** A parity test: for each path of a fixed list (one per kind: `.claude/rules/git.md`, `.github/workflows/checks.yml`, `.mcp.json`, `ops/flow.toml`, `.flow/flow.toml`, `plugins/agent-flow/hooks/hooks.json`, `.claude-plugin/marketplace.json`, `pyproject.toml`, `uv.lock`, `reviews/conftest.py`, plus the unguarded `reviews/services.py` and `ops/agent_tick.py`), the hook in loop mode with no allowed edits refuses exactly when `epic_pull_request.guarded("M", path, [])` is True.
- **AC8.** `plugin.json` of the plugin gets the next patch version above the one on `main` (`ops/check_plugin_version.py` passes); the hook's docstring names `guarded_paths.py` and `flow.toml`.
- **AC9.** New tests in `../plugins/agent-flow/hooks/tests/test_guarded_paths.py` (AC1, AC2, AC5) and `ops/tests/test_guard_list_one_source.py` (AC3, AC4, AC6, AC7). Every test on `main` passes unchanged.
- **AC10.** `.claude/knowledge/decisions/ADR-023-*.md`: the consequence "The guard rules are written twice ... A change to one is copied to the other." is replaced by "The guard rules live once, in `plugins/agent-flow/hooks/guarded_paths.py`; the hook and `ops/epic_pull_request.py` read it, and `flow.toml` is guarded (#486, 2026-11-12)." (built by hand, `.claude/` exception).

## Edge cases

- Empty: a diff with no guarded file gives the `## Guard files changed` section of `main` (no change).
- Large data: no change; one module load per tick.
- Permissions: the module is inside the plugin, which the loop cannot edit unless an issue lists it.
- A new-layout project (`.flow/plugin`, ADR-025): `paths.plugin_dir` points there, so the same code finds the module.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Where does the one list live? | A module in the plugin (`hooks/guarded_paths.py`) | `ops/flow.toml`; two copies plus a parity test | The plugin is guarded, so the loop cannot change its own guards; `flow.toml` was not guarded (owner, 2026-11-12) |
| Q2 Guard `flow.toml` in this task? | Yes, `flow.toml` in any folder | A separate issue | It holds `checks.protected_test_dirs`; one name more (owner, 2026-11-12) |
| Module missing in `ops/` | Fail closed: every changed file listed | Raise and stop the tick | Security rule: guards fail closed; a missing plugin must not hide guard files |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users.

## Open questions
