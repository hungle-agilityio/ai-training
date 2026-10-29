# Tasks: pr-parallel-guard

## T1: Tick guards for shared files, every Depends on and a red main

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC6, AC7
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_tick_guards.py` (new)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`

## T2: Merge one at a time, the loop fixes conflicts on /redo, ADR-015

- **ACs:** AC8, AC9, AC10, AC11, AC12, AC13
- **Files likely touched:** `.claude/project-instructions.md`, `.claude/skills/work-queue/SKILL.md`, `.claude/knowledge/decisions/ADR-015-guards-for-parallel-pull-requests.md` (new), `.claude/knowledge/decisions/README.md`, `.claude/CLAUDE.md`, `docs/app/templates/spec/tasks.md`
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)

## Owner, once

- Switch on the ruleset on `main` with the steps in ADR-015 (AC12), after T2 is merged.
