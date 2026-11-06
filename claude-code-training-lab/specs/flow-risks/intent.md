# Intent: flow-risks

## Problem

The flow review of 2026-11-06 (main e81cde6) found no blocker but six risks that cost disk, builds or trust:

- A change to `plugins/agent-flow/` can be merged without a new version in `plugin.json` (fac7bbc), so the installed plugin silently stays old.
- The tick keeps the worktree of every failed build and never removes it: on the Mac mini `~/.reviewradar/worktrees` holds 29 folders, 7.4 GB, and the disk is 86% full.
- The tick decides that a build still runs only with `os.kill(pid, 0)`. After a restart a reused pid makes a dead build look alive, and its issue stays `agent:running`.
- An issue said "every existing test passes unchanged" while its change altered what four tests assert. The build stopped for the contradiction, and the tick started it again when `main` moved, one minute before the owner decided (#246: two wasted builds).
- `pytest ops` collects the bootstrap template `ops/bootstrap_stubs/test_flow_config.py` and fails, so builds report "main is red" by mistake.
- The docs say the tick runs every 10 minutes; it runs every 5.

## Goal

Each risk is closed by a check or a rule: CI goes red on a plugin change without a version bump, the tick tidies worktrees of closed work and ends runs older than the limit, a build that needs the owner is never retried on its own, issues name the existing tests they change, `pytest ops` passes on main, and the docs say 5 minutes.

## Users

The owner, who writes issues through the Project, reads ntfy and merges; the tick and the builds on the Mac mini.

## Out of scope

- Risk 7 (automatic login after a reboot) and risk 8 (old folders in the Mac mini's main checkout): the owner checks those by hand.
- Removing worktrees of failed builds whose issue is still open.
- The Project instructions on claude.ai (the owner edits them in Project settings).
