# Spec: project-layout

## Summary

A new project made by `ops/bootstrap.py` gets a stack-agnostic layout: code in `src/`, documents in
`docs/`, scripts in `scripts/`, the agent flow in `.flow/`. The flow (plugin, loop scripts, hooks)
finds its folders through `ops/flow.toml` or `.flow/flow.toml` instead of fixed paths, and every
default keeps ReviewRadar working as today. Nothing visible to users of any app.

## The layout of a new project

```
CLAUDE.md  README.md  .env.example  .gitignore  [render.yaml]  [stack root files]
.claude/           settings.json, rules/, knowledge/ (KNOWN_PITFALLS.md, BUSINESS_RULES.md),
                   project-instructions.md
.claude-plugin/    marketplace.json (plugin source ./.flow/plugin)
.flow/             flow.toml, loop/ (the loop scripts), plugin/ (agent-flow)
.github/           workflows/checks.yml, pull_request_template.md, ISSUE_TEMPLATE/
docs/              intent/, specs/, plans/, decisions/, templates/, architecture.md
src/<feature>/     code of one feature, with tests/ beside it
scripts/           check.sh, setup.sh
```

"Stack root files" are only the files a stack's tools need at the root: Python `pyproject.toml`,
`uv.lock` (Django also `manage.py`); Node `package.json`, the lock file, `tsconfig.json`; other: none.

## Acceptance criteria

**Flow config (T1)**

- **AC1.** `ops/flow_config.py` has a function that finds a project's config: `FLOW_CONFIG` when
  set, else `<project>/.flow/flow.toml` when it exists, else `<project>/ops/flow.toml`. The error for
  "none found" names both paths.
- **AC2.** `flow.toml` accepts an optional `[paths]` table with these keys; a missing key takes the
  default in the right column, which is ReviewRadar's layout today. A key of the wrong kind stops with
  the file and the key name, like the other tables.

  | Key | New layout (bootstrap writes) | Default (ReviewRadar) |
  |---|---|---|
  | `loop_dir` | `.flow/loop` | `ops` |
  | `plugin_dir` | `.flow/plugin` | `../plugins/agent-flow` |
  | `intent_file` | `docs/intent/{feature}.md` | `specs/{feature}/intent.md` |
  | `specs_dir` | `docs/specs` | `specs` |
  | `spec_pr_dirs` | `["docs/intent", "docs/specs"]` | `["specs", "design"]` |
  | `plans_dir` | `docs/plans` | `out/plans` |
  | `decisions_dir` | `docs/decisions` | `.claude/knowledge/decisions` |
  | `templates_dir` | `docs/templates` | `docs/app/templates` |
  | `code_dirs` | `["src"]` | `["reviews", "reviewradar"]` |
  | `flow_dirs` | `[".flow/", ".claude/", ".github/", "docs/intent/", "docs/specs/", "scripts/"]` | `["ops/", ".claude/", ".github/", "specs/", "docs/learning/"]` |

- **AC3.** `ops/flow.toml` of ReviewRadar is not changed, and `python3 ops/flow_config.py paths.<key>`
  prints the default for each key of AC2.

**Plugin code (T2)**

- **AC4.** The hooks `before-edit-check`, `before-finish-check` and `before-github-command-check`,
  `route_issue.py`, `build_report.py` and the skills' `conftest.py` find the config and
  `flow_config.py` through AC1: `.flow/flow.toml` with `<loop_dir>/flow_config.py` in a new project,
  `ops/` in ReviewRadar.
- **AC5.** `route_issue.py` gives `area:flow` when a path starts with one of `paths.flow_dirs` or the
  plugin folder (`paths.plugin_dir`), else `area:app`; with ReviewRadar's config its output is the same
  as today for every issue body.
- **AC6.** In a project whose `checks.protected_test_dirs` is `["tests"]`, `before-edit-check` treats
  `src/<feature>/tests/test_x.py` as a protected test (as today a `tests` folder at any depth matches).
- **AC7.** A test builds a fake new project (`.flow/flow.toml`, `.flow/loop/flow_config.py`, no `ops/`)
  in a temp folder and shows AC4 to AC6 in it; the same calls in this repository still read
  `ops/flow.toml`.
- **AC8.** The plugin version in `plugins/agent-flow/.claude-plugin/plugin.json` goes up.

**Plugin texts (T3)**

- **AC9.** No agent, command, skill or README text in the plugin names `.claude/knowledge/decisions`,
  `docs/app/templates` or `specs/<feature>` as a fixed path. Each says the folder by its key (for
  example "the decisions folder, `paths.decisions_dir` of the flow config") and, once, ReviewRadar's
  value as the example. `.claude/knowledge/KNOWN_PITFALLS.md` and `BUSINESS_RULES.md` stay fixed paths.
- **AC10.** The spec rule in the plugin texts reads: a spec pull request changes only `paths.spec_pr_dirs`.
- **AC11.** A test fails when a plugin text contains one of the three fixed paths of AC9. The plugin
  version goes up again.

**Loop scripts (T4)**

- **AC12.** `start-loop.sh`, `install-launchd.sh` and `flow-value.sh` work from any folder they are
  in: they find the project through the config of AC1 and call the scripts beside themselves, never
  `$LAB/ops/...`. In ReviewRadar the tmux command, the launchd plist and the messages are the same as
  today.
- **AC13.** `agent_tick.py`, `release.py`, `epic_pull_request.py` and `check_plugin_version.py` run as
  scripts from `.flow/loop/` with the standard library only (no `from ops import` needed), and name the
  config file they read in their errors.
