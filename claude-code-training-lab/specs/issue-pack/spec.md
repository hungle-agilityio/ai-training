# Spec: issue-pack

## Summary

Nothing visible to users of the app. The spec templates get a user story, Given/When/Then for user-visible ACs and a new `test-matrix.md`; each task names its matrix rows. The `write-issue` skill carries the same rules into the issue body and adds a zero-questions test before `agent:ready`. The Project instructions and a new ADR make these part of steps 3 and 5 and of the Definition of Ready.

## User story

As the owner, I want every spec to say who gains what, to show user-visible ACs as Given/When/Then and to plan the tests from the ACs before the build, so that the loop builds an issue no one has to ask about and I can see the planned tests in the spec pull request.

## Acceptance criteria

**Templates and skill (T1)**

- **AC1.** `docs/app/templates/spec/spec.md` has a `## User story` section right after `## Summary`, holding `As a <user>, I want <ability>, so that <goal>.` and a comment: one line per kind of user; work no user of the app sees names the person who gains (the owner, QA, the loop).
- **AC2.** The `## Acceptance criteria` guidance of that template says: an AC that describes what a person sees or does is written `**ACn.** Given <the starting data, with real names and numbers>, when <the action>, then <the exact result>.`; an AC about a function, a query, a file or a setting keeps the plain form. The example shows one AC of each form. Its line "Write the test rule as "every test on `main` passes unchanged"." is kept as it is.
- **AC3.** A new template `docs/app/templates/spec/test-matrix.md` starts with the comment `Copy to specs/<feature>/test-matrix.md.` and holds:
  - a table with the columns `Row`, `AC`, `Case`, `Check`, `Level`, `Test file`, `Task`, rows numbered M1, M2, ...;
  - `Case` is one of `normal`, `empty`, `edge`, `error`, `permission`, `narrow screen`; `Level` is one of `unit`, `integration`, `browser`, `manual`; `Check` is the Given/When/Then (user-visible) or the plain check (technical);
  - the rules: every AC has at least one row; every user-visible AC has a `normal` row and an `empty` row, or a row whose `Check` says `n/a: <why>`; a row's test file is the new test file named in its task; a check no test can make is `manual` and says the person's steps; the matrix is written at step 3 from the ACs, before any build, and is part of the spec pull request.
- **AC4.** `docs/app/templates/spec/tasks.md` gives every task a line `- **Matrix rows:** M1, M2` after `- **ACs:**`.
- **AC5.** `specs/README.md` lists `test-matrix.md` with one line (the tests planned per AC: case, level, test file, task) and says that `spec.md` holds the user story.
- **AC6.** `write-issue` (`SKILL.md`, section 7 "Handing an issue to the loop") says:
  - the issue Summary ends with the user story line from the spec (fast lane: written in the issue);
  - user-visible "Done when" ACs use the AC2 Given/When/Then form; technical ACs keep the plain form;
  - the issue has a `## Test matrix rows` section that copies its rows from `<specs_dir>/<feature>/test-matrix.md` (`paths.specs_dir`); on the fast lane it holds the small table itself, built by the AC3 rules;
  - **Zero-questions test**, before `agent:ready`: start a new sub-agent with no conversation context, give it only the issue body and read access to the repository, and ask it to list every question it would have to ask before it could build and test the issue; a fact it can find in the repository is not a question. Fix each question in the issue body (a decision goes to the user first), then run a new sub-agent on the changed body. The issue is ready only when a round returns 0 questions. The `Decisions` comment gets the line `Zero-questions test: 0 questions after <n> rounds (<k> in round 1).`
  The skill names no fixed layout path (`specs/<feature>`, `docs/app/templates`): `../plugins/agent-flow/tests/test_no_fixed_layout_paths.py` passes unchanged.
- **AC7.** `../plugins/agent-flow/.claude-plugin/plugin.json` version goes from `1.0.18` to `1.0.19` (`ops/check_plugin_version.py`).
- **AC8.** `ops/bootstrap.py` copies `test-matrix.md` with the rest of the spec templates: in a target made with `--no-labels` the file `docs/app/templates/spec/test-matrix.md` exists; in a target made with `--stack python` the file `docs/templates/spec/test-matrix.md` exists and names `docs/specs/<feature>/test-matrix.md`. No change to `ops/bootstrap.py` or `ops/bootstrap_manifest.toml` is needed.
- **AC9.** New tests go in `ops/tests/test_issue_pack_templates.py` and cover AC1 to AC6 and AC8. Every test on `main` passes unchanged; ruff, mypy and pytest pass.

**Project rules (T2, built by hand)**

- **AC10.** `.claude/knowledge/decisions/ADR-026-issue-pack-and-test-matrix.md` records the decision (context: Day 12 of the training, the gaps found on 2026-11-11; decision: AC1 to AC6 and AC11; rejected: Given/When/Then for every AC, a script on the Mac mini for the zero-questions test, a self-assessed checkbox, the matrix inside `tasks.md`, the verify report ticking rows). `.claude/knowledge/decisions/README.md` lists it.
- **AC11.** `.claude/project-instructions.md`:
  - step 3 full lane: the thread also writes `specs/<feature>/test-matrix.md` from `docs/app/templates/spec/test-matrix.md`; `spec.md` has the user story; user-visible ACs are Given/When/Then;
  - step 3 fast lane: the short spec adds the user story and the small test matrix;
  - step 5: each issue has the user story line in its Summary, its `## Test matrix rows`, and passes the zero-questions test before `agent:ready`;
  - Definition of Ready gains two lines: `- [ ] user story, and Given/When/Then for every AC users can see` and `- [ ] test matrix rows listed, and the zero-questions test returned 0 (rounds in the Decisions comment)`.
  After the merge the owner pastes the same text into Project settings (the thread gives the exact text).

## Edge cases

- Empty: a spec with no user-visible AC has no Given/When/Then and its matrix has no `empty` row; the matrix still has one row per AC.
- Large data: an epic with many ACs keeps one matrix file; rows are grouped by task.
- Permissions: nothing changes; the zero-questions sub-agent only reads.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Where do the story and Given/When/Then apply? | The story line, plus Given/When/Then for user-visible ACs, in the spec template and the issue body | Every AC; also the CLI route (`feature.md`, `check_issue.py`) | Given/When/Then fits behaviour a person sees; for a function it only makes the line longer. The CLI route would change an existing test |
| Q2 How is zero-questions measured? | A fresh sub-agent reads the issue and the repo and must return 0 questions; rounds recorded in Decisions | A `claude -p` script on the Mac mini; a self-ticked checkbox | Measurable inside the thread, no new code, no run on the Mac mini |
| Q3 Where is the QA test matrix? | Its own file `specs/<feature>/test-matrix.md` in the spec pull request; each issue lists its rows; fast lane: a small table in the issue | Inside `tasks.md`; the matrix plus the verify report ticking rows | One place QA reads for the whole epic; the loop does not change |
| Q4 How far does it apply? | New requests in ai-training only | Also `agent-flow-starter` now | Try it here first, then copy to the template |

## Design

Nothing visible to users.

## Open questions
