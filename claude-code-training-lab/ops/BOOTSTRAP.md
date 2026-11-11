# Bootstrap a new repository

`ops/bootstrap.py` sets up the flow (loop, hooks, skills, specs, CI) in a clone of a new, empty
repository. Spec: `specs/flow-bootstrap/spec.md` (AC21 to AC31), `specs/project-layout/spec.md`.

## The layout of a new project (`--stack`)

```
uv run python ops/bootstrap.py --target <folder> --repo <owner/name> --owner <login> \
    --name <display name> --slug <slug> --ntfy-topic <topic> --stack python|node|other \
    [--dry-run] [--no-labels]
```

With `--stack` the project gets the same small root for every stack; `--app-dir` is `.` and may be
left out (any other value stops before writing anything).

```
CLAUDE.md  README.md  .env.example  .gitignore  [pyproject.toml for python]
.claude/           settings.json, rules/, knowledge/ (KNOWN_PITFALLS.md, BUSINESS_RULES.md),
                   project-instructions.md
.claude-plugin/    marketplace.json (plugin source ./.flow/plugin)
.flow/             flow.toml, loop/ (the loop scripts), plugin/ (agent-flow)
.github/           workflows/checks.yml, PULL_REQUEST_TEMPLATE.md, ISSUE_TEMPLATE/
docs/              intent/, specs/, plans/, decisions/, templates/, architecture.md
src/<feature>/     code of one feature, with tests/ beside it
scripts/           check.sh, setup.sh
```

- **Product code** goes in `src/<feature>/`, its tests in `src/<feature>/tests/`; a `tests` folder
  at any depth is a protected test folder for the loop.
- **The flow** is all in `.flow/`: the loop scripts (what `ops/` holds here, without `bootstrap*`,
  `flow.toml` and `tests/`) in `.flow/loop/`, the plugin in `.flow/plugin/` (version `1.0.0`,
  without its own tests), listed by `.claude-plugin/marketplace.json` as `agent-flow@<slug>`, which
  `.claude/settings.json` turns on. The loop and the hooks read `.flow/flow.toml`, whose `[paths]`
  table names every folder (spec AC2).
- **One check command:** `scripts/check.sh` (`set -euo pipefail`, prints each command): python
  `uv run ruff check .`, `uv run mypy .` (skipped while `src/` has no Python code) and
  `uv run pytest -q` (no tests collected counts as a pass with a warning); node `npm run lint`,
  `npm run typecheck`, `npm test`; other a TODO that fails. The loop (`checks.commands`) and CI
  (`.github/workflows/checks.yml`) both run it; CI also runs `.flow/loop/check_plugin_version.py`.
- **`.gitignore`** holds a common part (`.env`, `.env.*` but `.env.example`, `in/`, `out/`,
  `.DS_Store`, `.playwright-mcp/`, `*.log`, `.claude/settings.local.json`) and the stack's part.
- Nothing else at the root: no `ops/`, `plugins/`, `specs/`, `design/`, `tests/`, `in/`, `out/` or
  `docs/app/`. Each empty folder of `docs/` and `src/` holds a one-line `README.md`, and no file
  names this repository's project.
- `--dry-run` prints the tree it would write, one path per line, and writes nothing.
- The steps it prints start with `claude plugin marketplace add <owner/name>` and
  `claude plugin install agent-flow@<slug> --scope project`, and say to run
  `bash .flow/loop/install-launchd.sh` once.

## Without `--stack`

The first projects were made without `--stack`; that layout is kept as it was and is described
below.

```
uv run python ops/bootstrap.py --target <folder> --repo <owner/name> --owner <login> \
    --app-dir <folder or .> --name <display name> --slug <slug> --ntfy-topic <topic> \
    [--code-dirs <a,b,...>] [--dry-run] [--no-labels]
```

| Value | Meaning |
|---|---|
| `--target` | The clone of the new repository; its `origin` must point at `--repo` |
| `--repo`, `--owner` | `owner/name` of the repository and the owner's GitHub login |
| `--app-dir` | The folder of the app inside the repository, or `.` for the root |
| `--name`, `--slug` | Display name for messages; slug `^[a-z][a-z0-9-]{1,30}$` for the state folder `~/.<slug>`, tmux session `<slug>-loop` and launchd label `com.<slug>.loop` |
| `--ntfy-topic` | The ntfy.sh topic for the loop messages |
| `--code-dirs` | Optional, comma-separated code folders inside the app folder (no `..`); each gets an `Edit(./<dir>/**)` allow rule, in that order. `tests` is always added. Without it a step tells you to add the rules by hand |

## What it does

- Copies what `ops/bootstrap_manifest.toml` lists (never inferred) and renames the old repository,
  app folder, display name, tmux session and owner in every text file.
- Writes `<app-dir>/ops/flow.toml` with the six values and the defaults, the three stubs
  (`.claude/CLAUDE.md`, `rules/architecture.md`, `rules/domain.md`, each with
  `TODO: fill in for <name>`), and removes the coverage step of `checks.yml`.
- Creates the 18 labels with `gh label create ... --force` (skip with `--no-labels`; a failed
  label is reported and the others still run).
- Writes `~/.<slug>/agent.env` from `ops/agent.env.example`; an existing one is kept.
- Turns the `agent-flow` plugin on: the copied `.claude/settings.json` gets `extraKnownMarketplaces`
  (`ai-training`, the `hungle-agilityio/ai-training` repository) and `enabledPlugins`
  (`agent-flow@ai-training`); other keys are kept. No hooks, flow skills, commands or sub-agents
  are copied.
- Prints the 10 steps only you can do; the first two install the plugin:
  `claude plugin marketplace add hungle-agilityio/ai-training`, then
  `claude plugin install agent-flow@ai-training --scope project`. `--dry-run` prints the plan and writes nothing.

## A project that works without hand fixes

Spec: `specs/bootstrap-gaps/spec.md`.

- Writes `pyproject.toml` (from `ops/bootstrap_stubs/pyproject.toml.stub`), `tests/__init__.py` and
  `tests/test_flow_config.py` (from `ops/bootstrap_stubs/test_flow_config.py.stub`) when the app folder has no `pyproject.toml`; an existing one is kept
  and a step says what to add.
- The root `CLAUDE.md` is about the new project and imports only files bootstrap writes.
- `.claude/settings.json` loses the allow rules and coverage env of ReviewRadar's app.
- `ops/tests/` is not copied and `checks.yml` has no "Hook and skill tests" step.
- Texts that pointed at `../plugins/` name the file inside the installed agent-flow plugin.

## What it never does

No `git commit`, no `git push`, no `gh` command but `gh label create`. If any file it would write
exists, it lists them all and stops before writing anything, so a second run on the same target
stops.
