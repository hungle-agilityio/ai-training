# Intent: pr-parallel-guard

## Problem

The loop builds two issues at once. Each pull request is built and checked against the `main` of the moment it started. When the first one is merged, the second one may clash with it or be quietly wrong on the new `main`, and its verify report and CI still show the old picture. Nothing on GitHub stops a merge of a pull request that is behind `main`, a `Depends on` with two numbers only waits for the first one, and nobody is told when `main` turns red after a merge.

## Goal

Two builds that touch the same files never run at the same time, a pull request is merged only when it is up to date with `main` and green, a conflict is fixed by the loop on request, and a red `main` stops new builds and tells the owner.

## Users

The owner, who merges the loop's pull requests; the loop (the tick and `work-queue`); the Project threads that merge on the owner's OK.

## Out of scope

- Any change to the app (`reviewradar/`, `reviews/`).
- Rebasing or force-pushing loop branches.
- A new verify report after a clean update of the branch (CI on the new head is enough, Q3).
- Changing CI itself (`.github/workflows/checks.yml` already runs on every push to `main`).
