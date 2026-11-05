# Intent: bootstrap-gaps

## Problem

The owner starts a new project with `ops/bootstrap.py`. A test run on main (68e1072, again on
bada248) showed the copy is not ready to use: `uv sync --frozen` fails because there is no
`pyproject.toml`, the root `CLAUDE.md` still describes ai-training as a Django app and imports a
rule that is not copied, `.claude/settings.json` still allows only ReviewRadar's code folders (so
every new issue gets `agent:needs-permission`), CI runs tests that only exist in ai-training and
goes red, two copied texts point at `../plugins/agent-flow/`, and the printed install step
installs the plugin at user scope. Today the Notion guide fixes these by hand with a long prompt.

## Goal

One run of `bootstrap.py`, followed by the printed steps, gives a new repository whose first CI run
is green and whose first `agent:ready` issue the loop can build, with no hand fixes.

## Users

The owner, when starting a new project on the Mac mini.

## Out of scope

- Changing ReviewRadar's own files (`.claude/`, `CLAUDE.md`, `checks.yml`, `pyproject.toml`); only
  what bootstrap writes into the target changes.
- Making `ops/tests` run inside a new project.
- Projects that do not use Python and uv.
- Shortening the Notion page "Những gì cần cho một dự án mới" (done by the Project thread after
  the merge).
