# Spec: epic-branch

## Summary

The tick keeps one branch per epic, `epic/<epic number>-<slug of the epic title>`, made from `main`. A task belongs to an epic when its issue body has the line `Part of the epic #<N>` and #N is an open issue labelled `epic`. The tick merges every green, ready loop pull request of the epic into that branch, and keeps the branch up to date with `main`. A task of the epic whose unmet dependencies all have their pull request in the epic branch builds from the epic branch, opens its pull request into it, and moves to `main` once its dependencies are merged. Nothing visible to users.

## Acceptance criteria

**The epic branch**

- **AC1.** The first time a pull request of an epic's task is open, not a draft, labelled `pr:ready-for-review` and green on every check, the tick creates `epic/<N>-<slug>` from `origin/main` and pushes it. The slug is the epic title without the `Epic:` prefix, lowercase, non-letters and non-digits replaced by `-`, at most 40 characters, no leading or trailing `-` (for #236 "Epic: reply to reviews": `epic/236-reply-to-reviews`).
- **AC2.** Each tick, every pull request of the epic that meets AC1's conditions and whose head commit is not yet in the epic branch is merged into it with a merge commit (`git merge --no-ff`, never a rebase), then the branch is pushed. A pull request that gets new commits after review is merged again once it is green and ready.
- **AC3.** Each tick, when `origin/main` has commits the epic branch lacks, the tick merges `origin/main` into the epic branch with a merge commit and pushes it.
- **AC4.** When a merge of AC2 has a conflict, the tick aborts it, leaves the epic branch as it was, and posts once on that pull request the change request `/redo merge origin/epic/<N>-<slug> into this branch and fix the conflict`. The loop handles it like the `main` conflict of ADR-015; after the fix the pull request is merged into the epic branch at the next tick (AC2). A conflict of AC3 sends one ntfy message per hour naming the epic branch, and nothing builds from that epic branch until it is solved.
- **AC5.** The tick log has one line per epic per tick: `epic #<N>: branch epic/<N>-<slug>, <k> pull requests in it` (or the conflict of AC4).
- **AC6.** When the epic issue is closed and no open pull request has the epic branch as its base, the tick deletes the epic branch on GitHub and in the main checkout.

**Tasks that build on it**

- **AC7.** A ready task of an epic whose unmet dependencies (`Depends on #M`) are one or more issues that each have a pull request inside the epic branch (AC2) starts at once. The prompt says `Stacked on epic branch epic/<N>-<slug>: branch from origin/epic/<N>-<slug> and open the pull request into epic/<N>-<slug>.`
- **AC8.** That pull request's body has the line `Stacked on #<P1>, #<P2> through epic/<N>-<slug> (merge those first).` above `Closes #<n>`, listing the open dependency pull requests. Its diff shows only the task's own changes.
- **AC9.** The tick never merges a pull request whose base is the epic branch. When every dependency in its `Stacked on` line is merged into `main`, the tick changes the base to `main`, updates the branch from `main` (ADR-015), and it becomes a normal loop pull request.
- **AC10.** A dependency pull request closed without merge sets its stacked children `pr:blocked`, as in ADR-018.
- **AC11.** A task of an epic with exactly one unmet dependency uses the epic branch as in AC7, not the one-parent stacking. A task with no epic keeps the one-parent stacking of ADR-018 unchanged.
- **AC12.** A dependency whose pull request is not in the epic branch (red, draft, not ready, or in conflict) keeps the task waiting, and the waiting line says why (`#242 waits for #240: PR #252 is not in epic/236-reply-to-reviews (checks are red)`).

**The build and the record**

- **AC13.** `work-queue` accepts the epic prompt of AC7 and the `/redo merge origin/epic/...` change request of AC4; `create-pull-request` accepts the epic branch as a base only with the `Stacked on ... through epic/...` line.
- **AC14.** ADR-021 records this decision and amends ADR-018 point 1 for epic tasks; `ops/README.md` describes the epic branch.
- **AC15.** New tests only, in new files; every existing test passes unchanged.

## Edge cases

- Empty: an epic with no green, ready pull request has no epic branch; its tasks wait as today.
- Large data: an epic has at most 10 tasks (create-issue gate), so at most 10 merges per tick per epic.
- Several epics at once: each has its own branch; a task belongs to one epic only (the first `Part of the epic` line).
- A task listed in two epics' dependencies across epics: dependencies outside the task's own epic must be merged into `main`, as today.
- Permissions: only the tick pushes and deletes `epic/*` branches; a build never pushes to them.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Base of a dependent task's pull request | The epic branch, then `main` once the dependencies are merged (as ADR-018) | `main` from the start | The diff shows only the task's own changes; the base guards the merge order |
| Q2. Which pull requests go into the epic branch | Only green and `pr:ready-for-review`, merged again after each review fix | Every pull request as soon as it opens | Tasks build on checked code |
| Q3. Conflict when merging into the epic branch | The loop merges the epic branch into the task branch and fixes it (`/redo`, as ADR-015), then the tick tries again | Leave it out, `pr:blocked`, tell the owner | The owner does not fix conflicts by hand (ADR-015) |
| Q4. Which tasks use it | Tasks of an epic (`Part of the epic #N`) | Every dependent task | An epic is the unit of related work; other tasks keep the simpler rule |
| Q5. Tasks without an epic and one open dependency | Keep the one-parent stacking of ADR-018 | Drop it and wait | It works and needs no shared branch |

## Design

Nothing visible to users.

## Open questions
