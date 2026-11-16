# Test matrix: depends-heal

| Row | AC | Case | Check | Level | Test file | Task |
|---|---|---|---|---|---|---|
| M1 | AC1 | normal | `depends_on("Part of the epic #104. Depends on #107.")` is `{107}`; the multi-line body of `test_depends_on_reads_every_number_on_the_line` still gives `{63, 61, 7}` | unit | `ops/tests/test_tick_depends_anywhere.py` | T1 |
| M2 | AC1 | empty | `depends_on("Depends on: none")` and `depends_on("No dependency here")` are empty | unit | `ops/tests/test_tick_depends_anywhere.py` | T1 |
| M3 | AC2 | normal | `epic_number("Some text. Part of the epic #104. Depends on #107.")` is 104 | unit | `ops/tests/test_tick_depends_anywhere.py` | T1 |
| M4 | AC3 | edge | Epic #104, T2 #105 (older, `Depends on #107` mid-line), T1 #107 ready: `choose()` starts #107 only | integration | `ops/tests/test_tick_depends_anywhere.py` | T1 |
| M5 | AC4 | normal | Body with `Part of the epic #104.\nDepends on #107, #108.`: stderr has `Depends on: #107, #108`, exit 0 | unit | `../plugins/agent-flow/skills/create-issue/tests/test_route_depends.py` | T2 |
| M6 | AC4 | empty | Body outside an epic without `Depends on`: stderr has `Depends on: none`, exit 0 | unit | `../plugins/agent-flow/skills/create-issue/tests/test_route_depends.py` | T2 |
| M7 | AC5 | error | `Depends on the weather` (no number, no `none`) and an epic body with no `Depends on`: `NOT ROUTED`, exit 1 | unit | `../plugins/agent-flow/skills/create-issue/tests/test_route_depends.py` | T2 |
| M8 | AC6 | normal | The two skills and the tasks template contain the own-line rule and "base tasks first"; plugin version is one patch higher | unit | `../plugins/agent-flow/skills/create-issue/tests/test_route_depends.py` | T2 |
| M9 | AC7 | normal | The work-queue skill has the dependency check with the `<!-- waiting -->` comment, `agent:ready`, no code, no pull request | unit | `ops/tests/test_tick_waiting_release.py` | T3 |
| M10 | AC8 | edge | A build that ended with `agent:ready`, no `agent:running`, no pull request: no `agent:failed`, no record in `failed/`, no ntfy | integration | `ops/tests/test_tick_waiting_release.py` | T3 |
| M11 | AC9 | normal | Failed issue (kind `decision`) and an older ready issue, one slot: the heal run starts with prompt `... issue #<n> only: heal.`; `heals/<n>` is 1 | integration | `ops/tests/test_tick_heal.py` | T4 |
| M12 | AC9 | edge | A heal run starts while another running issue lists the same file and while its dependency is open | integration | `ops/tests/test_tick_heal.py` | T4 |
| M13 | AC10 | normal | Kind `transient` with 1 retry: retried, no heal; with 3 retries used: heal run | integration | `ops/tests/test_tick_heal.py` | T4 |
| M14 | AC11, AC12 | normal | The work-queue skill has `## Heal` with the reading order, the edit, the `<!-- heal -->` comment and the full forbidden list | unit | `ops/tests/test_tick_heal.py` | T4 |
| M15 | AC12 | edge | Newest heal comment has `<!-- needs-owner -->`: no heal run, one ntfy | integration | `ops/tests/test_tick_heal.py` | T4 |
| M16 | AC13 | edge | `heals/<n>` is 3 and the issue failed again: no heal run, one ntfy `failed after 3 heals`; another ready issue still starts | integration | `ops/tests/test_tick_heal.py` | T4 |
| M17 | AC14 | normal | A healed issue starts before an older ready issue; the epic pull request body lists the heal comment under `## Self-decided fixes` | integration | `ops/tests/test_tick_heal.py` | T4 |
| M18 | AC15 | manual | Read ADR-034, ADR-024, `workflow.md`, `decisions/README.md`, `.claude/CLAUDE.md`: each has the text of AC15 | manual | n/a: `.claude/` text, checked in the pull request | T5 |
| M19 | AC16 | manual | Read `.claude/project-instructions.md`: own-line rule, base tasks first, `route_issue.py` exit 0 | manual | n/a: `.claude/` text, checked in the pull request | T5 |
