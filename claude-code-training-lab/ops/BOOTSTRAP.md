# Bootstrap a new repository

`ops/bootstrap.py` sets up the flow (loop, hooks, skills, specs, CI) in a clone of a new, empty
repository. Spec: `specs/flow-bootstrap/spec.md` (AC21 to AC31).

```
uv run python ops/bootstrap.py --target <folder> --repo <owner/name> --owner <login> \
    --app-dir <folder or .> --name <display name> --slug <slug> --ntfy-topic <topic> \
    [--dry-run] [--no-labels]
```

| Value | Meaning |
|---|---|
| `--target` | The clone of the new repository; its `origin` must point at `--repo` |
| `--repo`, `--owner` | `owner/name` of the repository and the owner's GitHub login |
| `--app-dir` | The folder of the app inside the repository, or `.` for the root |
| `--name`, `--slug` | Display name for messages; slug `^[a-z][a-z0-9-]{1,30}$` for the state folder `~/.<slug>`, tmux session `<slug>-loop` and launchd label `com.<slug>.loop` |
| `--ntfy-topic` | The ntfy.sh topic for the loop messages |

## What it does

- Copies what `ops/bootstrap_manifest.toml` lists (never inferred) and renames the old repository,
  app folder, display name, tmux session and owner in every text file.
- Writes `<app-dir>/ops/flow.toml` with the six values and the defaults, the three stubs
  (`.claude/CLAUDE.md`, `rules/architecture.md`, `rules/domain.md`, each with
  `TODO: fill in for <name>`), and removes the coverage step of `checks.yml`.
- Creates the 18 labels with `gh label create ... --force` (skip with `--no-labels`; a failed
  label is reported and the others still run).
- Writes `~/.<slug>/agent.env` from `ops/agent.env.example`; an existing one is kept.
- Prints the 8 steps only you can do. `--dry-run` prints the plan and writes nothing.

## What it never does

No `git commit`, no `git push`, no `gh` command but `gh label create`. If any file it would write
exists, it lists them all and stops before writing anything, so a second run on the same target
stops.
