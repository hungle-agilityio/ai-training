# Spec: depends-heal

## Summary

Nothing visible to users of ReviewRadar. Four changes to the flow: (1) the tick reads `Depends on #N` and `Part of the epic #N` anywhere in an issue body; (2) `route_issue.py` refuses an issue whose dependency line it cannot read, and the issue templates put `Depends on` on its own line with base tasks created first; (3) a build whose dependency is not merged into its base releases the issue and waits, without `agent:failed`; (4) the next tick heals an `agent:failed` issue by itself, at most 3 heal rounds per issue, never in the forbidden cases. Recorded as ADR-034, an exception to team principles 1 and 4 that widens ADR-024.

## User story

As the owner, I want the loop to read every dependency and to fix a failed task by itself, so that a task never runs before its base task and the flow never waits for me.

## Acceptance criteria

**Reading the dependency (T1)**

- **AC1.** `depends_on()` in `ops/agent_tick.py` returns every `#N` that follows `Depends on` up to the end of that line, wherever `Depends on` stands in the line (case-insensitive, word boundary). `"Part of the epic #104. Depends on #107."` gives `{107}`; `"Depends on #63, #61 (both change settings.py)\nDepends on #7\nSee #99"` still gives `{63, 61, 7}`; `"Depends on: none"` gives an empty set; a body without `Depends on` gives an empty set.
- **AC2.** `epic_number()` in `ops/epic_branch.py` finds `Part of the epic #N` anywhere in a line: `"Some text. Part of the epic #104. Depends on #107."` gives `104`. The first match in the body wins, as today.
- **AC3.** Given epic #104 with T1 #107 (`agent:ready`) and T2 #105 whose body has `Part of the epic #104. Depends on #107.` on one line, when the tick chooses, then #107 is started and #105 is not (it waits until #107 has `agent:in-epic`), whatever their numbers or creation times.

**Checking before posting (T2)**

- **AC4.** `route_issue.py` prints one line `Depends on: #107, #108` (numbers in body order, no duplicates) or `Depends on: none` on stderr for every body it routes, using the same rule as AC1.
- **AC5.** `route_issue.py` prints `NOT ROUTED: ...` and exits 1 when (a) a line holds `Depends on` but no `#N` and not the word `none`, or (b) the body has `Part of the epic #N` and no `Depends on` line at all. The message names what to write: `Depends on #<n>.` or `Depends on: none`.
- **AC6.** The `write-issue` and `create-issue` skills and `docs/app/templates/spec/tasks.md` say: every task of an epic has its own line `Depends on #<n>.` (or `Depends on: none`) directly under `Part of the epic #N`, and the issues of an epic are created in dependency order, base tasks first. The plugin version goes up by one patch.

**Waiting for a base task (T3)**

- **AC7.** The `work-queue` skill, before planning an issue build, checks every `Depends on #M` of the issue: it is met when #M is closed, or, for a task of an epic, when #M has `agent:in-epic`. When one is not met, the build writes no code, adds a line `Depends on #M.` to the issue body when the body has no line the AC1 rule reads it from, posts one comment whose first lines are `<!-- work-queue -->` and `<!-- waiting -->` naming the unmet issues, sets `agent:ready`, removes `agent:running` and ends without a pull request.
- **AC8.** The tick treats a build that ended that way (the issue has `agent:ready`, no `agent:running`, no pull request) as ended normally: no `agent:failed`, no failure record, no retry or heal counted, no ntfy message. The issue is held by AC3 at the next tick.

**Healing a failed issue (T4)**

