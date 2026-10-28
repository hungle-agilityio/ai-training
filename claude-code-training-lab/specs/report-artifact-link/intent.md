# Intent: report-artifact-link

## Problem

The owner reviews every loop pull request from the verify report, and expects it as an online link (a private artifact). PR #41 had none: its body said "not shared as a link" and pointed to a file on the Mac mini. The share gate allowed the report, but the loop never called the Artifact tool (`out/artifact-publish.log` has no line for that run). Interactive sessions on the Mac mini did publish (log lines on 2026-10-19, 10-22, 10-26). `Artifact` is not in the allow list of `.claude/settings.json`, so each publish needs a permission prompt, and the unattended loop never asks one. Nothing checks that a pull request carries the link, so a Project thread had to publish it by hand.

## Goal

Every pull request the loop opens carries the private artifact link to its verify report. When a link cannot be made, the loop opens no pull request and says why on the issue.

## Users

The owner, who reviews and merges the loop's pull requests, often from the phone.

## Out of scope

- Pull requests opened by hand in an interactive session (they keep the "not shared" option).
- The loop scripts of ADR-012 (`claude -p` per issue). When they are written they must allow the same tool (`--allowedTools Artifact`); that belongs to their own issue.
- Publishing old reports, or changing the report page itself.
- Any change to the masking check or to the share gate conditions.
