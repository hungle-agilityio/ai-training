# Spec: flow-bootstrap

## Summary

Nothing visible to ReviewRadar users. The loop tooling (`ops/`, the hooks, `route_issue.py`) reads the project values from `ops/flow.toml` instead of constants, and a new `ops/bootstrap.py` copies the generic flow into a clone of a new, empty repository, renames it, creates the labels and `agent.env`, and prints the steps only the owner can do. With today's `ops/flow.toml` every message, path, name and command stays exactly as it is now.

## Acceptance criteria

### Config file (T1)

- **AC1.** `ops/flow.toml` exists, committed, with today's values:

  | Key | Value |
  |---|---|
  | `project.repo` | `hungle-agilityio/ai-training` |
  | `project.owner` | `hungle-agilityio` |
  | `project.app_dir` | `claude-code-training-lab` |
  | `project.display_name` | `ReviewRadar` |
  | `project.slug` | `reviewradar` |
  | `loop.state_dir` | `~/.reviewradar` |
  | `loop.tmux_session` | `rr-loop` |
  | `loop.launchd_label` | `com.reviewradar.loop` |
  | `loop.setup_command` | `["uv", "sync", "--frozen"]` |
  | `loop.alone_words` | `["migrations/", "models.py"]` |
  | `checks.commands` | `[["uv","run","ruff","check","."], ["uv","run","mypy","."], ["uv","run","pytest","-q","--no-cov","-p","no:cacheprovider"]]` |
  | `checks.ci_workflow` | `Checks` |
  | `checks.protected_test_dirs` | `["reviews/tests"]` |
  | `release.timezone` | `Asia/Ho_Chi_Minh` |
  | `release.deploy_line` | `Render deploys branch deploy after Checks pass.` |

- **AC2.** `ops/flow_config.py` has `load(path: Path | None = None) -> FlowConfig`, a frozen dataclass with one field per key. Without a path it reads `FLOW_CONFIG` from the environment if set, else `ops/flow.toml` next to the module. It uses `tomllib` (standard library only, no new dependency) and expands `~` in `loop.state_dir`.
- **AC3.** A missing key, an unknown key or a value of the wrong type raises `FlowConfigError` whose message names the file and the key, for example `ops/flow.toml: missing loop.tmux_session`. Nothing falls back to a hidden default (Q2).
- **AC4.** `python3 ops/flow_config.py <section.key>` prints the value on one line (a list as space-separated words) and exits 0; an unknown key prints the `FlowConfigError` message and exits 2. Shell scripts use this.

### Tick and loop scripts (T2)

