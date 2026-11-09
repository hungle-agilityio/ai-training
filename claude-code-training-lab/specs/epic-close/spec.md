# Spec: epic-close

## Summary

The tick keeps every open loop pull request whose base is not `main` (stacked on an epic branch or on a parent branch) as a draft, so GitHub disables its Merge button, and marks it ready again when it moves the base to `main`. When a loop pull request is merged into an epic branch anyway, the tick opens a new pull request from the same head branch into `main` with `Closes #<n>`, so the task reaches `main` and its issue closes on merge. Nothing visible to users.

## Acceptance criteria

**Stacked pull requests stay drafts**

- **AC1.** Each tick, every open loop pull request (marker `<!-- work-queue -->`) whose base is not `main` and that is not a draft is converted to a draft (`gh pr ready <n> --undo`). The tick records the number in `~/.reviewradar/stack-drafts` and logs `pr-<n>: draft while its base is <base>`.
- **AC2.** The build prompt of a stacked task (epic: `epic_prompt`; one parent: the ADR-018 prompt) asks for `gh pr create --draft`, so the pull request is a draft from the start. AC1 still covers a pull request opened without it.
- **AC3.** When the tick changes the base of a pull request to `main` (`settle_epic_children`, `move_children`, `settle_children`), it also marks it ready (`gh pr ready <n>`) when the number is in `stack-drafts`, then removes it from the record. A pull request the tick did not draft is never marked ready by the tick.
- **AC4.** A failed `gh pr ready` (either direction) is one log line and is tried again at the next tick; it never stops the tick.
- **AC5.** Nothing else changes for a draft stacked pull request: it is still left out of the epic branch merge (spec `epic-branch` AC1), the owner's approval comment on it still waits as today (`wait_for_parent`), and review fixes run on it as on any loop pull request.

**A pull request merged into an epic branch anyway**

- **AC6.** Each tick, for every loop pull request that is merged, whose base is an `epic/` branch, whose `Closes #<n>` issue is open, and whose head commit is not in `origin/main`: when every pull request on its `Stacked on ... through epic/...` line is merged, and no open pull request from the same head branch into `main` exists, the tick opens one with `gh pr create --base main --head <head branch>`, the same title, and the same body without the `Stacked on` line (the marker, the verify report link and `Closes #<n>` stay).
- **AC7.** It then labels the new pull request `pr:ready-for-review` when the old one had it, labels issue #<n> `agent:review`, logs `pr-<old>: merged into <epic branch>; opened PR #<new> into main for #<n>`, and sends one ntfy message `PR #<old> was merged into <epic branch>, not main: opened PR #<new> for #<n>`.
- **AC8.** While a pull request on the `Stacked on` line is still open, the tick waits and logs `pr-<old>: merged into <epic branch>; waits for #<P> before opening a pull request into main`. When one of them was closed without merge, it opens nothing, logs it and sends one ntfy message (once per pull request).
- **AC9.** The rescue happens once per old pull request (record `~/.reviewradar/epic-rescued`); a head branch already in `main`, or an issue already closed, needs nothing. `tidy_ended` does not remove the `agent:review` set by AC7.
- **AC10.** The new pull request is a normal loop pull request: the tick merges it only on the owner's approval comment, with green checks (ADR-016).

**The record**

- **AC11.** `ops/README.md` describes the draft guard and the rescue; ADR-021 gets a note under Consequences pointing to this spec.
- **AC12.** New tests only, in new files; every existing test passes unchanged.

## Edge cases

- Empty: no stacked pull request and no merged epic pull request: the tick does nothing new and logs nothing new.
- The owner turns a stacked draft back to ready by hand: AC1 converts it to a draft again at the next tick.
- The owner's own pull requests (no marker) are never drafted or rescued.
- A merged epic pull request from before this change (PR #320, #317) is rescued too, if no pull request into `main` exists for its branch yet; PR #295 (#283) needs nothing because #283 is closed.
- Several merged epic pull requests in one tick: each is handled on its own; one failure never stops the others.
- Permissions: only the tick drafts, readies and opens these pull requests; a build never changes another pull request.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Direction for tasks of an epic | Keep ADR-021 and add guards | B: every task into the epic branch, one final pull request into `main`; C: every pull request based on `main` from the start | Fixes the real cause (Merge pressed before the tick moved the base); tasks still build while reviews wait and close one by one |
| Q2. How to stop the Merge button on a stacked pull request | Keep it a draft until its base is `main` | Only a warning comment | GitHub disables Merge on a draft; no ruleset needed |
| Q3. A pull request merged into an epic branch anyway | The tick opens a new pull request from the same branch into `main`, `Closes #n`, `agent:review`, ntfy | Only ntfy and a comment; the owner fixes it in a thread | No task stays stranded like #317; the owner only approves the new pull request |
| Q4. #317 now | Rescued at once through the Mac mini (new pull request into `main`) | Wait for this feature | The code was reviewed; its diff against `main` is only its own 5 files |

## Design

Nothing visible to users.

## Open questions
