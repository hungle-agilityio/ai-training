# Tasks: app-prototype

The prototype itself is in this spec pull request (`design/app/`, AC1 to AC5). T1, T2 and T4 are `agent:ready` and run side by side (no shared file). T1 waits for test-harden T2 (#498): both change the plugin's `work-queue/SKILL.md` and `plugin.json`. T3 changes files under `.claude/` and is built by hand on `main` after test-harden T6 (#499) merges (ADR-023, "Exception: .claude/"); the owner clicks Merge. The security-check task ADR-031 waits for T3 (same `project-instructions.md`).

## Query budget

| Page | Queries on main | After T1 | After T2 | After T4 |
|---|---|---|---|---|
| `/dashboard/` | 5 | 5 | 5 | 5 |

## T1: Design vs build in the verify report

- **ACs:** AC6, AC7, AC8, AC9, AC10, AC11, AC12, AC13
- **Matrix rows:** M6 to M12
- **Files likely touched:** `../plugins/agent-flow/skills/build-verify-report/build_report.py`, `../plugins/agent-flow/skills/build-verify-report/design_capture.py` (NEW), `../plugins/agent-flow/skills/build-verify-report/SKILL.md`, `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/skills/write-issue/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `../plugins/agent-flow/skills/build-verify-report/tests/test_design_vs_build.py` (NEW), `specs/app-prototype/decisions/T1.md` (NEW)
- **Depends on:** test-harden T2 (#498)
- **Risk:** medium (every needs-ui build report)
- **needs-ui:** no (the report is not a page of the app)
- **Label:** `agent:ready`, `area:flow`

## T2: Spec templates name prototype states

- **ACs:** AC14, AC15
- **Matrix rows:** M13, M14
- **Files likely touched:** `docs/app/templates/spec/spec.md`, `docs/app/templates/spec/tasks.md`, `ops/tests/test_spec_templates_prototype.py` (NEW), `specs/app-prototype/decisions/T2.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T3: ADR-030 and the Project rules

- **ACs:** AC16, AC17, AC18
- **Matrix rows:** M15 to M17
- **Files likely touched:** `.claude/knowledge/decisions/ADR-030-app-prototype.md` (NEW), `.claude/knowledge/decisions/README.md`, `.claude/project-instructions.md`, `.claude/CLAUDE.md`
- **Depends on:** test-harden T6 (#499); T1, T2 (after they merge)
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception), `area:flow`

## T4: Dashboard fits a phone screen

- **ACs:** AC19, AC20, AC21
- **Matrix rows:** M18 to M20
- **Files likely touched:** `reviews/static/reviews/app.css`, `reviews/tests/integration/test_dashboard_narrow.py` (NEW), `specs/app-prototype/decisions/T4.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** yes
- **Screens to capture:** `/dashboard/` at 390 by 844 → `#location-scores` (design state `dashboard`); `/dashboard/` at 1280 by 800 → `.grid`
- **Label:** `agent:ready`, `area:app`
