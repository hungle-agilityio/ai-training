# Tasks: test-harden

One epic. T1 → T2 (both change `plugin.json`, and T2 calls the script of T1). T3, T4 and T5 run side by side with T1 (no shared file). T1 to T5 are `agent:ready` and merge into the epic branch; the owner reviews the one epic pull request. T6 changes files under `.claude/` and is built by hand on `main` after the epic merges (ADR-023, "Exception: .claude/"); the owner clicks Merge.

## Query budget

No page changes.

## T1: Sensitive paths and the review level

- **ACs:** AC1, AC2, AC3, AC4
- **Matrix rows:** M1 to M5
- **Files likely touched:** `ops/flow_config.py`, `ops/flow.toml`, `../plugins/agent-flow/skills/work-queue/review_level.py` (NEW), `../plugins/agent-flow/.claude-plugin/plugin.json`, `ops/tests/test_flow_config_review_sensitive.py` (NEW), `../plugins/agent-flow/skills/work-queue/tests/test_review_level.py` (NEW), `specs/test-harden/decisions/T1.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T2: /code-review in every build and on the epic

- **ACs:** AC5, AC6, AC7, AC8, AC9, AC10
- **Matrix rows:** M6 to M12
- **Files likely touched:** `../plugins/agent-flow/skills/work-queue/SKILL.md`, `../plugins/agent-flow/skills/draft-pull-request/draft_pr.py`, `../plugins/agent-flow/skills/draft-pull-request/SKILL.md`, `../plugins/agent-flow/.claude-plugin/plugin.json`, `../plugins/agent-flow/tests/test_code_review_texts.py` (NEW), `../plugins/agent-flow/skills/draft-pull-request/tests/test_code_review_section.py` (NEW), `specs/test-harden/decisions/T2.md` (NEW)
- **Depends on:** T1
- **Risk:** medium (changes every loop build)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T3: The tick starts the epic review

- **ACs:** AC11, AC12, AC13, AC14
- **Matrix rows:** M13 to M16
- **Files likely touched:** `ops/agent_tick.py`, `ops/tests/test_tick_epic_review.py` (NEW), `specs/test-harden/decisions/T3.md` (NEW)
- **Depends on:** none
- **Risk:** medium (the hand-over of every epic)
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T4: Browser regression of the main screens in CI

- **ACs:** AC15, AC16, AC17
- **Matrix rows:** M17 to M19
- **Files likely touched:** `ops/regression_screens.json` (NEW), `../.github/workflows/checks.yml`, `ops/tests/test_regression_screens.py` (NEW), `specs/test-harden/decisions/T4.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T5: Client-facing pull requests in the release

- **ACs:** AC18, AC19, AC20
- **Matrix rows:** M20 to M22
- **Files likely touched:** `ops/release.py`, `ops/tests/test_release_client_facing.py` (NEW), `specs/test-harden/decisions/T5.md` (NEW)
- **Depends on:** none
- **Risk:** low
- **needs-ui:** no
- **Label:** `agent:ready`, `area:flow`

## T6: ADR-029 and the Project rules

- **ACs:** AC21, AC22, AC23
- **Matrix rows:** M23 to M25
- **Files likely touched:** `.claude/knowledge/decisions/ADR-029-test-and-harden.md` (NEW), `.claude/knowledge/decisions/README.md`, `.claude/rules/workflow.md`, `.claude/project-instructions.md`
- **Depends on:** T1, T2, T3, T4, T5 (after the epic merges)
- **Risk:** low
- **needs-ui:** no
- **Label:** none (built by hand, `.claude/` exception), `area:flow`
