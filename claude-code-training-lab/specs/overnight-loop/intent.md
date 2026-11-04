# Intent: overnight-loop

## Problem

The owner runs the loop overnight with two builds at a time and splits each epic into small tasks, one pull request each, so every pull request is easy to review. Two things stop the loop until the owner wakes up:

- A task that `Depends on` another task waits until the other task's pull request is reviewed and merged. Overnight nobody merges, so the dependent tasks of an epic never start.
- A task labelled `agent:failed` is never picked again (`agent:failed` is in `SKIP_LABELS` of `ops/agent_tick.py`). Some failures go away by themselves (a timeout, a build that started without the Artifact tool) or after main changes (#132 on 2026-11-02), but only the owner can restart them.

On top of that the tick stops starting issues when 10 pull requests are waiting (`WAITING_CAP`), which a night of small pull requests reaches.

## Goal

In the morning the owner finds one pull request per task, including the tasks that depend on a task not merged yet, each showing only its own change. A failed build was retried when a retry could help, and only the tasks that failed for good wait for the owner.

## Users

The owner, who starts the loop on the Mac mini in the evening, reads ntfy and Slack on the phone, and reviews and merges on GitHub in the morning.

## Out of scope

- Reading the reason of a failure from the build log.
- Starting a task on two or more unmerged parents.
- Syncing a child pull request each time its parent changes in review (the existing update from `main` does it after the parent merges).
- Merging without the owner's approval; the merge rules of ADR-016 stay.
- `AGENT_CONCURRENCY` (stays 1 to 3 in `agent.env`).
