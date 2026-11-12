# Intent: member-file-hold

## Problem

When a team member claims a task (an assignee other than the owner, on the issue or on its epic, ADR-028), the loop skips that task, but the files the task will change are not held. The tick holds a file only for an issue labelled `agent:running` or `agent:review`. So the loop can start another task that changes the same file while the member is still working on it, and the two pull requests clash (retro issue #489).

## Goal

A task a member has claimed holds the files in its `## Files likely touched` section, the same way a running build does, until the issue is closed or the member is removed. The tick's log and its "waiting" message name the member, so the owner knows whom to ask.

## Users

The owner, who reads the tick's log and the "waiting" phone message; team members, whose work no longer clashes with the loop's.

## Out of scope

- How a member claims or gives back a task (ADR-028, unchanged).
- Holding files of a member's work that is not an open issue (a branch or a pull request without an issue).
- Any change to the app.
