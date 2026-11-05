# Spec: flow-plugin

## Summary

A Claude Code plugin `agent-flow` at `plugins/agent-flow/` (git root), listed by a marketplace
`ai-training` in `.claude-plugin/marketplace.json` (git root). It holds the 6 hooks, the 10 flow
skills, the 8 commands and the 5 sub-agents, with their tests. ReviewRadar turns it on in
`claude-code-training-lab/.claude/settings.json` and its own copies are removed (git history is the
archive). The tick updates the plugin once per tick. `ops/bootstrap.py` turns the plugin on in a new
project instead of copying those files. Nothing visible to app users.

## Acceptance criteria

Probe (T1)

- **AC1.** `plugins/agent-flow/.claude-plugin/plugin.json` (name `agent-flow`, version `0.1.0`,
  `license`), `plugins/agent-flow/README.md` and `.claude-plugin/marketplace.json` (name `ai-training`,
  one plugin with source `./plugins/agent-flow`) exist, and `claude plugin validate .` at the git root
  and `claude plugin validate plugins/agent-flow` both print "Validation passed".
- **AC2.** On the Mac mini, after `claude plugin marketplace add <git root>` and
  `claude plugin install agent-flow@ai-training`, a probe hook and a probe skill in the plugin are
  shown to fire in an interactive session and in `claude -p` started the way the tick starts builds
  (with `REVIEWRADAR_LOOP=1`); the README section "Probe" records the commands and their output.
- **AC3.** The README section "Probe" also records, with output: the absolute path the plugin has in
  the cache, whether that path changes with the version, and one Bash allow rule shape that lets
  `claude -p` run a script of a plugin skill without a prompt and does not allow any other script.
  If no such shape exists, it says so; T3 then keeps those scripts' rules as `ask`, never wider.
- **AC4.** The probe hook and skill are removed again before the pull request; the plugin then holds
  only `.claude-plugin/plugin.json`, `README.md` and `LICENSE`.

Hooks (T2)

- **AC5.** The 6 hooks and `.claude/hooks/tests/` move to `plugins/agent-flow/hooks/` with
  `git mv`; `plugins/agent-flow/hooks/hooks.json` registers the same events and matchers as the
  `hooks` block of `settings.json` today, each command as
  `/usr/bin/env python3 -I "${CLAUDE_PLUGIN_ROOT}/hooks/<file>.py"`.
- **AC6.** The hooks find `ops/flow.toml` and `ops/flow_config.py` under `$CLAUDE_PROJECT_DIR`
  (falling back to the payload `cwd`), not from their own folder. With no readable flow.toml a hook
  behaves as it does today when flow.toml cannot be read (same message).
- **AC7.** `before-github-command-check` takes the allowed repository from `project.repo` of
  flow.toml; `github-allowed-repo.txt` is removed. With today's flow.toml it allows and blocks
  exactly what it does today.
- **AC8.** `before-edit-check` in loop mode also blocks any path under `plugins/` and under
  `.claude-plugin/` at the git root, with the same message style as for `.claude/`.
- **AC9.** `claude-code-training-lab/.claude/settings.json` loses its `hooks` block and gains
  `extraKnownMarketplaces` (`ai-training`, source the GitHub repo `hungle-agilityio/ai-training`) and
  `enabledPlugins` `{"agent-flow@ai-training": true}`; `.claude/hooks/README.md` moves to
  `plugins/agent-flow/hooks/README.md`.
- **AC10.** The moved hook tests pass unchanged except the lines that locate files (paths and the
  repo file of AC7); every changed test line is listed in the pull request. New tests for AC6 to AC8
  are in a new file `plugins/agent-flow/hooks/tests/test_plugin_paths.py`.
- **AC11.** The "Hook and skill tests" step of `.github/workflows/checks.yml` runs
  `plugins/agent-flow/hooks/tests` instead of `.claude/hooks/tests`, and CI is green.
- **AC12.** `ops/bootstrap_manifest.toml` no longer lists `.claude/hooks`; in
  `ops/tests/test_bootstrap.py` only the lines that expect a copied hook or `github-allowed-repo.txt`
  (today lines 238, 277 and 340) change, to expect them absent; the pull request lists each line.
- **AC13.** Before the pull request is merged, the owner has installed the plugin on the Mac mini
  (the pull request lists the two commands); the pull request says so in "One concern".

Skills, commands, sub-agents (T3)

- **AC14.** The 10 flow skills (`work-queue`, `grill-me`, `create-issue`, `write-issue`,
  `create-pull-request`, `draft-pull-request`, `build-verify-report`, `share-report`,
  `review-pull-request`, `create-commit`) with their scripts and tests, the 8 commands and the
  5 sub-agents move to `plugins/agent-flow/{skills,commands,agents}/` with `git mv`.
- **AC15.** No moved file names ReviewRadar, Django, `reviews/`, `rounded_average` or
  `claude-code-training-lab`; where such a line gave a project rule, it now points to the project's
  `.claude/rules/` or `ops/flow.toml`. A test greps the plugin for these words.
