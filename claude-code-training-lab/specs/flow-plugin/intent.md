# Intent: flow-plugin

## Problem

The flow's hooks, skills, slash commands and sub-agents live as copies in each repository's
`.claude/` folder. `ops/bootstrap.py` copies them into a new project, so every project gets its own
copy, and a fix in one never reaches the others. A loop pull request branch also runs its own
copy of the hooks, so a branch can carry a weaker guard than `main`.

## Goal

Everything generic that a new project needs from Claude Code (hooks, flow skills, commands,
sub-agents) ships as one Claude Code plugin, `agent-flow`, from a marketplace in this repository.
ReviewRadar uses the plugin instead of its own copies, and `ops/bootstrap.py` turns the plugin on
in a new project instead of copying files. A fix to the plugin reaches every project at its next
tick.

## Users

The owner (sets up projects, reviews and merges), the CLI loop on the Mac mini (`claude -p` builds),
interactive Claude Code sessions on the Mac mini and the MacBook.

## Out of scope

- Moving `ops/`, `ops/flow.toml`, `.claude/rules/`, `CLAUDE.md`, project instructions, ADRs,
  `settings.json` permissions, CI, labels or the app skills (`write-tests`, `diagnose-bug`,
  `check-in-browser`, `capture-before-after`) into the plugin: they stay with `bootstrap.py`.
- A new repository for the plugin, a public listing, or submitting it to a directory.
- Cloud Project threads: they load neither plugins nor repository skills, nothing changes there.
- Creating a real new project.
