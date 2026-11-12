# Intent: epic-review-checklist

## Problem

The owner reviews one epic → `main` pull request (ADR-022) without a written checklist, and after a release nobody checks the released behaviour against the acceptance criteria on the live site (retro issue #488, Day 15 cross-review: "BA checks merged behaviour against the acceptance criteria"). `ops/live_check.py` (post-release epic, ADR-032) only checks that the main screens load.

## Goal

Every epic pull request opens with a short review checklist the owner ticks. After each release, once the live check passes, the release thread checks each user-visible AC of the released epics on the live site and turns every gap into a draft fast-lane issue the owner approves on a card.

## Users

The owner (reviewer and releaser).

## Out of scope

- Ticking the checklist automatically.
- Checking ACs of single (non-epic) pull requests after a release.
- Any change to the app or to `ops/live_check.py`.
