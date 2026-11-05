# Tasks: flow-bootstrap

T1 comes first. T2, T3 and T4 depend only on T1 and share no file, so they can run side by side. T5 depends on T2 (it copies the parametrised tick). T4 changes `.claude/`, so it is `agent:manual` and is built in one interactive session on the Mac mini. Every task is `area:flow`. New tests go in new test files; no existing test is edited.

## T1: Read the flow's project values from ops/flow.toml

- **ACs:** AC1 to AC4
- **Files likely touched:** `ops/flow.toml` (NEW), `ops/flow_config.py` (NEW), `ops/tests/test_flow_config.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

## T2: Tick and loop scripts read ops/flow.toml

- **ACs:** AC5 to AC11
- **Files likely touched:** `ops/agent_tick.py`, `ops/start-loop.sh`, `ops/install-launchd.sh`, `ops/agent.env.example`, `ops/README.md`, `ops/tests/test_tick_flow_config.py` (NEW)
- **Depends on:** T1
- **Risk:** high (the tick runs every build; AC10 keeps today's behaviour)
- **needs-ui:** no
- **Label:** `agent:ready`

## T3: Release reads ops/flow.toml

- **ACs:** AC12, AC13
- **Files likely touched:** `ops/release.py`, `ops/tests/test_release_flow_config.py` (NEW)
- **Depends on:** T1
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

## T4: Hooks and route_issue read ops/flow.toml; ADR-019

- **ACs:** AC14 to AC20
- **Files likely touched:** `.claude/hooks/before-finish-check.py`, `.claude/hooks/before-edit-check.py`, `.claude/hooks/before-github-command-check.py`, `.claude/hooks/before-commit-check.py`, `.claude/hooks/tests/test_flow_config_hooks.py` (NEW), `.claude/skills/create-issue/route_issue.py`, `.claude/skills/create-issue/tests/test_route_issue_flow_config.py` (NEW), `.claude/knowledge/decisions/ADR-019-flow-config-and-bootstrap.md` (NEW), `.claude/knowledge/decisions/README.md`, `.claude/CLAUDE.md`
- **Depends on:** T1
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)

## T5: ops/bootstrap.py sets up a new repository

- **ACs:** AC21 to AC31
- **Files likely touched:** `ops/bootstrap.py` (NEW), `ops/bootstrap_manifest.toml` (NEW), `ops/bootstrap_stubs/CLAUDE.md` (NEW), `ops/bootstrap_stubs/architecture.md` (NEW), `ops/bootstrap_stubs/domain.md` (NEW), `ops/BOOTSTRAP.md` (NEW), `ops/tests/test_bootstrap.py` (NEW)
- **Depends on:** T2
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`
- **Note:** may pass 400 lines with its tests; if so, the build splits the manifest and stubs into a first commit.

## After all are merged (not an issue)

1. A thread shortens section 4 of the Notion page "Những gì cần cho một dự án mới" to "run `ops/bootstrap.py` with these 6 values" and keeps the callout that tells Claude to ask for the 6 values (Q7).
2. The owner pastes nothing new: `.claude/project-instructions.md` does not change in this epic.
