# Tasks: loop-ux

## T1: The tick sends a message for every step that matters

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC17 (the ntfy list), AC18 (`ops/tests/test_tick_notify_cases.py`)
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_notify_cases.py` (new)
- **Depends on:** #68, #70, #72, #74 (all change `ops/agent_tick.py`)
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`

## T2: The loop marks each change request, and the rules say the tick merges

- **ACs:** AC12, AC13, AC14, AC15, AC16, AC18 (`.claude/hooks/tests/test_loop_review_marks.py`)
- **Files likely touched:** `.claude/skills/work-queue/SKILL.md`, `.claude/settings.json`, `.claude/hooks/before-github-command-check.py`, `.claude/hooks/tests/test_loop_review_marks.py` (new), `.claude/project-instructions.md`, `.claude/rules/git.md`, `.claude/rules/security.md`, `.claude/rules/workflow.md`, `.claude/CLAUDE.md`, `.claude/knowledge/decisions/ADR-016-tick-merges-on-owner-approval.md` (new), `.claude/knowledge/decisions/README.md`
- **Depends on:** #71, #76 (they change the same `.claude/` files)
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual`

## T3: The tick merges on the owner's approval and picks open change requests

- **ACs:** AC6, AC7, AC8, AC9, AC10, AC11, AC17 (approval words and marks), AC18 (`ops/tests/test_tick_merge.py`)
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_merge.py` (new)
- **Depends on:** T1 (same files), T2 (the loop must mark requests before the tick reads the marks)
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:ready`
