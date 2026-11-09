# Tasks: epic-review-once

## T1: The tick merges task pull requests into the epic branch

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC14
- **Files likely touched:** `ops/agent_tick.py`, `ops/epic_branch.py`, `ops/README.md`, `ops/tests/test_epic_task_merge.py` (NEW)
- **Depends on:** none
- **Risk:** high
- **needs-ui:** no
- **Label:** built by hand on the Mac mini (owner clicks Merge)

## T2: The tick opens one pull request per epic into main

- **ACs:** AC8, AC9, AC10, AC11, AC12, AC14
- **Files likely touched:** `ops/epic_pull_request.py` (NEW), `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_epic_pull_request.py` (NEW)
- **Depends on:** T1 (both change `ops/agent_tick.py` and `ops/README.md`)
- **Risk:** high
- **needs-ui:** no
- **Label:** built by hand on the Mac mini (owner clicks Merge)

## T3: ADR-022 and the work-queue skill

- **ACs:** AC13 (ADR and skill part)
- **Files likely touched:** `.claude/knowledge/decisions/ADR-022-epic-reviewed-once.md` (NEW), `.claude/knowledge/decisions/ADR-021-epic-branch.md`, `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/` and the plugin), built by hand with T1
