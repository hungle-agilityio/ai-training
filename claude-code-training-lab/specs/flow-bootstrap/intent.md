# Intent: flow-bootstrap

## Problem

The owner wants to start a new project with the same flow (Project threads, spec pull requests, issues, the loop on the Mac mini, merge on approval, release). Today the flow only fits ReviewRadar: the repository, the owner login, the folder `claude-code-training-lab/`, the name "ReviewRadar", `~/.reviewradar`, tmux `rr-loop`, launchd `com.reviewradar.loop`, the check commands and a few Django rules are written into about 60 places in about 25 files (`/mnt/project-files/flow-portability/analysis.md`). Copying by hand means two copies of the tick to fix forever, and a second loop on the same Mac mini would write over the first loop's state, lock and tmux session.

## Goal

The flow reads its project values from one file, `ops/flow.toml`, and `ops/bootstrap.py` sets up a new repository from six values. The owner opens a new chat, gives the Notion page, and Claude runs bootstrap with those six values and walks through the printed manual steps. ReviewRadar behaves exactly as it does today.

## Users

The owner (sets up new projects, runs two loops on one Mac mini) and the Claude session that runs bootstrap for the owner.

## Out of scope

- Creating a real new project or repository in this epic (Q7).
- A shared limit across two loops (Q5); the owner keeps the total `AGENT_CONCURRENCY` at 2 to 3.
- Copying the Django-specific parts (app code, `architecture.md`, `domain.md`, `python.md`, the browser check, the sub-agents, `write-tests`, `diagnose-bug`, `capture-before-after`); the new project gets short stubs (Q1).
- Making the flow tooling itself run without Python: the tick, hooks and release stay Python and need `uv` on the Mac mini (Q1).
- Committing or pushing in the new repository (Q4).
- Manual GitHub setup that the Mac mini token cannot do (ruleset, token scope, Claude GitHub App): bootstrap prints these as steps.
