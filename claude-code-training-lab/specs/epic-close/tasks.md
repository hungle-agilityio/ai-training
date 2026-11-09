# Tasks: epic-close

## T1: Stacked pull requests stay drafts until their base is main

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC12
- **Files likely touched:** `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_stack_draft.py` (NEW)
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`

## T2: The tick rescues a pull request merged into an epic branch

- **ACs:** AC6, AC7, AC8, AC9, AC10, AC12
- **Files likely touched:** `ops/epic_rescue.py` (NEW), `ops/agent_tick.py`, `ops/README.md`, `ops/tests/test_epic_rescue.py` (NEW)
- **Depends on:** T1 (both change `ops/agent_tick.py` and `ops/README.md`)
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:ready`

## T3: Note in ADR-021

- **ACs:** AC11 (the ADR part)
- **Files likely touched:** `.claude/knowledge/decisions/ADR-021-epic-branch.md`
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)
