# Intent: build-trust

## Problem

The loop builds an `agent:ready` issue from start to pull request without a human in between. Three parts of a trusted build are missing (Day 13 audit, 2026-11-11). The plan the `planner` writes inside a build is never shown: the pull request has no plan, and nobody approves a plan before code is written, even on a `risk:high` issue. The test matrix of the spec (ADR-026) is planned before the build but nobody checks it after: the build never reads `## Test matrix rows`, the verify report checks only the ACs, and the same agent writes the tests and the code, so tests can follow the code instead of the requirement. Decisions taken during a build (an open point taken from the spec, a self-fix, the owner's answer to a `needs-decision` stop, a change request) live only in the issue or the pull request: `specs/<feature>/spec.md` stays as it was merged and no longer tells what was built.

## Goal

1. Every loop pull request shows the plan it was built from; a `risk:high` issue stops after planning until the owner approves the plan.
2. A separate test author writes the failing tests from the issue and its matrix rows before the code, and the verify report fails when a matrix row has no passing test.
3. Each task of a full-lane spec records its build decisions in `specs/<feature>/decisions/T<k>.md` in its own pull request, so the spec folder stays current.

## Users

The owner, who approves a risky plan before code and reads the plan, the matrix check and the decisions in one place; QA, who reads the matrix result; the loop, which builds.

## Out of scope

- Changing specs, issues or pull requests that already exist; the rules apply to issues created after this change.
- A plan stop for issues that are not `risk:high`.
- Claude Code's interactive plan mode (`--permission-mode plan`) in the loop: the stop is a label and a comment.
- Rewriting `spec.md` itself after Gate 1; decisions go in their own files and `spec.md` links them.
- The template repository `agent-flow-starter`: a separate request later.
