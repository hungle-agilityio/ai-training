# ADR-003: Repository layout and issue files

- Status: Accepted
- Date: 2026-10-16

## Context

The git root was the parent folder and the project a subfolder, so files that a host reads at the root (workflows, templates) would not have been found. Issues were four-file folders from a learning exercise, and one epic held 31 tasks.

## Decision

- The lab folder becomes the root of the GitHub repository. Its history is kept; old `#N` references in commit messages are rewritten to `GitLab #N`, and the author becomes the account's GitHub no-reply address.
- `docs/` is split into `docs/app/` (ReviewRadar) and `docs/learning/` (Claude Code training).
- One issue is one markdown file. An epic has between 3 and 10 children and is built from `docs/app/templates/epic.md`; the first epic was split into three.

## Consequences

Commit ids change when the history moves, so a backup of the old repository is kept outside the project. A commit has a `Part of` line only when an issue number exists. Status: accepted; the move itself is the repository task.
