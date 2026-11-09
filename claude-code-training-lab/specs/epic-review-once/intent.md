# Intent: epic-review-once

## Problem

The owner reviews and approves every task pull request of an epic on its own. Epic #348 (three tasks) needed three approvals, and a five-task epic needs five, often hours apart. The epic branch of ADR-021 only lets tasks build on each other; it never reaches `main`, so it cannot be the thing the owner reviews.

## Goal

The tasks of an epic finish without the owner: each task pull request goes into the epic branch and the tick merges it there once its checks and verify report are good. When every task is in, the tick opens one pull request from the epic branch into `main`; the owner reviews that one, approves it, and then releases with "phát hành".

## Users

The owner (reviews once per epic), the loop (builds and merges tasks into the epic branch).

## Out of scope

- Tasks without an epic: unchanged (one pull request into `main` each, ADR-016, ADR-018).
- The release (`ops/release.py`, ADR-017): unchanged.
- Automatic review of task pull requests by another model.
