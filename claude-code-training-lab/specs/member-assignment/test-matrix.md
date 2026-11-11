# Test matrix: member-assignment

Written from the ACs of `spec.md` before any build. No AC is seen by users of the app; the flow's empty cases (no assignee, owner only, no epic member) are `edge` rows.

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | The issue list asks for `assignees`; the member is the first non-owner login, else the open `epic` issue's first non-owner login, else none | unit | `ops/tests/test_tick_member_assignment.py` | T1 |
| M2 | AC2 | normal | Given #500 `agent:ready` assigned to `alice`, when a tick runs, then #500 is not started and the log has `issue-500: assigned to alice; skipped` | unit | same | T1 |
| M3 | AC2 | edge | Given #500 assigned only to `hungle-agilityio`, or to nobody, when a tick runs, then #500 starts as on `main` | unit | same | T1 |
| M4 | AC3 | normal | Given epic #600 assigned to `alice` and task #601 assigned to the owner only, when a tick runs, then #601 is skipped with `assigned to alice (epic #600)` | unit | same | T1 |
| M5 | AC3 | edge | Given task #602 of epic #600 assigned to `bob`, the log names `bob`, not `alice` | unit | same | T1 |
| M6 | AC4 | normal | Given #500 with `alice` removed and `agent:ready` kept, the next tick starts it | unit | same | T1 |
| M7 | AC5 | normal | Given #500 `agent:running` then assigned to `alice`, the build is not stopped, the line is logged and one notification is sent; a second tick sends none | unit | same | T1 |
| M8 | AC6 | edge | A member's `agent:failed` issue is not retried; a member's `agent:ready` issue does not count as ready for "queue empty" or the waiting list | unit | same | T1 |
| M9 | AC7 | normal | Given PR #610 without the marker, `Closes #601`, merged into `epic/600-<slug>`, #601 gets `agent:in-epic`, loses `agent:ready`, once; the tick never merges an unmarked pull request | unit | same | T1 |
| M10 | AC8 | normal | Given #603 `Depends on #601` and #601 `agent:in-epic` from M9, the tick starts #603 on the epic branch | unit | same | T1 |
| M11 | AC9, AC10 | normal | `ops/README.md` has `## Team members` after `## The epic pull request` with the claim, give-back and hand-off commands; every test on `main` passes | unit | same, and full `pytest` run | T1 |
| M12 | AC11 | normal | ADR-028 exists with context, decision and rejected options; the decisions README lists it | manual | Owner reads the hand-built pull request | T2 |
| M13 | AC12 | normal | `workflow.md` loop mode names the member skip and ADR-028 | manual | Owner reads the hand-built pull request | T2 |
| M14 | AC13 | normal | Project instructions show the member in Status and have the "Assign" paragraph | manual | Owner reads the hand-built pull request and pastes the text into Project settings | T2 |
