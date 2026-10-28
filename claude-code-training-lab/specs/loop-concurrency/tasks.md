# Tasks: loop-concurrency

Both tasks change the loop itself, so the loop may not build them (ADR-012, "Phases"): they are built in an interactive session on the Mac mini. They share no file and can be built in either order; the trial run needs both.

## T1: Tick that starts up to two builds at once

- **ACs:** AC1 to AC15
- **Files likely touched:** `ops/agent_tick.py`, `ops/start-loop.sh`, `ops/agent.env.example`, `ops/README.md`, `ops/tests/test_agent_tick.py`, `ops/tests/__init__.py`, `.github/workflows/checks.yml` (one line in "Hook and skill tests")
- **Depends on:** none
- **Risk:** high
- **needs-ui:** no
- **Label:** `agent:manual` (the loop does not build its own machinery)
- **Note:** before the first real run, check on the Mac mini that the Stop hook `before-finish-check` runs in `claude -p` (not tested in phase 0).

## T2: work-queue takes one target from the tick; ADR-014

- **ACs:** AC16 to AC20
- **Files likely touched:** `.claude/skills/work-queue/SKILL.md`, `.claude/project-instructions.md`, `.claude/knowledge/decisions/ADR-014-tick-runs-builds-in-parallel.md`, `.claude/knowledge/decisions/README.md`, `.claude/CLAUDE.md`
- **Depends on:** none
- **Risk:** medium
- **needs-ui:** no
- **Label:** `agent:manual` (changes `.claude/`)
- **Note:** after the merge, the owner pastes the new `.claude/project-instructions.md` into the Project settings.

## After both are merged (owner, not an issue)

1. On the Mac mini: `brew install tmux`; make `~/.reviewradar/agent.env` from `ops/agent.env.example`; install the ntfy app and subscribe to the topic.
2. Stop the old `/loop 30m use the work-queue skill` session.
3. Trial: one Easy issue with `AGENT_CONCURRENCY=1`, then two independent Easy issues with `AGENT_CONCURRENCY=2`.
