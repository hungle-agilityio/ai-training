# Intent: project-layout

## Problem

The owner started a new project (`o-living-with-nature`) with `ops/bootstrap.py` and the kickoff
guide. Its root holds thirteen entries that mix three things: the agent flow (`ops/`, `plugins/`,
`specs/`), the framework's default folders (`apps/`, `config/`, `static/`, `templates/`, `tests/`)
and documents (`docs/`). It is not clear which folder is project setup and which is the product's
code. Some folders are empty or unused, and nothing says what must not be pushed. The layout also
assumes Python and Django, but the flow should work for any stack.

## Goal

A new project made by bootstrap has a small, fixed root that reads the same for every stack:
the product's code in `src/` (by feature, tests beside it), documents in `docs/`
(`intent/`, `specs/`, `plans/`, `decisions/`, `architecture.md`), project scripts in `scripts/`,
and every piece of the agent flow inside the hidden `.flow/` folder, next to `.claude/` and
`.github/`. What should not be pushed is in `.gitignore`. ReviewRadar keeps its own layout.

## Users

The owner, when starting a new project on the Mac mini, and the loop that builds its issues.

## Out of scope

- Moving ReviewRadar (this repository) to the new layout (decision Q1).
- Rewriting the kickoff instructions and the Notion page "Những gì cần cho một dự án mới"; the
  Project thread does that after the epic is merged.
- Re-laying out `o-living-with-nature`; a thread does that on the Mac mini after the epic is merged
  (decision Q6).
- Writing the app skeleton of a stack (that stays a kickoff step); bootstrap only fixes where it
  goes.