- **AC16.** A skill calls its own script through the skill's folder (as found in AC2/AC3), never
  through `.claude/skills/`; the 6 allow rules in `settings.json` that name `.claude/skills/...`
  use the shape found in AC3 (or `ask`).
- **AC17.** `.claude/skills/` keeps only the app skills and `README.md`; `.claude/agents/` and
  `.claude/commands/` are removed; `.claude/skills/tests/test_skill_layout.py` checks both folders
  (edited for the new place, listed in the pull request).
- **AC18.** `checks.yml` runs the plugin's skill tests; CI is green; a session on the Mac mini lists
  `agent-flow:work-queue` once (no duplicate from the repository).
- **AC19.** `ops/bootstrap_manifest.toml` no longer lists the 10 flow skills; in
  `ops/tests/test_bootstrap.py` only the line that expects `.claude/skills/work-queue/SKILL.md`
  (today line 240) changes, to expect it absent. `.claude/CLAUDE.md` "Removed, and why" gets one row
  for the removed hook, skill, command and sub-agent copies.
- **AC20.** `plugins/agent-flow/.claude-plugin/plugin.json` version is `1.0.0`; `CLAUDE.md`,
  `rules/workflow.md` and `rules/git.md` name skills and commands as they now resolve.

Tick (T4)

- **AC21.** At the start of each tick, before any build, the tick runs
  `claude plugin marketplace update ai-training` and `claude plugin update agent-flow@ai-training`
  and logs the installed version once per tick.
- **AC22.** If either command fails or takes over 60 seconds, the tick logs it, sends one ntfy message
  per failure kind per hour, and goes on with the installed version; builds still start.
- **AC23.** The build prompts name `agent-flow:work-queue`. The plugin id and marketplace name come from
  a new `[plugin]` table in `ops/flow.toml` (`id = "agent-flow@ai-training"`,
  `marketplace = "ai-training"`); a missing key stops the tick with the key's name, like other keys. `ops/bootstrap.py` writes the
  same table into a new project's flow.toml, so `ops/tests/test_bootstrap.py` passes unchanged.
- **AC24.** Existing tick tests pass unchanged; new tests in `ops/tests/test_tick_plugin_update.py`.

Bootstrap (T5)

- **AC25.** `ops/bootstrap.py` writes into the target's `settings.json` the same
  `extraKnownMarketplaces` and `enabledPlugins` as AC9; an existing key in the copied file is replaced,
  other keys are kept.
- **AC26.** A dry run of bootstrap lists that settings change; a target never gets `.claude/hooks`,
  the 10 flow skills, `.claude/commands` or `.claude/agents`.
- **AC27.** The printed manual steps start with
  `claude plugin marketplace add hungle-agilityio/ai-training` and
  `claude plugin install agent-flow@ai-training`; `ops/BOOTSTRAP.md` says the same.
- **AC28.** New tests in `ops/tests/test_bootstrap_plugin.py`; existing tests pass unchanged.
- **AC29.** `.claude/knowledge/decisions/ADR-020-flow-as-a-plugin.md` (new file) records the
  decision table below and links this spec.

## Edge cases

- Plugin not installed on a machine: hooks do not run there. AC13 makes installing a step before the
  hooks pull request merges; bootstrap prints it first (AC27).
- Marketplace or GitHub down at tick start: AC22, the tick builds with the installed version.
- A pull request branch that changes the plugin: its builds and checks use the installed plugin
  from `main`, not the branch; the branch's own plugin tests still run in CI.
- Two projects on one Mac mini: one installed plugin version for both; each reads its own flow.toml
  through `$CLAUDE_PROJECT_DIR`.
- Permissions: the loop may not edit `plugins/` or `.claude-plugin/` (AC8); plugin tasks are
  `agent:manual`.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Where the plugin lives | This repo: `plugins/agent-flow/` + root marketplace | New repo `agent-flow` | Only this repo may be touched; one place to review |
| Q2 What goes in | Hooks, 10 flow skills, 8 commands, 5 sub-agents, made generic | Hooks and skills only | One package; bootstrap copies less |
| Q3 New versions on the Mac mini | Marketplace install; tick runs `plugin update` each tick | `--plugin-dir` from main; update by hand | Same route for loop and interactive sessions, works for every project |
| Q4 Who edits the plugin | `agent:manual`; hook blocks the loop | Loop may edit | The loop must not change its own guards |
| Q5 ReviewRadar | Moves to the plugin now; repo copies removed | Two copies side by side | One copy to keep in step |
| Spec: names | Plugin `agent-flow`, marketplace `ai-training` | `reviewradar-flow` | Generic name, matches the repo |
| Spec: probe first | T1 probes `claude -p`, cache path and allow rules on the Mac mini | Build straight away | Cloud probe could not run a signed-in `claude -p` |

## Design

Nothing visible to users.

## Open questions
