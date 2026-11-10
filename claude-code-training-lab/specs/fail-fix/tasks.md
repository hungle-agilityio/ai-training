# Tasks: fail-fix

Four tasks. T1, then T2 (uses T1's `--unlisted`). T3 runs beside T2 (no shared file). T4 is built by hand (`.claude/` files, PR #401 exception) after T3.

## Query budget

No page changes.

## T1: Planning check sees every query cap

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC15
- **Files likely touched:** `ops/pinned_tests.py`, `ops/tests/test_pinned_query_caps.py` (NEW), `ops/tests/fixtures/pinned/issue-397.md` (NEW), `ops/tests/fixtures/pinned/issue-399.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: Tick checks pins and starts self-fixed issues first

- **ACs:** AC6, AC7, AC8, AC15
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_self_fix.py` (NEW)
- **Depends on:** T1
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T3: Build fixes technical stops itself

- **ACs:** AC9, AC10, AC11, AC12, AC15
- **Files likely touched:** `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/skills/create-pull-request/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `ops/epic_pull_request.py`, `ops/tests/test_epic_self_fixes.py` (NEW)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T4: ADR-024 and the planning rule

- **ACs:** AC13, AC14
- **Files likely touched:** `.claude/knowledge/decisions/ADR-024-loop-self-fix.md` (NEW), `.claude/knowledge/decisions/README.md`, `.claude/rules/workflow.md`, `.claude/project-instructions.md`
- **Depends on:** T3
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception)
