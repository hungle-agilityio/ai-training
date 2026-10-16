# ADR-002: GitHub is the only code host and tracker

- Status: Accepted
- Date: 2026-10-16

## Context

The project lived on a GitLab instance whose MCP connection no longer worked, and the work moves to a private GitHub repository under the account `hungle-agilityio`.

## Decision

GitHub is the only host and the only tracker. The repository is private and named `ai-training`. Claude uses the `gh` command now; the GitHub MCP server comes later. All GitLab files (pipeline, templates, MCP entry) are removed. The three old GitLab issue numbers stay in the issue index as history ("was GitLab #n").

## Consequences

The skills `create-issue` and `create-pull-request` use `gh`, keep the preview and the approval step, and never merge. Pushing and creating issues or pull requests wait for the user's approval of that item. The history of the lab folder moves to GitHub in the repository task.
