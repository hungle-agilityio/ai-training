# ADR-004: Claude may reach only one GitHub repository

- Status: Accepted
- Date: 2026-10-16

## Context

The `gh` login had the `repo` scope on every repository of the account, and the SSH key reaches all of them. A wrong command could touch another repository.

## Decision

Three layers: a fine-grained token limited to this repository for the API and the MCP server; the hook `before-github-command-check` plus allow, ask and deny lists in `.claude/settings.json`; and the text in `rules/security.md`. The SSH key stays registered; for `git` the hook is the limit. The repository name is read from `.claude/hooks/github-allowed-repo.txt`.

## Consequences

A blocked command is reported to the user, never worked around. The hook fails closed, is covered by tests, sees only shell commands that Claude runs (not a script that Claude runs, nor commands the user types), and a change of settings needs a new session.
