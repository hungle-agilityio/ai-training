# Tasks: depends-heal

Five tasks, plain issues (not an epic). T1 and T2 run in parallel (no shared file). T3 after T2 (both bump the plugin version). T4 after T1 and T3 (it changes `ops/agent_tick.py` and the `work-queue` skill after them). T5 by hand (`.claude/` files, ADR-023 exception) after T4. Then a follow-up outside this repository: one pull request for `agent-flow-starter` and one for `o-living-with-nature` through the Mac mini, and the Notion flow pages and the flow summary artifact updated (Q4).

## Query budget

No page changes.

## T1: Tick reads Depends on anywhere in the body

- **ACs:** AC1, AC2, AC3, AC17
- **Matrix rows:** M1, M2, M3, M4
- **Files likely touched:** `ops/agent_tick.py`, `ops/epic_branch.py`, `ops/README.md`, `ops/tests/test_tick_depends_anywhere.py` (NEW), `specs/depends-heal/decisions/T1.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: Refuse unreadable Depends on before posting

- **ACs:** AC4, AC5, AC6, AC17
- **Matrix rows:** M5, M6, M7, M8
- **Files likely touched:** `../plugins/agent-flow/skills/create-issue/route_issue.py`, `../plugins/agent-flow/skills/create-issue/SKILL.md`, `../plugins/agent-flow/skills/write-issue/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `docs/app/templates/spec/tasks.md`, `../plugins/agent-flow/skills/create-issue/tests/test_route_depends.py` (NEW), `specs/depends-heal/decisions/T2.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T3: Build waits for an unmerged base task

- **ACs:** AC7, AC8, AC17
- **Matrix rows:** M9, M10
- **Files likely touched:** `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `ops/tests/test_tick_waiting_release.py` (NEW), `specs/depends-heal/decisions/T3.md` (NEW)
- **Depends on:** T2
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T4: Next tick heals a failed issue

- **ACs:** AC9, AC10, AC11, AC12, AC13, AC14, AC17
- **Matrix rows:** M11, M12, M13, M14, M15, M16, M17
- **Files likely touched:** `ops/agent_tick.py`, `ops/epic_pull_request.py`, `ops/README.md`, `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/skills/create-pull-request/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `ops/tests/test_tick_heal.py` (NEW), `specs/depends-heal/decisions/T4.md` (NEW)
- **Depends on:** T1, T3
- **Risk:** high (the build stops for plan approval)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T5: ADR-034 and the issue-writing rule

- **ACs:** AC15, AC16
- **Matrix rows:** M18, M19
- **Files likely touched:** `.claude/knowledge/decisions/ADR-034-depends-and-heal.md` (NEW), `.claude/knowledge/decisions/ADR-024-loop-self-fix.md`, `.claude/knowledge/decisions/README.md`, `.claude/rules/workflow.md`, `.claude/CLAUDE.md`, `.claude/project-instructions.md`
- **Depends on:** T4
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception)
