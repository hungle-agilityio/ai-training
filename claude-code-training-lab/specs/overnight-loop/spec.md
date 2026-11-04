# Spec: overnight-loop

## Summary

Three changes to the loop (`ops/agent_tick.py` and the `work-queue` skill), nothing visible in the app. (1) The tick retries a failed issue up to 3 times when a retry can help. (2) The pull request limit of 10 is removed. (3) An issue whose one unmerged dependency already has a green loop pull request starts at once, on that pull request's branch, and opens its own pull request into that branch ("stacked"); it is merged only after its parent.

"Parent" below is the one dependency of a stacked issue; "parent pull request" is the open loop pull request that closes it (`Closes #P`). "Child" is the stacked issue and its pull request.

## Acceptance criteria

### Retry of failed builds (Q1)

- **AC1.** When a build of issue #N ends with `agent:failed`, the tick writes `~/.reviewradar/failed/<N>` (JSON) with: `main` = the `origin/main` commit at that moment, `parent` = the head commit of the parent pull request when #N was stacked (else empty), `kind`, and `retries` (0 the first time, kept on later failures). `kind` is `transient` when the tick set `agent:failed` itself for `timeout`, `gone` (no exit code), a non-zero exit code, or `no-artifact`; it is `stopped` in every other case (the build ended without a pull request, or the build set `agent:failed` itself). An open `agent:failed` issue the tick finds without a record gets one with `kind` `stopped` and `retries` 0.
- **AC2.** A failed issue is retried when all hold: `retries` < 3; it is not `agent:manual`; for `stopped`, `origin/main` or the parent pull request head moved since the record (for `transient`, no condition); its dependencies are met by the rules of today or of AC9; a slot is free after the ready issues (oldest ready issues first, then failed issues oldest first); no other start rule holds it (shared file, runs alone, red main, pause).
- **AC3.** A retry: removes `agent:failed`, renames the issue's local branches `bug|feat|task/<N>-*` to `archive/...` (as `archive_branches`, deleting nothing, also when no worktree is kept), starts the build like a new issue (from `origin/main`, or from the parent branch by AC10), adds 1 to `retries`, comments on the issue `<!-- work-queue -->` + `Retry <k> of 3: <reason>.` where `<reason>` is `the last build <outcome>` for `transient` or `main moved from <old> to <new>` / `the parent pull request #<P> moved from <old> to <new>` for `stopped` (7-character shas), and notifies `ReviewRadar retrying #<N> (<k> of 3)`.
- **AC4.** When a build with `retries` = 3 fails, the issue stays `agent:failed` and the tick notifies once `ReviewRadar #<N> failed after 3 retries, needs you: <issue link>`. It is not retried again.
- **AC5.** The plan limit is not a failure: it goes back to `agent:ready` and pauses as today, and it changes no record.
- **AC6.** When the owner restarts an issue by hand (removes `agent:failed`, adds `agent:ready`) or closes it, its record moves to `~/.reviewradar/archive/failed-<N>-<time>`, so a later failure starts at `retries` 0.

### No pull request limit (Q5)

- **AC7.** The tick starts ready issues whatever the number of open pull requests; only `AGENT_CONCURRENCY` and the other start rules limit it. `WAITING_CAP`, the message `ReviewRadar waiting: <k> pull requests open (limit 10), ...` and the rule that hides the "blocked" message at the limit are removed.
- **AC8.** When no build starts, nothing runs and no ready issue is left (ready = `agent:ready` without a skip label), the tick sends `ReviewRadar queue empty, <k> pull requests waiting` as today. When ready issues are left but all are blocked, only the blocked message of #143 is sent.

### Stacked tasks (Q2, Q3, Q4)

