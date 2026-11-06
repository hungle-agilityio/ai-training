# Tasks: epic-branch

## T1: Record the epic branch and let builds use it

- **ACs:** AC13, AC14
- **Files likely touched:** `.claude/knowledge/decisions/ADR-021-epic-branch.md`, `.claude/knowledge/decisions/README.md`, `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/skills/create-pull-request/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `../plugins/agent-flow/tests/test_epic_branch_texts.py` (NEW)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/` and the plugin)

## T2: The tick keeps one branch per epic

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC6
- **Files likely touched:** `ops/epic_branch.py` (NEW), `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_epic_branch.py` (NEW)
- **Depends on:** none
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:ready`

## T3: Epic tasks start on the epic branch

- **ACs:** AC7, AC8, AC9, AC10, AC11, AC12, AC15
- **Files likely touched:** `ops/agent_tick.py`, `ops/tests/test_epic_stacked_start.py` (NEW)
- **Depends on:** T1, T2
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:ready`
