# Spec: tick-hardening

## Summary

Five small guards in the tick (`ops/agent_tick.py`): only the owner's own pull requests count, the main checkout is fast-forwarded before each tick, the plan limit is recognised in more cases, `agent:ready` is removed once a build has handed over, and a failed build no longer blocks the next one. Nothing visible to users of the app.

## Acceptance criteria

- **AC1. Only the owner's pull requests.** The tick reads `author` and `isCrossRepository` with the pull request list. A pull request is not a loop pull request when `isCrossRepository` is true, or when `author.login` is a login other than `hungle-agilityio`, even if its body holds `<!-- work-queue -->`. Such a pull request is never chosen, does not count towards the cap of 3, and its `Closes #N` is not read (a failed build of issue #N is still marked `agent:failed`).
- **AC2. Main is pulled before each tick.** After taking the lock, the tick reads the current branch of the main checkout (`git -C <git root> branch --show-current`) and its tracked changes (`git -C <git root> status --porcelain --untracked-files=no`). When the branch is `main` and there are no tracked changes, it runs `git -C <git root> fetch origin main` and `git -C <git root> merge --ff-only origin/main`. The new code runs from the next tick; the tick does not restart itself.
- **AC3. When main cannot be pulled.** The tick writes one log line and goes on with the tick as today when: the branch cannot be read (empty output or an error); the branch is not `main`; there are tracked changes; or the fetch or the fast-forward fails. In the last three cases it also sends one ntfy message, `ReviewRadar main checkout not updated: <reason>`, and does not send the same reason again until the pull succeeds once.
- **AC4. Plan limit, more texts.** The plan-limit text also matches `extra_usage`, `usage_limit` and `hit your .*limit` as a regular expression (any case, so the real message `You've hit your 5-hour limit · resets 1:50pm` matches), besides today's `usage limit`, `limit reached` and `rate_limit`.
- **AC5. Plan limit, any exit code.** The plan limit is checked for every ended build, whatever its exit code, but only when the build did not hand over: for an issue, when it would otherwise get `agent:failed` (it still has `agent:running` and no loop pull request closes it); for a pull request run, when it would otherwise be reported as stopped. Then, as today, the issue goes back to `agent:ready`, the worktree is removed and new builds pause for 60 minutes. A build that handed over is never put back to `agent:ready`.
- **AC6. agent:ready leaves after the hand-over.** At each tick, every open issue that has both `agent:ready` and `agent:review` loses `agent:ready` (`gh issue edit <n> --remove-label agent:ready`), with one log line. An issue with `agent:failed` keeps `agent:ready`, so removing `agent:failed` is still enough to build it again. To build a handed-over issue again, the owner adds `agent:ready` again.
- **AC7. A failed build frees its branch.** When the tick starts a target whose worktree is still there, it moves the worktree aside as today, then renames the branch checked out there (if any) to `archive/<branch>-<unix time>`. For an issue target it also renames every local branch whose name starts with `bug/<n>-`, `feat/<n>-` or `task/<n>-`, for the same reason. Nothing is deleted; commits stay on the archive branches. A pull request run then checks out its branch from `origin` as today.
- **AC8. ntfy when a build does not start.** When a start fails (worktree, `uv sync` or another step), the tick sends one ntfy message `ReviewRadar build for <issue #n | pull request #n> did not start: <step> failed`, besides today's log line. The same key and step is not sent again until that key starts once.
- **AC9. Tests.** A new test file `ops/tests/test_tick_hardening.py` covers AC1 to AC8 with `gh`, `git` and the clock faked (no network), including: a fork pull request with the marker; a pull request by another login with the marker and `Closes #1` while the build of #1 failed; a checkout on another branch, with tracked changes, with a failed fast-forward, and a clean pull; the same reason sent once; `extra_usage_unavailable` with exit code 0 and `You've hit your 5-hour limit · resets 1:50pm` with exit code 1, both before the hand-over, and a limit text after the hand-over; an issue with `agent:ready` and `agent:review`, and one with `agent:ready` and `agent:failed`; a kept worktree on `task/5-x` renamed and the run started; a failed start sent once. Existing tests in `ops/tests/test_agent_tick.py` stay unchanged and pass. `uv run ruff check .` and `uv run mypy .` pass.
- **AC10. How to run.** `ops/README.md` says in a short "Self-repair" part: the tick pulls `main` when the checkout is on `main` and clean; the `archive/` branches; that a handed-over issue loses `agent:ready`; and the new ntfy messages.

## Edge cases

- Empty: no loop pull request, no ready issue: the pull of `main` still runs; nothing else changes.
- Large data: still one pull request list (40) and one issue list (200) per tick; AC6 adds one `gh issue edit` per issue to tidy, normally zero or one.
- Permissions: only `hungle-agilityio` pull requests from this repository count (AC1); labels and `/redo` keep today's owner checks.
- The main checkout has untracked files only (for example `.claude/worktrees/`): it is still pulled, because only tracked changes count.
- A fast-forward is impossible (local commits on `main`): no pull, one ntfy (AC3); the owner decides.
- A build is running while `main` is pulled: no effect, builds run in their own worktrees.
- A failed build had already pushed its branch to GitHub without a pull request: out of scope; the new build cannot push over it and fails with that reason.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Which pull requests are the loop's | Owner's login and same repository, with the marker | Same repository only | The loop always opens its pull requests with the owner's login from this repository, so nothing real is lost |
| Q2. How the tick gets the new `main` | At the start of each tick, fast-forward only, only on `main` with no tracked changes; else one ntfy | Force the checkout to `main`; no pull (a thread runs "pull main") | Automatic without ever overwriting work in progress; the new code runs from the next tick |
| Q3. Plan limit | More texts, checked for any exit code before the hand-over | More texts only | A false match costs a 60-minute pause; a miss leaves `agent:failed` to remove by hand. #61, #68 and #72 failed on 2026-10-29 with `You've hit your 5-hour limit`, which today's text misses |
| Q4. A closed (rejected) pull request | `agent:ready` is removed once the issue is handed over (`agent:review`) | Keep today's behaviour (rebuilt in 10 minutes) | The labels show the real state and a rejection does not spend a build. Removed at the hand-over rather than at the claim, so a failed build is still rebuilt by removing `agent:failed` and the existing tests stay unchanged |
| Q5. A failed build that blocks the next one | Rename the old branch to `archive/...`, ntfy when a start fails, delete nothing | ntfy only; also delete old worktrees | Gets past the block on its own and keeps "archive, do not delete"; old worktrees only cost disk |

## Design

Nothing visible to users.

## Open questions