- **AC9.** An `agent:ready` (or retried) issue #N whose dependencies are all met except exactly one, #P, starts stacked when: #P is not closed as not planned; #P has an open, non-draft loop pull request #Q with `Closes #P`, label `pr:ready-for-review`, and every check green (`check_state` = green, at least one check); #N is not `agent:manual`. Several unmet dependencies, or a parent without such a pull request, keep #N waiting with the reasons of #143.
- **AC10.** A stacked build starts in a worktree detached at `origin/<head branch of #Q>` (the tick fetches it), with the prompt `Use the work-queue skill for issue #<N> only. Stacked on pull request #<Q>: branch from origin/<branch> and open the pull request into <branch>.` The start message is `ReviewRadar started #<N> on top of PR #<Q>: <title>`. The record `~/.reviewradar/stacked/<N>` holds `#Q`, its branch and its head commit.
- **AC11.** The shared-file rule of ADR-015 ignores the files of #P (and of #P's own parents in a chain) for #N; a file shared with any other running or in-review issue still holds #N.
- **AC12.** Chains are allowed: a child pull request that is itself green and `pr:ready-for-review` can be the parent of the next issue (its base is not `main`).
- **AC13.** The tick never merges a pull request whose base is not `main`. An approval on such a pull request gives the log line and one message `PR #<n> not merged: it waits for its parent PR #<Q>` (once per approval), and the approval stays valid: the pull request merges at a later tick, after its parent, by the rules of ADR-016.
- **AC14.** When a parent pull request is merged, the tick makes sure each open pull request based on its branch now has base `main` (`gh pr edit <n> --base main` when GitHub did not retarget it). From then on the child is a normal loop pull request: behind `main` it is updated, a conflict gets `/redo merge origin/main into this branch and fix the conflict` (ADR-015).
- **AC15.** When a parent pull request is closed without merge, each open child based on its branch gets `pr:blocked` (the other `pr:*` labels removed) and a comment `<!-- work-queue -->` + `The parent pull request #<Q> was closed without merge. This pull request is built on it and is not merged.`, and the tick notifies once `ReviewRadar PR #<n> blocked: its parent PR #<Q> was closed`.
- **AC16.** A change to the parent after the child started (change requests, CI fixes, update from main) does nothing to the child until the parent merges (AC14).
- **AC17.** The `work-queue` skill: when the prompt says `Stacked on pull request #Q`, the build branches from the current detached commit (the parent branch), opens its pull request with `--base <parent branch>`, and adds the line `Stacked on #<Q> (merge that one first).` above `Closes #N`. Everything else in the build stays as it is. `create-pull-request` accepts a base other than `main` only in that case.
- **AC18.** ADR-018 records stacked pull requests, the retry rule and the end of the pull request limit; `ops/README.md` describes AC1 to AC16 in short paragraphs; ADR-012/ADR-014 lines on the limit are marked superseded by ADR-018.

## Edge cases

- Empty: no failed issue and no stackable issue: the tick behaves as today, minus the limit.
- Large data: no limit on open pull requests; the issue list is read once per tick (limit 200) and the pull request list as today (limit 40). A night of 20 pull requests needs the pull request list limit raised to 100 (AC7 task).
- A stacked child fails (`stopped`): AC2 retries it when `main` or the parent head moved. When its parent merged meanwhile, the retry starts from `origin/main` (AC9 no longer applies, the dependency is met).
- A parent pull request turns `pr:changes-requested` or red before a child starts: the child waits (AC9). After it started: AC16.
- The owner approves a child before its parent: AC13; it merges after the parent without a second approval unless the update from `main` hits a conflict (ADR-016).
- A parent pull request is closed and its issue later rebuilt: the blocked child stays `pr:blocked`; the owner closes it and relabels the child issue `agent:ready`.
- Permissions: only the owner's `agent:ready` counts (`labelled_by_owner`), for retries and stacked issues too.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Retry of `agent:failed` | Up to 3 retries, each from a fresh branch: transient ends at the next free slot; a build that stopped itself only when `main` or the parent moved; then notify | 3 retries whatever changed; once only (#149) | Real failures so far were deterministic (#132, #149); a retry with nothing changed repeats them and spends the 5-hour plan |
| Q2. When a dependent task starts early | Exactly one unmerged dependency whose loop pull request is `pr:ready-for-review` with green CI; chains allowed | Several unmerged parents; as soon as the parent has a pull request | The child builds on checked code and never merges two branches |
| Q3. Base of the child pull request | The parent's branch; never merged while its base is not `main` | Base `main` | One task, one small diff to review; the base guards the merge order |
| Q4. Parent changed in review, or closed | No extra sync; after the parent merges the update from `main` takes over; parent closed -> child `pr:blocked` | Sync the child on every parent commit | Reuses existing steps and permissions (`git merge origin/main` only) |
| Q5. Pull request limit of 10 | Removed in code | `AGENT_WAITING_CAP` in `agent.env` | The owner's request; builds stay limited by `AGENT_CONCURRENCY` |

## Design

Nothing visible to users.

## Open questions
