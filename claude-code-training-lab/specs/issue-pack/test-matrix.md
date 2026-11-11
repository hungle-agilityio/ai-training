# Test matrix: issue-pack

Written from the ACs of `spec.md` before any build. No AC here is seen by users of the app, so every check is in the plain form and there are no `empty` rows.

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | `spec.md` template has `## User story` right after `## Summary`, with `As a <user>, I want <ability>, so that <goal>.` | unit | `ops/tests/test_issue_pack_templates.py` | T1 |
| M2 | AC2 | normal | Template states the Given/When/Then form for user-visible ACs and the plain form for technical ACs; the example has one of each; the "passes unchanged" line is still there | unit | `ops/tests/test_issue_pack_templates.py` | T1 |
| M3 | AC3 | normal | `test-matrix.md` template exists, starts with the copy comment, has the seven columns, the six cases, the four levels and the rules | unit | `ops/tests/test_issue_pack_templates.py` | T1 |
| M4 | AC4 | normal | Every `## T` entry of the `tasks.md` template has `- **Matrix rows:**` right after `- **ACs:**` | unit | `ops/tests/test_issue_pack_templates.py` | T1 |
| M5 | AC5 | normal | `specs/README.md` names `test-matrix.md` and the user story | unit | `ops/tests/test_issue_pack_templates.py` | T1 |
| M6 | AC6 | normal | `write-issue` section 7 names the user story, Given/When/Then, `## Test matrix rows`, `paths.specs_dir`, the zero-questions test and the Decisions line | unit | `ops/tests/test_issue_pack_templates.py` | T1 |
| M7 | AC6 | edge | The skill names no fixed layout path: the existing `test_no_fixed_layout_paths.py` passes unchanged | unit | `../plugins/agent-flow/tests/test_no_fixed_layout_paths.py` (existing, unchanged) | T1 |
| M8 | AC7 | normal | CI step `check_plugin_version.py` passes on the pull request with version `1.0.19` | manual | CI run of the pull request | T1 |
| M9 | AC8 | normal | Bootstrap with `--no-labels` gives `docs/app/templates/spec/test-matrix.md`; with `--stack python` gives `docs/templates/spec/test-matrix.md` naming `docs/specs/<feature>/test-matrix.md` | integration | `ops/tests/test_issue_pack_templates.py` | T1 |
| M10 | AC10 | normal | ADR-026 exists with context, decision and the five rejected options; the decisions README lists it | manual | Owner reads the hand-built pull request | T2 |
| M11 | AC11 | normal | Project instructions name `test-matrix.md`, the user story, Given/When/Then, the zero-questions test and the two new Definition of Ready lines | manual | Owner reads the hand-built pull request and pastes the text into Project settings | T2 |
