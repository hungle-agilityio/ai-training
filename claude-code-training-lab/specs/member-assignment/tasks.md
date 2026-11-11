# Tasks: member-assignment

Two tasks, not an epic. T1 changes `ops/agent_tick.py`, which T3 #471 of the build-trust epic #468 also changes, so T1 depends on #468 (the epic issue closes when the epic pull request merges into `main`). T2 changes files under `.claude/`, two of which T5 #473 also changes, so it is built by hand on `main` after T1 and #473 (ADR-023, "Exception: .claude/"); the owner clicks Merge.

## Query budget

No page changes.

## T1: The loop skips issues assigned to a team member

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC9, AC10
- **Matrix rows:** M1 to M11
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_member_assignment.py` (NEW)
- **Depends on:** #468
- **Risk:** medium (which issues the loop starts)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: ADR-028 and the Project rules for member assignment

- **ACs:** AC11, AC12, AC13
- **Matrix rows:** M12 to M14
- **Files likely touched:** `.claude/knowledge/decisions/ADR-028-member-assignment.md` (NEW), `.claude/knowledge/decisions/README.md`, `.claude/rules/workflow.md`, `.claude/project-instructions.md`
- **Depends on:** T1, #473
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception), `area:flow`
