# Intent: loop-depends

## Problem

On 2026-11-02 the owner merged PR #134 (#131) and PR #140 (#130), the two dependencies of #132 and #133. The next tick merged both pull requests, then started two full Claude builds only to remove labels from those merged pull requests. They took both build slots, so #132 and #133 waited another tick. Before that, while #132 and #133 waited on their Depends on, the tick skipped them without a word, and its only message ("waiting: 1 pull requests open (limit 10), 2 ready issues not started") blamed the pull request limit. The owner could not see that the loop was waiting for a review and a merge, or which pull request to review first.

## Goal

A merged pull request never costs a build slot, and when ready issues cannot start, the owner gets one message that names each issue, what it waits for, and which pull request to review or merge first.

## Users

The owner, who reads ntfy and Slack on the phone and reviews and merges on GitHub.

## Out of scope

- Editing or removing the "Depends on" line of an issue (closing the dependency already satisfies it; the tick pulls main every tick).
- The pull request limit (`WAITING_CAP`) and its message, which stay as they are.
- The work-queue skill (`.claude/`): its "Merged or closed" step stays; it is just no longer started for that case.
- Merging, Gate 1 and Gate 2.
