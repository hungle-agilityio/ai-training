# Intent: no-manual-label

## Problem

Some issues cannot be built by the loop. When an issue touches `.claude/`, `.github/`, the flow plugin, a gate file (`pyproject.toml`, `uv.lock`, `conftest.py`, ...) or an existing protected test, `route_issue.py` labels it `agent:manual`. When it touches a file with no `Edit(...)` allow rule, it gets `agent:needs-permission`. The loop skips both, so the owner has to start a session by hand on the Mac mini, build the change and merge it. Most flow work ends up this way.

## Goal

Every issue gets `agent:ready` and the loop builds it. A build may change exactly the files its issue lists, guarded files included. It can never switch its own guards off, and the owner sees every guarded file it changed when reviewing the pull request.

## Users

The owner, who writes requests and reviews pull requests. The loop on the Mac mini, which builds the issues.

## Out of scope

- Deleting the `agent:manual` and `agent:needs-permission` labels on GitHub (they stay, unused; archive, not delete).
- Rewriting old specs that mention `agent:manual` (they stay as history).
- Changing who merges: build pull requests still merge only on the owner's approval comment (ADR-016) or through the epic pull request (ADR-022).
