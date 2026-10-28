# Intent: pr-status-labels

## Problem

The owner reviews the pull requests the loop opens, but a pull request does not say whether it is waiting for the owner, being fixed by the loop, or stuck. Today only the issue carries a status (`agent:running`, `agent:review`, `agent:failed`). The loop never reads CI, so a pull request whose checks went red still looks ready.

## Goal

Every open pull request of the loop carries exactly one status label, set and changed by the loop, so the owner filters `label:pr:ready-for-review` on GitHub to see what waits for them, and the Project's Status reads the same labels.

## Users

The owner (reviews and merges), the `work-queue` loop on the Mac mini (sets the labels), the Project (reads them for Status).

## Out of scope

- Draft pull requests, or more than one status label on a pull request.
- Changing the issue labels `agent:*`; they stay as they are.
- A hook that limits `gh pr edit` to labels.
- The loop scripts of ADR-012 phase 2; they carry these rules over when they are built.
- Merging: the loop still never merges.
