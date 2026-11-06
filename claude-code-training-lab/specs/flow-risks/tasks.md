# Tasks: flow-risks

## T1: CI fails when the plugin changes without a new version

- **ACs:** AC1, AC2, AC3
- **Files likely touched:** `.github/workflows/checks.yml`, `claude-code-training-lab/ops/check_plugin_version.py` (new), `claude-code-training-lab/ops/tests/test_check_plugin_version.py` (new)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.github/`)

## T2: The tick removes worktrees of closed work

- **ACs:** AC4, AC5, AC6, AC7
- **Files likely touched:** `claude-code-training-lab/ops/agent_tick.py`, `claude-code-training-lab/ops/README.md`, `claude-code-training-lab/ops/tests/test_tick_tidy_worktrees.py` (new)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`

## T3: The tick ends runs older than the time limit

- **ACs:** AC8, AC9
- **Files likely touched:** `claude-code-training-lab/ops/agent_tick.py`, `claude-code-training-lab/ops/README.md`, `claude-code-training-lab/ops/tests/test_tick_stale_runs.py` (new)
- **Depends on:** T2 (same files)
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`

## T4: The tick does not retry a build that needs a decision

- **ACs:** AC11, AC12, AC13
- **Files likely touched:** `claude-code-training-lab/ops/agent_tick.py`, `claude-code-training-lab/ops/README.md`, `claude-code-training-lab/ops/tests/test_tick_needs_decision.py` (new)
- **Depends on:** T3 (same files)
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

## T5: The work-queue skill marks a stop that needs a decision

- **ACs:** AC10, AC18
- **Files likely touched:** `plugins/agent-flow/skills/work-queue/SKILL.md`, `plugins/agent-flow/.claude-plugin/plugin.json` (version 1.0.3)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** as `route_issue.py` prints (`plugins/` has no loop allow rule today, so `agent:needs-permission`); built by hand if the owner prefers

## T6: The bootstrap template test is no longer collected

- **ACs:** AC14, AC15
- **Files likely touched:** `claude-code-training-lab/ops/bootstrap.py`, `claude-code-training-lab/ops/bootstrap_stubs/test_flow_config.py.stub` (renamed from `test_flow_config.py`), `claude-code-training-lab/ops/tests/test_bootstrap_stub_name.py` (new)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

## T7: Docs say 5 minutes; issues name the existing tests they change

- **ACs:** AC16, AC17
- **Files likely touched:** `claude-code-training-lab/.claude/CLAUDE.md`, `claude-code-training-lab/.claude/project-instructions.md`, `claude-code-training-lab/.claude/knowledge/decisions/ADR-014-tick-runs-builds-in-parallel.md`
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)
