# Spec: build-trust

## Summary

Nothing visible to users of the app. The loop build shows its plan in every pull request and, for a `risk:high` issue, stops after planning until the owner approves it. A new `test-author` sub-agent writes the failing tests from the issue and its matrix rows before the `implementer` writes code. The verify report gets a Test matrix axis that fails when a row has no passing test. Each task of a full-lane spec writes its build decisions to `specs/<feature>/decisions/T<k>.md` in its own pull request.

## User story

As the owner, I want to see and, on risky issues, approve the plan before code is written, to have tests written from the requirement by a separate agent and checked row by row against the test matrix, and to find every build decision next to the spec, so that I can trust a loop build without reading all of its code.

## Acceptance criteria

**Verify report: Test matrix axis (T1)**

- **AC1.** The criteria file of `build_report.py` accepts an optional `"matrix"` list; each entry has `row` (`M1`...), `ac`, `test` (`path::test_name`, or the manual steps for a `manual` row), `status` (`PASS`, `FAIL` or `MANUAL`) and `evidence`.
- **AC2.** The report has an axis `Test matrix`: `NOT APPLICABLE` when the criteria file has no `"matrix"` key (issues written before ADR-026 and issues without the section); `FAIL` when any entry has status `FAIL`, any status other than `PASS`, `FAIL` or `MANUAL`, or a `PASS` entry has an empty `test`; otherwise `PASS` with the evidence `<p> of <n> rows pass, <m> manual`. A `FAIL` on this axis makes the verdict `FAIL`, like the Issue axis.
- **AC3.** The report page shows a table with one line per matrix entry (Row, AC, Test, Status, Evidence) under the criteria table; the share page shows the same table. With no `"matrix"` key no table is shown.
- **AC4.** `build-verify-report` `SKILL.md` documents the `"matrix"` list and the axis.
- **AC5.** Plugin version `1.0.19` → `1.0.20` (`ops/check_plugin_version.py`). New tests in `../plugins/agent-flow/skills/build-verify-report/tests/test_matrix_axis.py`; every test on `main` passes unchanged.

**Build steps: plan, test author, decisions file (T2)**

- **AC6.** A new sub-agent `../plugins/agent-flow/agents/test-author.md` (role: builder of tests; `model: sonnet`): it reads only the issue body (its "Done when" ACs and `## Test matrix rows`), the rules and the code, never the plan or the implementer's work; it writes, in the new test file each row names, one test per row whose level is `unit` or `integration` (the test name says the behaviour, `rules/python.md`), runs them and reports which fail and why. A row whose level is `browser` or `manual` gets no test from it; the build checks it at verify. It never writes application code.
- **AC7.** `work-queue` section 2 order becomes: Analyse, Decide, **Plan** (`planner` for every difficulty; Easy gets its three lines: what to change, the test to write first, how to verify), **Plan stop** (AC8), **Tests** (`test-author`, when the issue has `## Test matrix rows`), **Build** (`implementer` makes those tests pass), Test, Review, Verify. After the `test-author` step the build commits its tests alone, with the title `Add the failing tests for #<N>`.
- **AC8.** **Plan stop.** When the issue has the label `risk:high` and no approved plan, the build, after Plan, posts one issue comment whose first line is `<!-- work-queue -->`, second line `<!-- plan -->`, then `## Plan` and the plan; it creates the label `agent:plan-review` if missing (`gh label create agent:plan-review --color 5319E7 --description "The loop posted a plan and waits for the owner's approval"`), sets `agent:plan-review`, removes `agent:running`, and ends the run with no branch pushed and no pull request. A plan is approved when the owner added `agent:ready` after the newest plan comment and wrote no comment after it other than an approval word (`lgtm`, `ok`, `duyệt`, `approved`, `approve`, `looks good`, `ship it`). Then the next run skips Plan and builds that plan. When the owner wrote any other comment after the newest plan comment, the run plans again with that comment as input and stops again the same way.
- **AC9.** `implementer.md`: it receives the plan and the `test-author`'s failing tests; it makes them pass and never deletes, skips or weakens them (removing an assertion, widening an expected value, marking `skip` or `xfail`). When a test is wrong against the issue, it may fix it only to match the issue's AC, and the pull request lists each such test under `## Tests changed after the test commit` with the AC and the reason. With no such change the section says `None`.
- **AC10.** The build writes the criteria file with one `"matrix"` entry per row of the issue's `## Test matrix rows` (AC1); an issue without that section writes no `"matrix"` key.
- **AC11.** `draft-pull-request`: every loop pull request body has a `## Plan` section, after What and before Why, holding the plan the build used, and for an approved plan the line `Approved by the owner on <YYYY-MM-DD> (<link to the plan comment>).` It also has the `## Tests changed after the test commit` section of AC9.
- **AC12.** **Decisions file.** When the issue's `## Files likely touched` lists a path `.../decisions/T<k>.md`, the build writes that file in its pull request with a heading `# Decisions during build: T<k> (#<N>)` and the table `| Question | Chosen | Rejected | Why | From |`, one line per decision taken in the build (an open point taken from the spec, a narrowest reading, a self-fix of this issue, the owner's answer to a `needs-decision` stop, the plan's assumptions); `From` is `owner` or `build`. With no decision the file holds the line `No decision beyond the issue.` In a round of change requests that changes behaviour, the build adds a line with `From` = `owner` and the comment link.
- **AC13.** `write-issue` section 7: an issue of a task of a full-lane spec lists its decisions file under `## Files likely touched` as `` `<specs_dir>/<feature>/decisions/T<k>.md` (NEW) `` (built from `paths.specs_dir`, no fixed layout path), and a `risk:high` issue says in its Summary that the build stops for plan approval. `../plugins/agent-flow/tests/test_no_fixed_layout_paths.py` passes unchanged.
- **AC14.** Plugin version `1.0.20` → `1.0.21`. New tests in `../plugins/agent-flow/tests/test_build_trust_texts.py` cover AC6 to AC13 (texts and the order of steps); every test on `main` passes unchanged, except the tests a pinned-test run lists in the issue.

