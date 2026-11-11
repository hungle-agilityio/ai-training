# Spec: member-assignment

## Summary

Nothing visible to users of the app. The tick reads the assignees of each issue and of its epic. An issue whose own assignees, or whose epic's assignees, include a login other than the owner is a member's work: the tick never starts it, retries it or counts it as ready. A member claims, releases and hands off work only by changing the assignee. A member's pull request merged by hand into an epic branch sets `agent:in-epic` on the task it closes, like a loop pull request. `ops/README.md` explains the rule to members; ADR-028 and the Project rules record it.

## User story

As the owner, I want the loop to leave alone every task or epic I assign to a team member, so that a member and the loop never build the same issue and the team can share one board.
As a team member, I want to claim, give back or hand off a task by changing its assignee, so that I need no label or command the loop owns.

## Acceptance criteria

**Tick: member assignment (T1)**

- **AC1.** `open_issue_list` in `ops/agent_tick.py` also reads `assignees`. A *member* is any assignee login other than `OWNER`. The member of an issue is its first member assignee (sorted by login); when the issue has none and its `Part of the epic #N` line names an open issue labelled `epic` that has a member assignee, the issue's member is the epic's first member (sorted by login); otherwise it has none.
- **AC2.** Given issue #500 labelled `agent:ready` by the owner and assigned to `alice`, when a tick runs, then it does not start #500 and its log has the line `issue-500: assigned to alice; skipped`. Given #500 assigned only to `hungle-agilityio`, or to nobody, the tick starts it as on `main`.
- **AC3.** Given epic #600 (label `epic`) assigned to `alice` and task #601 (`agent:ready`, `Part of the epic #600`, assigned to `hungle-agilityio` only), when a tick runs, then it does not start #601 and logs `issue-601: assigned to alice (epic #600); skipped`. Given task #602 of the same epic assigned to `bob`, the tick logs `issue-602: assigned to bob; skipped` (the task's own member wins).
- **AC4.** Given #500 from AC2 with `alice` removed (no member left) and `agent:ready` still on it, when the next tick runs, then it starts #500 with no label change by anyone.
- **AC5.** Given #500 labelled `agent:running` (a build going) or `agent:review` and then assigned to `alice`, when a tick runs, then the build and its pull request go on unchanged, the log has `issue-500: assigned to alice while the loop builds it; the build goes on`, and one notification `ReviewRadar #500 is assigned to alice while the loop builds it: <issue link>` is sent once per issue and member (recorded in `<state dir>/member-claims`).
- **AC6.** An issue whose member is set is never retried as `agent:failed` (`retry_reason` is not reached) and is not counted as ready by the "queue empty" notice (`queue_empty`) or the waiting list (`#143 AC4`).
- **AC7.** Given open epic #600 with branch `epic/600-<slug>` and a pull request #610 without the work-queue marker, opened by any login, with `Closes #601` in its body, merged into that branch by hand, when a tick runs, then #601 gets `agent:in-epic` and loses `agent:ready`, `agent:running` and `agent:review`, once (recorded in `epic-tasks-merged` as on `main`), and the log has `pr-610: merged into epic/600-<slug>; #601 agent:in-epic`. The tick never merges a pull request without the marker (unchanged).
- **AC8.** Given loop task #603 (`Depends on #601`, same epic, no member), when #601 has `agent:in-epic` from AC7, then the tick starts #603 on the epic branch as for a loop dependency (ADR-022).
- **AC9.** New tests in `ops/tests/test_tick_member_assignment.py` cover AC1 to AC8; every test on `main` passes unchanged, except the tests a pinned-test run lists in the issue.

**Docs for members (T1)**

- **AC10.** `ops/README.md` has a section `## Team members` after `## The epic pull request`: the rule of AC1 to AC3; claim `gh issue edit <n> --add-assignee @me`; give back `gh issue edit <n> --remove-assignee @me` (the loop takes it at the next tick when it has `agent:ready`); hand off by `--remove-assignee @me --add-assignee <login>`; an epic is claimed the same way on the epic issue; claiming an issue the loop is building does not stop it (AC5), so check its `agent:running` / `agent:review` label first; a member's branch is `<kind>/<n>-<short-description>` and the pull request for a task of an epic goes into `epic/<N>-<slug>` with `Closes #<n>`, otherwise into `main`; the owner clicks Merge.

**Project rules (T2, built by hand)**

- **AC11.** `.claude/knowledge/decisions/ADR-028-member-assignment.md` records the decision (context: team work on one board, 2026-11-11; decision: AC1 to AC10; rejected options of Q1 to Q5 below). `.claude/knowledge/decisions/README.md` lists it.
- **AC12.** `.claude/rules/workflow.md` Modes, loop mode: the loop skips an issue whose member is set (ADR-028); a member's work follows the same branch, test and pull request rules by hand.
- **AC13.** `.claude/project-instructions.md`: the Status list shows each issue's member (or "loop"); a new "Assign" paragraph: when the owner asks here to give an issue or an epic to a member, take it back, or hand it off, a thread runs `gh issue edit <n> --add-assignee <login>` / `--remove-assignee <login>` through Remote Control with the owner's login. After the merge the owner pastes the same text into Project settings (the thread gives the exact text).

## Edge cases

- Empty: an issue with no assignee, or assigned only to the owner, is the loop's, exactly as on `main` (AC2). An epic with no member gives its tasks nothing (AC1).
- Large data: the tick reads assignees in the same `gh issue list` call (200 issues); no call per issue.
- Permissions: only the owner's `agent:ready` hands an issue to the loop (unchanged); assigning needs write access to the repository, which the owner grants on GitHub.
- A closed epic, or an issue named in `Part of the epic #N` without the `epic` label, gives no member (AC1, like `epic_of`).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 How does the loop know a task is a member's? | An assignee other than the owner | A new label `human:claimed` | GitHub's own assignee, no new label; old issues assigned to the owner keep building |
| Q2 Does a member assigned to an epic own its tasks? | Yes, tasks inherit; a task's own member wins | Only the task's assignee counts | The owner hands out work by epic or by task in one click |
| Q3 How does a member claim, give back and hand off? | Only by changing the assignee; `agent:ready` stays | Assign and remove `agent:ready` | One step, and giving back needs no label from the owner |
| Q4 A member claims an issue the loop is building | The build goes on; the tick warns once | The tick stops the build | No lost build and no half-stopped state |
| Q5 Where does a member's pull request for an epic task go? | Into the epic branch; owner clicks Merge; tick sets `agent:in-epic` | Into `main` after the epic merges | Members and the loop share one epic; the owner still reviews one epic pull request |

## Design

Nothing visible to users of the app.

## Open questions
