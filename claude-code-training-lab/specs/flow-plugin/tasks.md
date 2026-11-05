# Tasks: flow-plugin

All tasks: `area:flow`, needs-ui: no. T1, T2 and T3 change `plugins/` or `.claude/` and are built by
hand on the Mac mini (`agent:manual`); T4 and T5 are for the loop (`agent:ready`). The tasks run one
after the other: T2 and T3 share `settings.json` and `checks.yml`, T4 and T5 share `ops/bootstrap.py`. T2 and T3
also fix `ops/bootstrap_manifest.toml` and the named lines of `ops/tests/test_bootstrap.py`, so CI stays
green after each merge.

## T1: Plugin skeleton, marketplace and Mac mini probe

- **ACs:** AC1, AC2, AC3, AC4
- **Files likely touched:** `plugins/agent-flow/.claude-plugin/plugin.json` (NEW), `plugins/agent-flow/README.md` (NEW), `plugins/agent-flow/LICENSE` (NEW), `.claude-plugin/marketplace.json` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual`

## T2: Hooks move into the plugin

- **ACs:** AC5, AC6, AC7, AC8, AC9, AC10, AC11, AC12, AC13
- **Files likely touched:** `claude-code-training-lab/.claude/hooks/` → `plugins/agent-flow/hooks/` (all files), `plugins/agent-flow/hooks/hooks.json` (NEW), `plugins/agent-flow/hooks/tests/test_plugin_paths.py` (NEW), `claude-code-training-lab/.claude/settings.json`, `.github/workflows/checks.yml`, `claude-code-training-lab/ops/bootstrap_manifest.toml`, `claude-code-training-lab/ops/tests/test_bootstrap.py` (named lines only)
- **Depends on:** T1
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:manual`

## T3: Flow skills, commands and sub-agents move into the plugin

- **ACs:** AC14, AC15, AC16, AC17, AC18, AC19, AC20
- **Files likely touched:** the 10 flow skills under `claude-code-training-lab/.claude/skills/`, `claude-code-training-lab/.claude/commands/`, `claude-code-training-lab/.claude/agents/` → `plugins/agent-flow/`, `plugins/agent-flow/tests/test_generic_words.py` (NEW), `claude-code-training-lab/.claude/skills/tests/test_skill_layout.py`, `claude-code-training-lab/.claude/settings.json`, `claude-code-training-lab/.claude/CLAUDE.md`, `claude-code-training-lab/.claude/rules/workflow.md`, `claude-code-training-lab/.claude/rules/git.md`, `.github/workflows/checks.yml`, `claude-code-training-lab/ops/bootstrap_manifest.toml`, `claude-code-training-lab/ops/tests/test_bootstrap.py` (named line only)
- **Depends on:** T2
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual`

## T4: Tick updates the plugin each tick

- **ACs:** AC21, AC22, AC23, AC24
- **Files likely touched:** `claude-code-training-lab/ops/agent_tick.py`, `claude-code-training-lab/ops/flow_config.py`, `claude-code-training-lab/ops/flow.toml`, `claude-code-training-lab/ops/bootstrap.py`, `claude-code-training-lab/ops/tests/test_tick_plugin_update.py` (NEW)
- **Depends on:** T3
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:ready`

## T5: Bootstrap turns the plugin on instead of copying

- **ACs:** AC25, AC26, AC27, AC28, AC29
- **Files likely touched:** `claude-code-training-lab/ops/bootstrap.py`, `claude-code-training-lab/ops/BOOTSTRAP.md`, `claude-code-training-lab/ops/tests/test_bootstrap_plugin.py` (NEW), `claude-code-training-lab/.claude/knowledge/decisions/ADR-020-flow-as-a-plugin.md` (NEW)
- **Depends on:** T4
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`
