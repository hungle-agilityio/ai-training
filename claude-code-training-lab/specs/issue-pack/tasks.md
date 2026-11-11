# Tasks: issue-pack

Two tasks. T1 is built by the loop. T2 changes files under `.claude/` and is built by hand after T1 (ADR-023, "Exception: .claude/"); the owner clicks Merge.

## Query budget

No page changes.

## T1: Templates and write-issue carry the issue pack

- **ACs:** AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC9
- **Matrix rows:** M1 to M9
- **Files likely touched:** `docs/app/templates/spec/spec.md`, `docs/app/templates/spec/test-matrix.md` (NEW), `docs/app/templates/spec/tasks.md`, `specs/README.md`, `../plugins/agent-flow/skills/write-issue/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `ops/tests/test_issue_pack_templates.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: ADR-026 and the Project rules

- **ACs:** AC10, AC11
- **Matrix rows:** M10, M11
- **Files likely touched:** `.claude/knowledge/decisions/ADR-026-issue-pack-and-test-matrix.md` (NEW), `.claude/knowledge/decisions/README.md`, `.claude/project-instructions.md`
- **Depends on:** T1
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception), `area:flow`
