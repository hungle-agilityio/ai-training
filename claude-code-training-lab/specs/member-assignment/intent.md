# Intent: member-assignment

## Problem

The loop on the Mac mini builds every open issue labelled `agent:ready`. It never reads who an issue is assigned to. When a team member takes a task or a whole epic to do by hand, the loop can still start the same issue, so two people (or a person and the loop) build it at once. There is no agreed way for a member to claim a task, give it back or hand it to someone else. A member's pull request merged into an epic branch is not seen by the tick, so the later tasks of that epic wait for ever.

## Goal

1. An issue assigned to a team member (any login other than the owner `hungle-agilityio`, whose login the loop uses) is that member's work, and the loop never starts it. An epic assigned to a member gives that member every task of the epic, unless a task is assigned to another member.
2. A member claims a task by assigning themselves, gives it back by removing themselves, and hands it off by changing the assignee; no label changes.
3. A member's pull request for a task of an epic goes into the epic branch, the owner clicks Merge, and the tick marks the task done in the epic so the next tasks start.

## Users

The owner, who hands work to the loop or to members; team members, who work from GitHub and their own Claude Code sessions with the repository's CLAUDE.md and `.claude/rules/` (the Claude Code Project is private to the owner); the loop, which builds the rest.

## Out of scope

- Giving members access to the repository or the Project; the owner adds collaborators on GitHub.
- Members handing issues to the loop: only the owner's `agent:ready` starts a build (unchanged, `labelled_by_owner`).
- The tick merging a member's pull request: the owner clicks Merge (unchanged for pull requests without the work-queue marker).
- Stopping a loop build that is already running when a member claims the issue.
- Giving one task of a member's epic back to the loop while the member stays on the epic.
- The template repository `agent-flow-starter`: a separate request later.
