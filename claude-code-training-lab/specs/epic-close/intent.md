# Intent: epic-close

## Problem

A task of an epic whose dependency is not merged yet opens its pull request into the epic branch (ADR-021, spec `epic-branch` AC7 to AC9). The tick moves that pull request to `main` only after the dependencies are merged. GitHub still shows a working Merge button on it. On 2026-11-06 the owner merged PR #319 (#313) and, ten seconds later, PR #320 (#317) with the Merge button, before the tick had moved #320 to `main`. #320 went into `epic/312-review-topics-what-customers-talk-about`, which never reaches `main`. #317 stayed open without an `agent:*` label, and its code was not on `main`. The same happened to PR #295 (#283) on 2026-11-06 and was fixed by hand with PR #304.

## Goal

A stacked pull request cannot be merged by mistake: it stays a draft until its base is `main`. If one is still merged into an epic branch, the tick opens a new pull request from the same branch into `main`, so the issue closes when that one is merged. Tasks still reach `main` and close one by one.

## Users

The owner, who reviews and merges pull requests on GitHub or with an approval comment; the tick on the Mac mini.

## Out of scope

- Merging the epic branch into `main`, or one final pull request per epic (option B, rejected 2026-11-09).
- Giving every pull request base `main` from the start (option C, rejected).
- A GitHub ruleset (the Mac mini token cannot create one).
- Anything users of ReviewRadar see.
