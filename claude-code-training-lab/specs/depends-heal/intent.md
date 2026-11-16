# Intent: depends-heal

## Problem

On 2026-11-16 the loop of a project built from the starter (epic #104 of o-living-with-nature) built T2 #105 before its base task T1 #107. The issue said `Part of the epic #104. Depends on #107.` on one line, and the tick only reads a `Depends on` line that starts the line, so it saw no dependency. The build found nothing of T1 on the epic branch, stopped with `needs-decision` and set `agent:failed`. The same parser runs in this repository (`ops/agent_tick.py`) and in the starter. Nothing checks the line before an issue is posted, and T2 and T3 had been created before T1.

Separately, a `needs-decision` stop waits for the owner until the owner adds `agent:ready` again. Inside an epic, every task that depends on the stopped one waits too, so the flow is blocked until the owner looks.

## Goal

The tick reads every dependency wherever it stands in the body, an issue with an unreadable dependency cannot be posted, and a task whose base task is not merged waits without failing. When a build sets `agent:failed`, the next tick starts a heal run that fixes the issue by itself (up to 3 rounds per issue, never in the forbidden cases), so the queue keeps moving without the owner. The owner sees every heal decision once, in the pull request.

## Users

The owner, who wants a loop that is not blocked by a failed task, and the Project threads that write issues.

## Out of scope

- Reading `tasks.md` of the spec from the tick (Q3, rejected).
- A heal run that writes code: it edits only the issue.
- Retrying transient failures differently: they keep `RETRIES = 3` as today.
- Changing the starter and O - Living in this repository: that is a follow-up through the Mac mini after T1 to T5 merge (Q4).
