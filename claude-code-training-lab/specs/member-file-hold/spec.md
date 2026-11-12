# Spec: member-file-hold

## Summary

The tick (`ops/agent_tick.py`) treats every open issue that has a member, on the issue or through its open epic (`member_of`), as holding the backticked paths of its `## Files likely touched` section, whatever its labels. A ready loop issue that lists one of those paths waits, and the log line and the "waiting" message name the member. Nothing visible to users of the app.

## User story

As the owner, I want a task a member has claimed to hold its files like a running build does, so that a member and the loop never change the same file at once.

## Acceptance criteria

- **AC1.** Given open issue #509 assigned to `alice` (a member) whose `## Files likely touched` lists `reviews/views.py`, with any labels or none, and ready issue #512 (labelled `agent:ready` by the owner, no member, no open dependency) that lists `reviews/views.py`, when the tick picks issues, then #512 is not started and the log says `issue-512: waits for #509 (member alice), which also touches reviews/views.py`.
- **AC2.** Given the same issues, when the tick builds its "waiting" lines (`blocked_lines`), then #512 is counted as blocked and its line is `#512 waits for #509 (member alice), which also touches reviews/views.py`.
- **AC3.** Given open epic #600 assigned to `bob` (a member) and its open task #601 (no own member, `Part of the epic #600`) that lists `ops/release.py`, and ready issue #605 (not part of the epic) that lists `ops/release.py`, when the tick picks issues, then #605 is not started and the log says `issue-605: waits for #601 (member bob, epic #600), which also touches ops/release.py`; the "waiting" line is `#605 waits for #601 (member bob, epic #600), which also touches ops/release.py`. When the task has its own member, that member is named, without the epic (the task's member wins, ADR-028).
- **AC4.** Given #509 and #512 of AC1, when `alice` is removed from #509 (no other member on it or its epic) or #509 is closed, then at the next tick #512 is started as on `main`.
- **AC5.** A path held by an `agent:running` or `agent:review` issue, or by an issue chosen earlier in the same tick, keeps the line of `main` (`waits for #<m>, which also touches <path>`, without a member) even when a member issue lists the same path. Among member issues, the one with the lowest number holds a path. The parents a stacked or epic task builds on are still ignored as on `main` (`shared_holder`, #165 AC3), whether they are loop or member issues.
- **AC6.** A member issue whose body has no `## Files likely touched` paths holds nothing; a member issue itself is still skipped as on `main` (`issue-<n>: assigned to <login>; skipped`) and is never blocked by its own files. The epic issue of AC3 holds only the paths of its own body, like any member issue.
- **AC7.** The tick makes no extra `gh` call for this: it uses the issue list it already reads (`open_issue_list`, with `assignees`) and `member_of`.
- **AC8.** `ops/README.md`, section `## Guards`: the file bullet also names an open issue that has a member (on the issue or its epic), any label, and gives the log line `issue-<n>: waits for #<m> (member <login>), which also touches <path>`; section `## Team members` gets one bullet: a claimed issue holds the files of its `## Files likely touched` until it is closed or the member is removed, so list them before claiming.
- **AC9.** New tests in `ops/tests/test_tick_member_files.py` (no network, a fake `gh` as in the other tick tests): AC1 to AC7 and the two README texts of AC8. Every test on `main` passes unchanged.

## Edge cases

- Empty: no open issue has a member: the tick behaves exactly as on `main`.
- Large data: the tick reads at most 200 open issues in one call (as on `main`); holding adds no call.
- Permissions: only assignees decide; an assignee equal to the owner (`hungle-agilityio`) is not a member and holds nothing beyond `main`'s rules.
- An `agent:in-epic` task of a member (merged into the epic branch, still open) keeps holding its files until the epic merges and closes it: its change is not on `main` yet.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Which member issues hold files? | Every open issue with a member (directly or through its epic), any label | Only member issues labelled `agent:ready` | A member builds by hand, so a label does not say whether they are changing the file; the assignee says they took the work (owner, 2026-11-12) |
| Q2 What does the waiting line say? | Name the member: `waits for #509 (member alice), which also touches ...` | The line of `main` only | The owner sees at once whom to ask, without opening the issue (owner, 2026-11-12) |

## Decisions during build

See [decisions/](decisions/): one file per task, written by its build.

## Design

Nothing visible to users.

## Open questions
