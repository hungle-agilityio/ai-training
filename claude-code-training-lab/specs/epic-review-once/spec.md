# Spec: epic-review-once

## Summary

For tasks of an epic (`Part of the epic #N`, #N open and labelled `epic`), the epic branch `epic/<N>-<slug>` becomes the integration branch. Every task pull request goes into it, and the tick merges it there without an owner comment when it is green, has its verify report and has no open change request. When all open tasks of the epic are in it, the tick opens one pull request `epic/<N>-<slug>` → `main` that closes the tasks and the epic; the owner approves only that one (ADR-016). This reverses ADR-021 point 4 ("only main ships") for epics, recorded in ADR-022. Nothing visible to users of the app.

## Acceptance criteria

**Tasks go into the epic branch**

- **AC1.** When the first `agent:ready` task of an open epic is chosen and `origin/epic/<N>-<slug>` does not exist, the tick creates it from `origin/main` before the build starts (log `epic #<N>: branch <branch> created`).
- **AC2.** Every task of an epic, with or without dependencies, starts from `origin/epic/<N>-<slug>` and its prompt asks for a normal (not draft) pull request into that branch. Its body has no `Stacked on` line.
- **AC3.** A dependency that is a task of the same epic counts as met when its issue has the label `agent:in-epic` (AC6). A dependency on an issue outside the epic must be closed, as today.
- **AC4.** The draft guard (`keep_stacked_as_drafts`, spec epic-close AC1 to AC3), the retarget to `main` (`settle_epic_children`) and the rescue (`rescue_epic_merges`) leave pull requests whose base is an epic branch alone. They keep working for one-parent stacks (ADR-018).

**The tick merges tasks into the epic branch**

- **AC5.** Each tick, an open loop pull request (marker `<!-- work-queue -->`) whose base is `epic/<N>-<slug>` is merged with `gh pr merge <n> --merge --delete-branch --match-head-commit <head>` when: not a draft, `pr:ready-for-review`, at least one check and every check green, a `https://claude.ai/artifact/` link in the body, no open change request, no run for it going, and merge state not `DIRTY` or `BLOCKED`. No owner comment is needed. When the merge state is `BEHIND`, the tick runs `gh pr update-branch <n>` first and merges at a later tick; on a conflict it posts `/redo merge origin/epic/<N>-<slug> into this branch and fix the conflict` once per head (as ADR-021 point 3).
- **AC6.** After the merge, the issue the pull request closes gets `agent:in-epic` and loses `agent:review`, `agent:running` and `agent:ready`; it stays open. The tick logs `pr-<n>: merged into <branch>; #<issue> agent:in-epic` and sends one ntfy message `PR #<n> merged into <branch> (#<issue>)`.
- **AC7.** At most one task pull request is merged into a given epic branch per tick, so each merge is checked against the branch as it is after the previous one.

**One pull request into main per epic**

- **AC8.** When every open issue with `Part of the epic #<N>` has `agent:in-epic` (at least one does), and no open pull request from `epic/<N>-<slug>` into `main` exists, the tick merges `origin/main` into the epic branch if needed and opens it: title `[EPIC] <epic title without "Epic:">`, body starting with the marker, a table task → pull request → verify report link (from each merged task pull request), then one `Closes #<task>` line per task and `Closes #<N>`. A pull request whose head is an epic branch and that has no `pr:*` label starts no run (it is not unfinished work); `mark_green_ready` labels it `pr:ready-for-review` once its checks are green. The tick sends one ntfy message `Epic #<N> is ready for your review: PR #<p>`.
- **AC9.** The owner's approval comment on the epic pull request merges it as for any loop pull request (ADR-016: green checks, no open change request, update when behind). The epic pull request is merged with `--merge` and the branch is deleted on merge; GitHub closes the tasks and the epic.
- **AC10.** Any other owner comment on the epic pull request is a change request, handled by a loop run on that pull request (branch `epic/<N>-<slug>`), as for any loop pull request (ADR-016). The run pushes its fix to the epic branch.
- **AC11.** A task issue that gets `agent:ready` again while the epic pull request is open (the owner wants more work) builds as in AC2; the tick adds its `Closes #<task>` line to the epic pull request body after its merge into the epic branch.
- **AC12.** While the epic pull request is open, `main` moving on is merged into the epic branch each tick as today (ADR-021 point 1); a conflict is reported once per hour as today.

**The record**

- **AC13.** ADR-022 records the decision (amends ADR-021 points 2 and 4 for epics); ADR-021 gets a "Superseded in part by ADR-022" line; the `work-queue` skill says how to open the pull request into the epic branch (no draft, no `Stacked on`) and that a run on the epic pull request pushes to the epic branch; `ops/README.md` describes `agent:in-epic` and the epic pull request.
- **AC14.** New tests only, in new files; existing tests pass unchanged, except those listed under "Existing tests that change" in the issue.

## Edge cases

- Empty: an epic with no ready task: no branch, nothing new.
- A task pull request is red: it is not merged; its review fix runs as today (ADR-016). Dependent tasks wait (AC3).
- The owner clicks Merge on a task pull request into the epic branch by hand: the same as AC5; AC6 runs at the next tick.
- A task fails three times (`agent:failed`): the epic pull request is not opened (AC8 needs every open task `agent:in-epic`); the owner closes the task as not planned or fixes it, and AC8 runs at the next tick.
- A task closed as not planned is not open, so AC8 ignores it.
- Epic #N closed by hand while tasks are open: the tick stops merging into its branch and deletes the branch once no pull request is based on it (ADR-021 point 4, `delete_ended`).
- Epics opened before this change (none open on 2026-11-09): nothing to migrate.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Where task pull requests of an epic go | Into the epic branch, merged by the tick; one epic pull request into `main` | Each task into `main` with its own approval (ADR-021, chosen 2026-11-09 02:49Z) | The owner wants to review once per epic and let the tasks run on their own |
| Q2. When a task issue closes | When the epic pull request merges (`Closes #` lines), label `agent:in-epic` until then | Closed by the tick at the merge into the epic branch | An issue is closed only after a human checked the result (workflow guardrail) |
| Q3. Owner comments on the epic pull request | A loop run fixes them on the epic branch | A new task issue per comment | The same review route as every loop pull request |
| Q4. Who builds this flow change | By hand on the Mac mini, the owner clicks Merge (as #352 to #355) | `agent:ready` issues for the loop | The loop would build its own merge rules; the epic test waits for it |

## Design

Nothing visible to users of the app.

## Open questions
