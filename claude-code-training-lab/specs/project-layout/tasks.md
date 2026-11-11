# Tasks: project-layout

Epic. T2 and T4 can run in parallel after T1; they share no file. T3 follows T2 (both bump
`plugin.json`). T5 needs all four.

## Query budget

| Page | Queries on main | After T1 | After T2 | After T3 | After T4 | After T5 |
|---|---|---|---|---|---|---|
| (no page changes) | - | - | - | - | - | - |

## T1: Flow config finds .flow/ and has [paths]

- **ACs:** AC1, AC2, AC3
- **Files likely touched:** `ops/flow_config.py`, `ops/tests/test_flow_config_paths.py` (NEW)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: Plugin code reads the config of either layout

- **ACs:** AC4, AC5, AC6, AC7, AC8
- **Files likely touched:** `../plugins/agent-flow/hooks/before-edit-check.py`,
  `../plugins/agent-flow/hooks/before-finish-check.py`,
  `../plugins/agent-flow/hooks/before-github-command-check.py`,
  `../plugins/agent-flow/skills/create-issue/route_issue.py`,
  `../plugins/agent-flow/skills/build-verify-report/build_report.py`,
  `../plugins/agent-flow/skills/conftest.py`, `../plugins/agent-flow/.claude-plugin/plugin.json`,
  `../plugins/agent-flow/tests/test_layout_paths.py` (NEW)
- **Depends on:** T1
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T3: Plugin texts name folders by their config key

- **ACs:** AC9, AC10, AC10a, AC11
- **Files likely touched:** `../plugins/agent-flow/agents/*.md` (analyst, planner, implementer,
  reviewer), `../plugins/agent-flow/commands/` (plan, understand, review, learn),
  `../plugins/agent-flow/skills/` SKILL.md of grill-me, review-pull-request, write-issue, work-queue,
  create-issue, `../plugins/agent-flow/README.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`,
  `../plugins/agent-flow/tests/test_no_fixed_layout_paths.py` (NEW); the issue lists each file by path
- **Depends on:** T2
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T4: Loop scripts run from any folder

- **ACs:** AC12, AC13, AC14, AC15
- **Files likely touched:** `ops/start-loop.sh`, `ops/install-launchd.sh`, `ops/flow-value.sh`,
  `ops/agent_tick.py`, `ops/release.py`, `ops/epic_pull_request.py`, `ops/check_plugin_version.py`,
  `ops/pinned_tests.py`, `ops/tests/test_loop_location.py` (NEW)
- **Depends on:** T1
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T5: Bootstrap writes the new layout for any stack

- **ACs:** AC16 to AC25
- **Files likely touched:** `ops/bootstrap.py`, `ops/bootstrap_manifest.toml`,
  `ops/bootstrap_stubs/` (new stubs: `check-python.sh`, `check-node.sh`, `check-other.sh`,
  `gitignore-common`, `gitignore-python`, `gitignore-node`, `checks.yml`, `CLAUDE.md`,
  `architecture.md`, folder READMEs), `ops/BOOTSTRAP.md`,
  `ops/tests/test_bootstrap_layout.py` (NEW), plus the existing bootstrap tests the issue lists
- **Depends on:** T1, T2, T3, T4
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`
- **Note:** if the diff passes about 400 lines, split the stubs into a T5a before the issue is posted.

## After the epic (Project thread, not the loop)

- Rewrite Phase 4 of the kickoff instructions and the Notion page to the new layout.
- Re-lay out `o-living-with-nature` on the Mac mini on a branch with a pull request (Q6).
