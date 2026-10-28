# Intent: loop-concurrency

## Problem

The owner hands over several `agent:ready` issues at once, but the loop on the Mac mini builds one issue at a time: one interactive session runs `/loop 30m use the work-queue skill` and takes a single issue per run. Independent issues wait in line, and a run has no time limit, so a stuck run holds up everything behind it.

## Goal

A tick script on the Mac mini starts up to two builds at the same time, each in its own `claude -p` and its own git worktree, with a time limit, and never lets two builds take the same issue. Inside each build the `work-queue` skill still does the work, so the pull requests look and behave as today (verify report link, `pr:*` status labels). This is the smallest working part of phase 2 and phase 5 of ADR-012.

## Users

- The owner: starts the loop on the Mac mini, reviews and merges the pull requests.
- The Project: posts the issues, merges on the owner's "ok".
- Nobody using the ReviewRadar app sees a change.

## Out of scope

- The separate read-only review `claude -p` with `VERDICT`, the committed `plans/issue-N.md`, the new Gate 2 report, automatic risk flags (later phases of ADR-012).
- `agent:needs-info` and `/answer`, the limit of 3 `/redo` rounds, `/replan`, the `allow-test-edit` label.
- Removing the `work-queue` skill.
- Starting the loop again by itself after a power loss or reboot (tier 2).