- **AC9.** At each tick, an open issue with `agent:failed` and without `agent:ready` whose failure record kind is `decision` or `stopped` (or that has no record) and that has fewer than 3 heal starts gets a heal run: prompt `Use the work-queue skill for issue #<n> only: heal.`. Heal runs are chosen before ready issues, oldest failure first, within the free slots. A heal run ignores the file-overlap guard and the issue's dependencies (it changes no file in the repository). The tick counts heal starts per issue in its state folder (`heals/<n>`); the count stays when the issue is restarted and leaves only when the issue is closed.
- **AC10.** A `transient` failure keeps today's retries (`RETRIES = 3`) and gets no heal run. A `transient` failure that used all its retries gets heal runs like a `stopped` one.
- **AC11.** The `work-queue` skill gets a section `## Heal`. The heal run reads the issue body, every comment with the `<!-- work-queue -->` marker (the stop reasons and their choices), the spec linked from the issue, the `Decisions` comment and the epic's other issues. It picks the option the stop comment recommends, else the narrowest reading that meets every AC, else the recommended option in the spec. It edits the issue body (ACs, `## Files likely touched`, `## Existing tests that change`, `Depends on`, test matrix rows) and posts one comment whose first lines are `<!-- work-queue -->` and `<!-- heal -->`, then a `## Decisions` table (what stopped, what changed, why). It sets `agent:ready`, removes `agent:failed` and ends without a pull request. It writes no code and pushes nothing.
- **AC12.** Forbidden for a heal run: deleting files or data; a migration or any change to stored data; anything about security, secrets, permissions or sign-in; a setting or file that turns a guard off, or a file under `.claude/`; deleting, skipping or weakening a test beyond the new number an AC needs; a query count that grows with the data. When the only way forward is forbidden, the heal run posts a comment whose first lines are `<!-- work-queue -->`, `<!-- heal -->` and `<!-- needs-owner -->` with the reason and the choices, and keeps `agent:failed`; the tick then starts no more heal runs for that issue and sends one ntfy message.
- **AC13.** After the 3rd heal start of an issue, a new failure sends one ntfy message `<name> #<n> failed after 3 heals, needs you: <link>` and the tick starts no more heal runs for it. In both AC12 and AC13 the tick keeps building every issue that does not depend on it. The owner restarts it by adding `agent:ready` as today.
- **AC14.** A heal comment counts like a self-fix comment: the healed issue is started before other ready issues (as fail-fix AC7), and the epic pull request body (`ops/epic_pull_request.py`) and a loop pull request outside an epic list each heal comment under `## Self-decided fixes` next to the self-fix comments.

**The rules (T5, built by hand)**

- **AC15.** ADR-034 records: dependencies are read anywhere and checked before posting; a build waits for an unmet base task; heal runs with the AC12 forbidden list and the 3-round cap; it is an exception to team principle 1 (a heal run may change the issue within AC11 and AC12) and to team principle 4 (3 heal rounds, each followed by one build). ADR-024 gets a line pointing to ADR-034; `rules/workflow.md` principles 1 and 4 point to it; `decisions/README.md` lists ADR-034; `.claude/CLAUDE.md` "Removed, and why" records that a `needs-decision` stop no longer waits for the owner.
- **AC16.** `.claude/project-instructions.md`: an epic task has its own `Depends on #<n>.` or `Depends on: none` line under "Part of the epic #N"; the issues of an epic are created base tasks first; `route_issue.py` must exit 0 (AC5) before an issue is posted.
- **AC17.** Every test on `main` passes unchanged except the tests each issue lists under `## Existing tests that change` (found with `ops/pinned_tests.py --unlisted` when the issue is written); `uv run ruff check .`, `uv run mypy .` and `uv run pytest -q` pass. Each task puts its tests in the new test file it names.

## Edge cases

- Empty: an issue without `Depends on` and outside an epic is routed and built as today.
- `Depends on` in prose that is not a dependency (for example "Depends on the weather"): AC5 refuses it; the writer rewrites the sentence or adds the numbers.
- A heal run that itself crashes or times out counts as a heal start (AC9), so a broken heal cannot loop for ever.
- Owner restarts by hand after 3 heals: the count is not reset; a new failure goes straight to the owner (AC13).
- Two failed issues and one free slot: the older failure heals first; the other waits one tick.
- Permissions: heal runs use the same `gh` login and hooks as builds; they cannot edit repository files.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 What a heal run may decide | Everything except the forbidden list (AC12) | Everything; technical only (ADR-024 as today) | The flow is not blocked for most stops, and steps that cannot be undone still go to the owner |
| Q2 Heal rounds per issue | 3, then park with one ntfy; the rest of the queue goes on | 1; no limit | Same as `RETRIES = 3`; no endless loop and no burnt 5-hour plan |
| Q3 Task started before its base task | The build checks and releases to `agent:ready` with a waiting comment, no failure | Also read the spec's `tasks.md` from the tick | The parser fix and the posting check cover it; `tasks.md` T-numbers are not issue numbers and its folder differs per layout |
| Q4 Starter and O - Living | Both, one pull request each through the Mac mini after T1 to T5 merge | Hotfix O - Living now; only this repository and the starter | #105 and #106 were fixed by hand, so O - Living is not blocked now |
| Where the posting check lives | `route_issue.py` | `check_issue.py` | The project instructions already run it on every issue body |
| Dependency order of creation | Written in the skills and templates; the parser makes the order harmless | Enforced in code | The tick holds a dependent issue whatever its number once AC1 holds |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users.

## Open questions
