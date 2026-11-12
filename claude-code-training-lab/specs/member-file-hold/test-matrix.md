# Test matrix: member-file-hold

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | Given #509 (member alice, no labels) and ready #512 both listing `reviews/views.py`, when the tick picks issues, then #512 is not started and the log has `issue-512: waits for #509 (member alice), which also touches reviews/views.py`. | integration | `ops/tests/test_tick_member_files.py` | T1 |
| M2 | AC1 | edge | Same with #509 labelled `agent:ready`, `agent:failed` or `agent:in-epic`: #512 still waits. | integration | `ops/tests/test_tick_member_files.py` | T1 |
| M3 | AC2 | normal | `blocked_lines` counts #512 and gives `#512 waits for #509 (member alice), which also touches reviews/views.py`. | unit | `ops/tests/test_tick_member_files.py` | T1 |
| M4 | AC3 | normal | Epic #600 (member bob), task #601 listing `ops/release.py`, ready #605 listing it: log and waiting line name `(member bob, epic #600)`; with carol on #601 itself the line says `(member carol)`. | integration | `ops/tests/test_tick_member_files.py` | T1 |
| M5 | AC4 | normal | alice removed from #509, or #509 closed: #512 is started. | integration | `ops/tests/test_tick_member_files.py` | T1 |
| M6 | AC5 | edge | A path held by an `agent:running` issue and a member issue: the line has no member; two member issues: the lower number holds; a stacked or epic parent is ignored. | unit | `ops/tests/test_tick_member_files.py` | T1 |
| M7 | AC6 | empty | Member issue without `## Files likely touched` paths: #512 is started; the member issue is skipped with the line of `main`. | integration | `ops/tests/test_tick_member_files.py` | T1 |
| M8 | AC6 | empty | No open issue has a member: the issues started and the log equal those of `main` for the same fake issue list. | integration | `ops/tests/test_tick_member_files.py` | T1 |
| M9 | AC7 | normal | The fake `gh` records no call beyond those of the same tick without members. | integration | `ops/tests/test_tick_member_files.py` | T1 |
| M10 | AC8 | normal | `ops/README.md` `## Guards` has the member log line; `## Team members` has the bullet about held files. | unit | `ops/tests/test_tick_member_files.py` | T1 |
