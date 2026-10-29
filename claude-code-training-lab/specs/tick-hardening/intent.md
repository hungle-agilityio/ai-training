# Intent: tick-hardening

## Problem

The tick (`ops/agent_tick.py`) has five gaps that make the loop stop or go wrong without anyone being told:

- The repository is public. Any pull request whose body holds the line `<!-- work-queue -->` counts as a loop pull request, also one from a stranger's fork. Three such pull requests stop the loop (the cap of 3), and a fake `Closes #N` hides a failed build of a real issue.
- The tick runs from the main checkout on the Mac mini, which nothing pulls. After a merge, in particular one clicked on GitHub, the tick keeps running the old code, so a fix to the tick (#68, #70) does not take effect.
- The plan limit is missed when Claude stops with `extra_usage_unavailable`, or when the build exits with code 0. The issue then gets `agent:failed` and the loop does not pause.
- `agent:ready` is never removed. When the owner closes a pull request to reject it, the issue keeps only `agent:ready` and the tick builds it again within 10 minutes.
- A failed build keeps its worktree, and that worktree keeps its branch checked out. The next run on the same pull request cannot start (`'<branch>' is already used by worktree`), a new build of the same issue cannot create its branch again, and the tick only writes a log line every 10 minutes.

## Goal

The tick works only on the owner's own pull requests, runs the code on `main`, pauses on the plan limit, leaves a rejected issue alone, and gets past a failed build on its own. When it cannot do one of these, the owner gets one ntfy message.

## Users

The owner, who reads ntfy and merges; the tick on the Mac mini.

## Out of scope

- Any change to the app (`reviewradar/`, `reviews/`) or to `.claude/` (skills, hooks, project instructions).
- Starting the loop again after a reboot (launchd), and the narrow-screen check in the verify report: separate work.
- Deleting old worktrees or branches: they are kept (archive, do not delete).
- A branch that a failed build already pushed to GitHub without a pull request.
