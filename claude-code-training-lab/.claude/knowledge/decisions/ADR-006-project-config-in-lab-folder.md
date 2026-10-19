# ADR-006: Project configuration lives in the lab folder, sessions open there

- Status: Accepted
- Date: 2026-10-19

## Context

The git root is `ai-training/`, the project is the subfolder `claude-code-training-lab/`. GitHub reads `.github/` only at the git root. Claude Code reads `.claude/` and `.mcp.json` from the folder where a session is opened.

## Decision

`.github/` stays at the git root. `.claude/`, `.mcp.json` and the code stay in `claude-code-training-lab/`, and sessions are opened there. Moving everything to the root was rejected: it means moving `.claude/`, and rewriting the paths in hooks, settings and the project map, for no gain.

## Consequences

A session opened at the git root does not see the project's rules, skills, hooks or MCP server, and its memory folder is a different one. Commits made from the lab folder still cover the whole repository, but `git add .` stages only that folder: stage files outside it by name.
