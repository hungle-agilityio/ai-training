# Test matrix: build-trust

Written from the ACs of `spec.md` before any build. No AC here is seen by users of the app, so every check is in the plain form and there are no `empty` rows; the empty cases of the flow (no matrix, no decision) are `edge` rows.

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1, AC2 | normal | Criteria with matrix entries all `PASS`/`MANUAL` give axis `PASS` with "<p> of <n> rows pass, <m> manual" | unit | `../plugins/agent-flow/skills/build-verify-report/tests/test_matrix_axis.py` | T1 |
| M2 | AC2 | error | One `FAIL` entry, an unknown status, or a `PASS` with empty `test` gives axis `FAIL` and verdict `FAIL` | unit | same | T1 |
| M3 | AC2 | edge | Criteria without a `"matrix"` key give axis `NOT APPLICABLE` and the verdict is unchanged | unit | same | T1 |
| M4 | AC3 | normal | Report and share HTML show the matrix table with each row; none without the key | unit | same | T1 |
| M5 | AC4, AC5 | normal | `SKILL.md` names `"matrix"` and the axis; `plugin.json` is `1.0.20` | unit | same | T1 |
| M6 | AC6 | normal | `agents/test-author.md` exists with role, `model: sonnet`, reads only issue, rules and code, one test per `unit`/`integration` row, never app code | unit | `../plugins/agent-flow/tests/test_build_trust_texts.py` | T2 |
| M7 | AC7 | normal | work-queue section 2 lists Plan, Plan stop, Tests, Build in that order; Plan for every difficulty; the test commit title | unit | same | T2 |
| M8 | AC8 | normal | work-queue names the `<!-- plan -->` marker, `agent:plan-review` with color and description, no push and no pull request, the approval rule and the re-plan rule | unit | same | T2 |
| M9 | AC9 | normal | `implementer.md` forbids deleting, skipping or weakening the tests and names `## Tests changed after the test commit` | unit | same | T2 |
| M10 | AC10 | normal | work-queue puts one `"matrix"` entry per `## Test matrix rows` row in the criteria file | unit | same | T2 |
| M11 | AC11 | normal | `draft-pull-request` has `## Plan` after What and before Why, the approval line, and the tests-changed section | unit | same | T2 |
| M12 | AC12 | normal | work-queue names the decisions file heading, table columns, `From` values and the `No decision beyond the issue.` line | unit | same | T2 |
| M13 | AC13 | edge | `write-issue` adds the decisions file from `paths.specs_dir`; `test_no_fixed_layout_paths.py` passes unchanged | unit | same, and `../plugins/agent-flow/tests/test_no_fixed_layout_paths.py` (existing, unchanged) | T2 |
| M14 | AC14 | normal | `plugin.json` is `1.0.21`; CI `check_plugin_version.py` passes | manual | CI run of the pull request | T2 |
| M15 | AC15 | normal | An issue with `agent:ready` and `agent:plan-review` is not chosen; the label color and description are set | unit | `ops/tests/test_tick_plan_review.py` | T3 |
| M16 | AC16 | normal | A build that ended with `agent:plan-review` and no pull request: worktree removed, the line and one notification, no failure record | unit | same | T3 |
| M17 | AC16 | edge | A build that ended with no pull request and no `agent:plan-review` behaves as on `main` | unit | same | T3 |
| M18 | AC18 | normal | `spec.md` template has `## Decisions during build` right after `## Decisions`, linking `decisions/` | unit | `ops/tests/test_build_trust_templates.py` | T4 |
| M19 | AC19 | normal | `tasks.md` template lists `decisions/T<k>.md` (NEW) in each task's files and says `high: the build stops for plan approval` | unit | same | T4 |
| M20 | AC20 | normal | `specs/README.md` names `decisions/` and ADR-027 | unit | same | T4 |
| M21 | AC21 | edge | Every test on `main` passes unchanged | integration | full `pytest` run | T4 |
| M22 | AC22 | normal | ADR-027 exists with context, decision and the rejected options; the decisions README lists it | manual | Owner reads the hand-built pull request | T5 |
| M23 | AC23 | normal | `workflow.md` loop mode names the plan stop and `agent:plan-review` | manual | Owner reads the hand-built pull request | T5 |
| M24 | AC24 | normal | Project instructions name the decisions file, `agent:plan-review` and "Approve a plan" | manual | Owner reads the hand-built pull request and pastes the text into Project settings | T5 |
