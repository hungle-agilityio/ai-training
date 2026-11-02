# Spec: loop-depends

## Summary

Two changes in the tick (`ops/agent_tick.py`), nothing visible in the app. (1) The tick removes the labels of a merged or closed loop pull request itself, without a Claude build. (2) The tick tells the owner, once per change, which ready issues are waiting and why, with the pull request to review or merge first. It also stops treating a dependency closed as "not planned" as done, and removes `agent:ready` from closed issues.

## Acceptance criteria

- **AC1.** For a loop pull request in state `MERGED` or `CLOSED`, the tick removes every `pr:*` label from it and `agent:review` from the issue it closes (`Closes #N`), with `gh`, in the same tick. It starts no build for that pull request, so the slot stays free for a ready issue in the same tick. The log says `pr-<n>: tidied, labels removed`.
- **AC2.** With `AGENT_CONCURRENCY=2`, a tick that merges two pull requests (or finds two merged ones with labels) and has two ready issues whose dependencies are now closed starts both issues in that tick.
- **AC3.** A dependency counts as done when its issue is closed with state reason `COMPLETED`, or when its state reason cannot be read. A dependency closed as `NOT_PLANNED` does not count: the issue does not start.
- **AC4.** When at least one open `agent:ready` issue (without `agent:running`, `agent:review`, `agent:failed`, `agent:manual`) is not started in a tick, because of a dependency or a shared file, the tick sends one message (ntfy and Slack, through the existing `notify`):
  ```
  ReviewRadar waiting: <k> ready issues blocked
  #<n> waits for #<m>: <reason>
  ...
  ```
  one line per blocked issue and per blocking issue, ordered by issue number, where `<reason>` is:
  - `review PR #<p>` when #m has an open loop pull request `#p` (`Closes #m`);
  - `building` when #m has `agent:running`;
  - `closed as not planned, remove the dependency or reopen it` for AC3;
  - `no pull request yet` otherwise;
  - for a shared file: `#<n> waits for #<m>, which also touches <path>`.
- **AC5.** The AC4 message is sent also while builds are running. It is sent again only when its text changes (stored in `~/.reviewradar/last-blocked`); when no issue is blocked any more, the file is removed and nothing is sent.
- **AC6.** The pull request limit message ("ReviewRadar waiting: N pull requests open (limit 10), M ready issues not started") and "queue empty" keep their text and their rules. When the limit is reached, only the limit message is sent, not AC4.
- **AC7.** Each tick removes `agent:ready` from closed issues that still carry it, and logs `issue-<n>: closed, agent:ready removed`.
- **AC8.** Each tick logs one line per blocked issue, the same text as its AC4 line.
- **AC9.** `ops/README.md` lists the AC4 message among the notifications.

## Edge cases

- Empty: no ready issue, or none blocked: no AC4 message, `last-blocked` removed.
- Large data: one line per blocked issue; the issue list is read once per tick, as today (limit 200).
- An issue with several dependencies gets one line per open or not-planned dependency.
- A dependency that is not a loop issue (no pull request with `Closes #m`): reason `no pull request yet`.
- Permissions: only the owner's `agent:ready` counts, as today (`labelled_by_owner`); an issue skipped for that reason is not in AC4.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Who tidies a merged pull request | The tick, with `gh`, no build | A Claude build, issues first | Removing labels needs no Claude; a build cost a slot and minutes on 2026-11-02 |
| Q2 What the waiting message says | One message, a line per issue with the reason and the PR, sent when it changes | Every tick | The owner sees which PR to review first, without noise |
| Q3 While builds run | Send it too | Only when nothing runs | Today the tick is silent while anything runs |
| Q4 Dependency closed as not planned | Not done; the issue waits and the owner is told | Counts as done | A dependency that was never built must not unlock work |
| Q5 Closed issues with `agent:ready` | The tick removes the label | Leave it | #130 kept it after the merge; confusing on GitHub |

## Design

Nothing visible to users.

## Open questions