- **AC14.** `check_plugin_version.py` reads the plugin folder from `paths.plugin_dir`; with ReviewRadar's
  config it checks `plugins/agent-flow/` as today.
- **AC15.** `pinned_tests.py` takes its test roots from `checks.protected_test_dirs` and
  `paths.plugin_dir`, and its app folders from `paths.code_dirs`; with ReviewRadar's config its output on
  the issue bodies of `ops/tests/` is the same as today.

**Bootstrap (T5)**

- **AC16.** A new flag `--stack python|node|other` (required). `--app-dir` must be `.` with the new
  layout; another value stops before writing anything and says why.
- **AC17.** Bootstrap writes exactly the layout above and nothing else at the root: no `ops/`,
  `plugins/`, `specs/`, `design/`, `tests/`, `in/`, `out/` or `docs/app/`. Each empty folder of `docs/`
  and `src/` gets a one-line `README.md` saying what goes in it.
- **AC18.** It copies the loop scripts (what `ops/` holds today except `bootstrap*`, `flow.toml` and
  `tests/`) into `.flow/loop/`, the plugin into `.flow/plugin/` with the renames of the kickoff guide
  (marketplace `<slug>`, plugin `agent-flow@<slug>`, version `1.0.0`), writes
  `.claude-plugin/marketplace.json` with source `./.flow/plugin`, and points `settings.json`
  (`extraKnownMarketplaces`, `enabledPlugins`) and `.flow/flow.toml` `[plugin]` at it.
- **AC19.** `.flow/flow.toml` has the `[paths]` values of the "New layout" column, `checks.commands =
  [["bash", "scripts/check.sh"]]` and `checks.protected_test_dirs = ["tests"]`. Per stack:

  | Stack | `loop.setup_command` | `loop.alone_words` | `scripts/check.sh` runs |
  |---|---|---|---|
  | python | `["uv", "sync", "--frozen"]` | `["migrations/"]` | `uv run ruff check .`, `uv run mypy .`, `uv run pytest -q` |
  | node | `["npm", "ci"]` | `["migrations/"]` | `npm run lint`, `npm run typecheck`, `npm test` |
  | other | `["bash", "scripts/setup.sh"]` | `[]` | a line that prints "TODO: add the checks of this stack" and exits 1 |

  `check.sh` stops at the first failing command (`set -euo pipefail`) and prints each command before it
  runs. For python, pytest's "no tests collected" (exit 5) counts as a pass with a warning line.
- **AC20.** `.gitignore` has a common part (`.env`, `.env.*` except `.env.example`, `in/`, `out/`,
  `.DS_Store`, `.playwright-mcp/`, `*.log`, `.claude/settings.local.json`) and the part of the stack
  (python: `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `db.sqlite3`,
  `staticfiles/`, `.coverage`; node: `node_modules/`, `dist/`, `coverage/`). `.env.example` is written
  with one comment line and no values.
- **AC21.** `.github/workflows/checks.yml` (workflow name `Checks`) runs on pull requests and pushes to
  `main` and `deploy`: it sets up the stack, runs `bash scripts/check.sh`, then the flow's own tests
  (`.flow/plugin` and `.flow/loop/tests`) and `check_plugin_version.py` with `uvx --from pytest`. No step
  names a path outside the repository.
- **AC22.** The root `CLAUDE.md` says in its first lines: product code is in `src/<feature>/` with tests
  beside it; documents in `docs/`; the agent flow in `.flow/` (do not change it in a feature task);
  `scripts/check.sh` is the one command that checks everything. `.claude/rules/architecture.md` stub
  says "by feature, not by layer".
- **AC23.** `grep -rn "ai-training\|reviewradar\|ReviewRadar\|claude-code-training-lab\|reviews/"` over
  the target after bootstrap returns nothing, and a test checks it on a fake target for each stack.
- **AC24.** `--dry-run` prints the tree it would write (one path per line) and writes nothing.
- **AC25.** `ops/BOOTSTRAP.md` describes the new flags and layout. Existing bootstrap tests that assert
  the old layout are listed in the issue under "Existing tests that change", old → new; every other test
  on `main` passes unchanged.

## Edge cases

- Empty: a new project with no feature yet has `src/README.md` only; `check.sh` (python) passes with
  the warning of AC19.
- Large data: not applicable.
- Permissions: the build may edit `.flow/` only when an issue lists the file (ADR-023), the same as
  `ops/` and the plugin today.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Scope | New projects only; paths in `flow.toml`, defaults = ReviewRadar | Move ReviewRadar too | ReviewRadar keeps working with no migration |
| Q2 Where the flow lives | Hidden `.flow/` (`loop/`, `plugin/`, `flow.toml`) | Visible `tools/`; keep `ops/` + `plugins/` | Flow is setup like `.claude/` and `.github/`; root shows only the product |
| Q3 Documents | `docs/{intent,specs,plans,decisions,templates}` + `architecture.md` | Keep `specs/` and `.claude/knowledge/decisions` | The owner's tree; one place for every document |
| Q4 Tests | Beside the feature, `src/<feature>/tests/`; any `tests` folder is protected | One root `tests/` | The owner's tree; the hook already matches `tests` at any depth |
| Q5 Stacks | `--stack`, one `scripts/check.sh` for CI and loop, gitignore per stack | Python only | Works for any stack with one entry point |
| Q6 `o-living-with-nature` | Re-laid out by a thread after the epic merges | Delete and restart; leave it | Keeps the work already done |
| Plugin not under `.claude/` (spec) | `.flow/plugin` | `.claude/plugins/` | A task that changes `.claude/` cannot be built by the loop (ADR-023) |

## Design

Nothing visible to users.

## Open questions
