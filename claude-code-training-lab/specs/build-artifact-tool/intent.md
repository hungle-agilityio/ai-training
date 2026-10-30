# Intent: build-artifact-tool

## Problem

A loop build on the Mac mini sometimes starts without the `Artifact` tool. It builds and checks the issue, then cannot publish the verify report, so by the rule "no link, no pull request" it ends `agent:failed` although the code passed (#64 on 2026-10-30 03:12Z, #103 at 07:31Z). A retry usually works, but the work of the failed run is lost, and the run leaves no record of which tools the session had.

## Goal

A build that starts without the `Artifact` tool is stopped within seconds and started again, before it spends any work. Every build keeps a full session log, so the next failure shows its cause.

## Users

The owner, who reads the issue labels, the ntfy messages and the logs in `~/.reviewradar/runs/`.

## Out of scope

- Resuming a failed build from the report step on its kept branch.
- A fallback report without an artifact link; "no link, no pull request" stays.
- Any change under `.claude/` (skills, settings, hooks, KNOWN_PITFALLS).