**Tick: plan-review label (T3)**

- **AC15.** `ops/agent_tick.py`: `agent:plan-review` is in `SKIP_LABELS` and `LABEL_COLORS` (`5319E7`, the AC8 description). An issue with `agent:plan-review` is never started, even when it also has `agent:ready`.
- **AC16.** When a build ends with no pull request and the issue has `agent:plan-review`, the tick removes the worktree, says `issue-<N>: plan posted; waiting for the owner`, and sends one notification `ReviewRadar #<N> plan waits for your approval: <issue link>`; it records no failure.
- **AC17.** New tests in `ops/tests/test_tick_plan_review.py`; every test on `main` passes unchanged, except the tests a pinned-test run lists in the issue.

**Spec templates (T4)**

- **AC18.** `docs/app/templates/spec/spec.md` gets a section `## Decisions during build` after `## Decisions`, holding `See [decisions/](decisions/): one file per task, written by its build.`
- **AC19.** `docs/app/templates/spec/tasks.md`: the example `Files likely touched` of each task ends with `` `specs/<feature>/decisions/T<k>.md` (NEW) `` and its comment says why (AC12); the `Risk` line says `high: the build stops for plan approval`.
- **AC20.** `specs/README.md` lists `decisions/` (one file per task, written by its build, ADR-027).
- **AC21.** New tests in `ops/tests/test_build_trust_templates.py` cover AC18 to AC20; every test on `main` passes unchanged.

**Project rules (T5, built by hand)**

- **AC22.** `.claude/knowledge/decisions/ADR-027-plan-tests-and-build-decisions.md` records the decision (context: Day 13 of the training, the audit of 2026-11-11; decision: AC6 to AC20; rejected options of Q1 to Q5 below). `.claude/knowledge/decisions/README.md` lists it.
- **AC23.** `.claude/rules/workflow.md` Modes, loop mode: a `risk:high` issue stops after the plan with `agent:plan-review`; the owner's approval of that plan is Gate 1 of the build.
- **AC24.** `.claude/project-instructions.md`: step 5 adds the decisions file to each full-lane issue's files; the Status list names `agent:plan-review`; a new "Approve a plan" paragraph: when the owner approves a plan here, a thread posts `lgtm` on the issue and runs `gh issue edit <n> --add-label agent:ready --remove-label agent:plan-review` through Remote Control with the owner's login; a change to the plan is posted as a plain comment and then the same label change. After the merge the owner pastes the same text into Project settings (the thread gives the exact text).

## Edge cases

- Empty: an issue without `## Test matrix rows` gets no test-author step and a `NOT APPLICABLE` matrix axis; a task with no build decision still writes its decisions file with `No decision beyond the issue.`
- Large data: an epic with many tasks has one decisions file per task, so tasks built side by side never share a file.
- Permissions: only the owner's `agent:ready` approves a plan (the tick already starts only issues the owner labelled).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 How does a `risk:high` build wait for plan approval? | Plan posted as an issue comment, label `agent:plan-review`, the owner approves in the thread, the Mac mini posts `lgtm` and `agent:ready`, the next build uses that plan | No stop (plan only in the pull request); a stop for every Medium and Hard issue | Approval before code where the risk is, without slowing the rest of the loop |
| Q2 Which pull requests show the plan? | Every loop pull request; Easy gets three lines | Medium and Hard only | The owner always sees what the build meant to do |
| Q3 A matrix row with no passing test? | Test matrix axis `FAIL`, verdict `FAIL`, no pull request (`agent:failed`); no matrix = `NOT APPLICABLE` | A warning only | The matrix is only worth something when it is checked |
| Q4 Who writes the tests from the matrix? | A separate `test-author` sub-agent, before the code; the implementer may not weaken them | The implementer, as today | Tests written from the requirement, not from the code |
| Q5 Where do build decisions go? | `specs/<feature>/decisions/T<k>.md`, one file per task, in the build's pull request; `spec.md` links the folder | Edit `spec.md` (tasks of an epic would share a file); a spec pull request per decision from a thread (self-fixes missed) | The spec folder stays current and parallel tasks never share a file |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users.

## Open questions
