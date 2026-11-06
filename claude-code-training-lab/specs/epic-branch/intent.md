# Intent: epic-branch

## Problem

The loop starts a task early only when exactly one of its dependencies is still open (ADR-018). A task that waits for two or more unreviewed pull requests stops until the owner has reviewed and merged them. On 2026-11-06 #242 of the epic "reply to reviews" (#236) waited for PR #251 and PR #252, both green and ready, while the owner had no time to review.

## Goal

Each epic gets one shared branch that holds every green, ready pull request of the epic. A task of the epic whose dependencies have such pull requests builds on that branch and goes on while the owner reviews. Every task still gets its own pull request with only its own diff, and `main` still receives only reviewed work.

## Users

The owner, who reviews and merges pull requests when there is time; the loop on the Mac mini, which builds the issues.

## Out of scope

- Merging the epic branch into `main`: work reaches `main` only through each task's own reviewed pull request.
- Tasks that belong to no epic: they keep the one-parent stacking of ADR-018.
- Any change to what users of ReviewRadar see.
