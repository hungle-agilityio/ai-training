# Test matrix: epic-review-checklist

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | `body_for` for epic #9 with one task gives the section of AC1 directly after the task table and before the other sections. | unit | `ops/tests/test_epic_review_checklist.py` | T1 |
| M2 | AC2 | normal | A body with the first box ticked keeps it after `with_line`, `with_changes`, `with_self_fixes` and `with_guard_section`. | unit | `ops/tests/test_epic_review_checklist.py` | T1 |
| M3 | AC3 | empty | A body without the section stays without it after the same four rewrites. | unit | `ops/tests/test_epic_review_checklist.py` | T1 |
| M4 | AC4 | normal | The epic pull request opened by the tick (fake `gh`) has the section in its `--body-file`. | integration | `ops/tests/test_epic_review_checklist.py` | T1 |
| M5 | AC5 | normal | After the next release with an epic, the thread shows one table per epic and a card per `fail`. | manual | Ask "phát hành", choose A, read the thread. | T2 |
| M6 | AC5 | empty | A release without an epic says `No epic in this release; no live AC check.` | manual | Same, on a release without an epic. | T2 |
