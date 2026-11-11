# Tasks: build-trust

One epic. T1 → T2 (both change `plugin.json`), T3 and T4 side by side with T1 (no shared file). T1 to T4 are `agent:ready` and merge into the epic branch; the owner reviews the one epic pull request. T5 changes files under `.claude/` and is built by hand on `main` after the epic merges (ADR-023, "Exception: .claude/"); the owner clicks Merge. These tasks are written before ADR-027 is live, so they have no decisions file.

## Query budget

No page changes.

## T1: Test matrix axis in the verify report

- **ACs:** AC1, AC2, AC3, AC4, AC5
- **Matrix rows:** M1 to M5
- **Files likely touched:** `../plugins/agent-flow/skills/build-verify-report/build_report.py`, `../plugins/agent-flow/skills/build-verify-report/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `../plugins/agent-flow/skills/build-verify-report/tests/test_matrix_axis.py` (NEW)
- **Depends on:** none
- **Risk:** medium (the verdict that gates every pull request)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: Plan, test author and decisions file in the build

- **ACs:** AC6, AC7, AC8, AC9, AC10, AC11, AC12, AC13, AC14
- **Matrix rows:** M6 to M14
- **Files likely touched:** `../plugins/agent-flow/agents/test-author.md` (NEW), `../plugins/agent-flow/agents/implementer.md`, `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/skills/draft-pull-request/SKILL.md`, `../plugins/agent-flow/skills/write-issue/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `../plugins/agent-flow/tests/test_build_trust_texts.py` (NEW)
- **Depends on:** T1
- **Risk:** medium (changes every loop build)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T3: Tick knows agent:plan-review

- **ACs:** AC15, AC16, AC17
- **Matrix rows:** M15 to M17
- **Files likely touched:** `ops/agent_tick.py`, `ops/tests/test_tick_plan_review.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T4: Spec templates link the decisions files

- **ACs:** AC18, AC19, AC20, AC21
- **Matrix rows:** M18 to M21
- **Files likely touched:** `docs/app/templates/spec/spec.md`, `docs/app/templates/spec/tasks.md`, `specs/README.md`, `ops/tests/test_build_trust_templates.py` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T5: ADR-027 and the Project rules

- **ACs:** AC22, AC23, AC24
- **Matrix rows:** M22 to M24
- **Files likely touched:** `.claude/knowledge/decisions/ADR-027-plan-tests-and-build-decisions.md` (NEW), `.claude/knowledge/decisions/README.md`, `.claude/rules/workflow.md`, `.claude/project-instructions.md`
- **Depends on:** T1, T2, T3, T4 (after the epic merges)
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception), `area:flow`