- **AC5.** `ops/agent_tick.py` takes the repository, owner, app folder (worktree path and the file prefix of "Files likely touched"), display name (every message and the ntfy title), setup command, alone words and CI workflow name from `load()`. `ops/agent_tick.py` no longer contains the literals `hungle-agilityio`, `claude-code-training-lab`, `ReviewRadar`, `.reviewradar` or `"Checks"` (a test greps the file).
- **AC6.** With `project.app_dir = "."` the worktree root is the app folder and the file prefix is empty.
- **AC7.** The state folder is `FLOW_HOME` if set, else `REVIEWRADAR_HOME` if set (kept for today's tests and machine), else `loop.state_dir`.
- **AC8.** Every build the tick starts has both `FLOW_LOOP=1` and `REVIEWRADAR_LOOP=1` in its environment.
- **AC9.** `ops/start-loop.sh` and `ops/install-launchd.sh` take the tmux session, launchd label and state folder from `ops/flow_config.py`; `agent.env` is read from the state folder. `ops/agent.env.example` and `ops/README.md` say "the state folder from `ops/flow.toml` (`~/.reviewradar` for ReviewRadar)".
- **AC10.** With today's `ops/flow.toml`, every existing test in `ops/tests/` passes unchanged, and the messages are byte for byte the same as today (for example `ReviewRadar started #12: Add a filter`, `ReviewRadar PR #34 merged (#12)`).
- **AC11.** A new test with a second config (`acme/shop`, owner `acme-owner`, app folder `.`, name `Shop`, slug `shop`, tmux `shop-loop`) shows: messages start with `Shop `, the state folder is `~/.shop`, `gh` calls use `-R acme/shop` or `GH_REPO=acme/shop` as today's calls do for ReviewRadar, the worktree root is used for `uv sync`, and approvals are read from `acme-owner`.

### Release (T3)

- **AC12.** `ops/release.py` takes the time zone, the CI workflow name and the deploy line from `load()`; an empty `release.deploy_line` prints no deploy line. With today's config its output and refusals are unchanged (existing `ops/tests/test_release.py` passes unchanged).
- **AC13.** A new test with a second config (time zone `Europe/Berlin`, workflow `CI`, empty deploy line) shows the tag date in that zone, `gh run list --workflow CI`, and no deploy line.

### Hooks, skills and the decision record (T4, `agent:manual`)

- **AC14.** `before-finish-check.py` runs `checks.commands` from `ops/flow.toml`, in order, instead of its three fixed commands.
- **AC15.** `before-edit-check.py` protects existing tests under every folder in `checks.protected_test_dirs` (today `reviews/tests`), with the same message and `ALLOW_TEST_EDIT=1` escape as today.
- **AC16.** Every hook that checks loop mode treats `FLOW_LOOP=1` or `REVIEWRADAR_LOOP=1` as loop mode.
- **AC17.** `.claude/skills/create-issue/route_issue.py` takes its folder prefix from `project.app_dir` (`.` means no prefix).
- **AC18.** `github-allowed-repo.txt` stays the source for the GitHub guard; a new test fails if its first line differs from `project.repo` in `ops/flow.toml`.
- **AC19.** `ADR-019-flow-config-and-bootstrap.md` records `ops/flow.toml`, the copy-and-rename bootstrap and the decisions below; `.claude/knowledge/decisions/README.md` lists it; "Where things go" in `.claude/CLAUDE.md` gets one line: "Project values of the flow: `ops/flow.toml`".
- **AC20.** Every existing test in `.claude/hooks/tests/` and `.claude/skills/` passes unchanged.

### Bootstrap (T5)

- **AC21.** `uv run python ops/bootstrap.py --target <folder> --repo <owner/name> --owner <login> --app-dir <folder or .> --name <display name> --slug <slug> --ntfy-topic <topic> [--dry-run] [--no-labels]`. A missing value stops with one message listing every missing flag. A slug must match `^[a-z][a-z0-9-]{1,30}$`. The target must be a git clone whose `origin` points at `--repo` (https or ssh form); otherwise it refuses and says why.
- **AC22.** What is copied is listed in `ops/bootstrap_manifest.toml`, never inferred: `ops/` (tick, scripts, release, `flow_config.py`, `bootstrap.py`, `agent.env.example`, `README.md`, the tick and release tests), `.claude/hooks/` with their tests, `.claude/settings.json`, the skills `work-queue`, `grill-me`, `create-issue`, `write-issue`, `create-pull-request`, `draft-pull-request`, `build-verify-report`, `share-report`, `review-pull-request`, `create-commit`, the rules `workflow.md`, `git.md`, `security.md`, `issues.md`, `naming.md`, ADR-008 to ADR-019 and the decisions README, `docs/app/templates/spec/`, `specs/README.md`, `.claude/project-instructions.md`, and from the git root `CLAUDE.md`, `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`, `.github/workflows/checks.yml`. The app folder part goes under `<target>/<app-dir>/`.
- **AC23.** Bootstrap writes `<app-dir>/ops/flow.toml` with the six values and these defaults: `state_dir = "~/.<slug>"`, `tmux_session = "<slug>-loop"`, `launchd_label = "com.<slug>.loop"`, `setup_command = ["uv","sync","--frozen"]`, `alone_words = []`, the three `uv run` check commands of AC1, `ci_workflow = "Checks"`, `protected_test_dirs = ["tests"]`, `timezone = "Asia/Ho_Chi_Minh"`, `deploy_line = ""`. The file loads with `load()` (AC2).
- **AC24.** In every copied text file, bootstrap replaces `hungle-agilityio/ai-training` with the new repo, `claude-code-training-lab` with the new app folder (the `working-directory` of `checks.yml` becomes `.` when the app folder is `.`), `ReviewRadar` with the display name, `rr-loop` with the tmux session and the owner login with the new owner, and writes the new repo as the first line of `github-allowed-repo.txt`. A test greps the result: no copied file contains an old value unless it equals the new one.
- **AC25.** Bootstrap writes short stubs, each with headings and the line `TODO: fill in for <display name>`: `.claude/CLAUDE.md`, `.claude/rules/architecture.md`, `.claude/rules/domain.md`, and the coverage step of `checks.yml` removed.
- **AC26.** Unless `--no-labels`, bootstrap creates the 18 labels of the flow (`agent:ready`, `agent:running`, `agent:review`, `agent:failed`, `agent:manual`, `agent:needs-permission`, `pr:ready-for-review`, `pr:changes-requested`, `pr:blocked`, `pr:ci-failed`, `risk:low`, `risk:medium`, `risk:high`, `needs-ui`, `area:flow`, `area:app`, `epic`, `needs-info`) with `gh label create <name> --color <c> --description <d> --force -R <repo>`; colors and descriptions are in the manifest, copied from the labels on `hungle-agilityio/ai-training` today. A failed label is reported and the others still run.
- **AC27.** Bootstrap writes `~/.<slug>/agent.env` from `agent.env.example` with `AGENT_CONCURRENCY=1`, `NTFY_TOPIC=<topic>`, `CLAUDE_CODE_ENTRYPOINT=claude-desktop`, and `CLAUDE_CONFIG_DIR` copied from its own environment when set. An existing `agent.env` is never overwritten; bootstrap says so and goes on.
- **AC28.** Bootstrap never runs `git commit`, `git push` or any `gh` command other than `gh label create`, and never overwrites a file in the target: if any file it would write already exists, it lists all of them and stops before writing anything.
- **AC29.** At the end it prints numbered steps for the owner and the Claude session: (1) add the repo to the Mac mini fine-grained token and install the Claude GitHub App on it, (2) create the ruleset on `main` by hand, (3) `uv sync`, then the first commit and push of `main`, (4) create a Claude Project, attach the repo, paste `<app-dir>/.claude/project-instructions.md`, approve the folder for Remote Control, and start Remote Control sessions inside the app folder, (5) fill the stubs of AC25, (6) `bash ops/install-launchd.sh` once, (7) subscribe to the ntfy topic, (8) keep the total `AGENT_CONCURRENCY` of all loops on this Mac mini at 2 to 3.
- **AC30.** `--dry-run` prints the files it would write, the labels, the `agent.env` path and the steps of AC29, and writes nothing and runs no `gh`.
- **AC31.** Tests in `ops/tests/test_bootstrap.py` use temporary folders, a fake `gh` and a fake `HOME`; they never touch the network, the ReviewRadar repository or the real `~/.reviewradar`.

## Edge cases

- Empty: a new repository with no commits is the normal target; bootstrap writes into the working tree only.
- Large data: not applicable; about 150 files are copied.
- Permissions: `gh label create` fails without access to the repo; bootstrap reports which labels failed and the token step of AC29 explains why.
- Two loops: each slug has its own state folder, lock, tmux session, launchd label and ntfy topic, so the second loop never touches the first loop's files.
- Running bootstrap twice on the same target: the second run stops at AC28 because the files exist.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Stack of the new project | Any app stack; flow tooling stays Python with `uv`; copy only the generic flow plus stubs | Python/Django only, copy the Django parts | The Django parts are ReviewRadar's; check commands come from config |
| Q2 Config file | `ops/flow.toml` committed with today's values; a missing key stops with its name | Defaults in code, file only overrides | One visible source; no silent ReviewRadar defaults in a new project |
| Q3 Values bootstrap asks | 6: repo, owner, app folder, display name, slug, ntfy topic; the rest defaults in `flow.toml` | Also ask stack and check commands | Short prompt; defaults are edited later in one file |
| Q4 Effect on the target | Writes files, labels and `agent.env`, prints steps; never commits or pushes; `--dry-run` | Commit and push to `main` | The first push is checked by a person; no push to `main` by a script |
| Q5 Two loops on one Mac mini | Fully separate per slug; no shared limit; the steps say keep the total at 2 to 3 | A shared limit across loops | Smaller change; a shared limit can come later |
| Q6 `.claude/` work | One `agent:manual` task (T4) | Several manual tasks | One interactive session on the Mac mini |
| Q7 After the merge | Shorten section 4 of the Notion page to "run bootstrap.py with these 6 values"; no real project in this epic | Bootstrap a sample repository end to end | Keeps the epic small; the first real project is the end-to-end test |
| Where the config lives (spec) | `ops/flow.toml` | `flow.toml` at the app root | The loop may edit `ops/**`, so T1 to T3 can be `agent:ready` |
| Skills naming the repo (spec) | Renamed at copy time by bootstrap (AC24) | Editing every skill to use a placeholder | Fewer `.claude/` edits; the GitHub guard and allow rules keep exact repo names |
| Loop-mode variable (spec) | `FLOW_LOOP=1`, with `REVIEWRADAR_LOOP=1` still set and accepted | Rename only | Today's hooks, tests and docs keep working |

## Design

Nothing visible to users.

## Open questions
