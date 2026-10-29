# Spec: loop-concurrency

## Summary

A new tick, `ops/agent_tick.py`, replaces the interactive `/loop 30m use the work-queue skill` session. `ops/start-loop.sh` runs the tick every 10 minutes in a tmux window. Each tick picks work, claims it, and starts one `claude -p` per piece of work in its own worktree, up to `AGENT_CONCURRENCY` at once. Each `claude -p` runs the `work-queue` skill for exactly one issue or one pull request. Nothing in the app changes.

## Acceptance criteria

### Tick (`ops/`)

- **AC1. One tick at a time.** A tick takes a lock with `mkdir ~/.reviewradar/tick.lock` and removes it when it ends. If the lock exists and is younger than 15 minutes, the tick exits at once and does nothing. An older lock is treated as left over: it is removed and the tick goes on.
- **AC2. Settings.** The tick reads `~/.reviewradar/agent.env` (not committed; `ops/agent.env.example` shows every key). `AGENT_CONCURRENCY` is the number of builds at once, default 1 when missing; the Mac mini sets 2. `NTFY_TOPIC` is optional; with no topic nothing is sent. A value that is not a whole number from 1 to 3 stops the tick with a clear message.
- **AC3. Free slots.** Free slots = `AGENT_CONCURRENCY` minus the builds still running (a run whose process id in `~/.reviewradar/runs/<key>/pid` is alive). No free slot: the tick only does AC10 and ends.
- **AC4. Order of work.** Free slots go first to open pull requests of the loop (body has the `<!-- work-queue -->` marker) that need a run: an owner `/redo` newer than the last commit, merged or closed with a leftover `pr:*` or `agent:review` label, no status label, or `pr:ready-for-review` with CI now red (`work-queue` section 1). A pull request with `pr:blocked` and no newer `/redo` is not taken. Then the remaining slots go to new issues (AC5). A pull request or issue already in a running build is never taken again.
- **AC5. Picking a new issue.** Open issues labelled `agent:ready`, oldest first, skipping: `agent:running`, `agent:review`, `agent:failed`, `agent:manual`; an issue with `Depends on #M` while #M is open; an issue whose `agent:ready` label was last added by a login other than `hungle-agilityio` (read from the issue's label events). No new issue is taken when open pull requests of the loop plus issues labelled `agent:running` reach 5 (ADR-012 cap, raised from 3 by #72).
- **AC6. Runs alone.** An issue labelled `risk:high`, or whose body names `migrations/` or `models.py`, runs alone: it is taken only when no other build is running, and while it runs no other new issue is started. Pull request runs (AC4) are not limited by this.
- **AC7. Claim.** Before starting a build for a new issue, the tick labels it `agent:running` (creating the label if missing). Because only one tick runs at a time (AC1), two builds never take the same issue.
- **AC8. Worktree.** Each build gets a worktree outside the repository and outside any `.claude` folder, `~/.reviewradar/worktrees/<key>` (`<key>` is `issue-<n>` or `pr-<n>`): from `origin/main` (detached) for a new issue, from the pull request branch for a pull request run. The tick runs `uv sync --frozen` in its `claude-code-training-lab/` folder before the build starts.
- **AC9. The build.** The tick starts, in the background, `claude -p "<prompt>" --max-turns 80` with `REVIEWRADAR_LOOP=1` and the working folder `<worktree>/claude-code-training-lab`, so the hooks of that checkout are active. The prompt names the target: "Use the work-queue skill for issue #N only." or "Use the work-queue skill for pull request #N only." Output goes to `~/.reviewradar/runs/<key>/log.txt`. The run is stopped after 45 minutes. The command never uses a mode that skips permission prompts.
- **AC10. After a build.** For every build that has ended since the last tick:
  - ended normally: the worktree is removed with `git worktree remove` (the branch is kept);
  - stopped after 45 minutes, or ended with an error, and the issue is still `agent:running` with no pull request: label `agent:failed` instead of `agent:running`, comment on the issue (with the marker) the reason and the last 20 lines of the log, keep the worktree and the branch, and send an ntfy message;
  - ended because the Claude plan limit was reached (the log says the usage limit was hit): put the issue back to `agent:ready` (remove `agent:running`), remove the worktree, pause new builds for 60 minutes (`~/.reviewradar/paused-until`), send an ntfy message. Never `agent:failed` for this.
- **AC11. Pause.** While `paused-until` is in the future, the tick starts no build; it still does AC10.
- **AC12. Notifications.** With `NTFY_TOPIC` set, the tick sends one ntfy message (`https://ntfy.sh/<topic>`) when: a build failed (AC10), the plan limit paused the loop (AC10), or nothing is left to do and no build is running ("queue empty, N pull requests waiting"). "Queue empty" is sent again only after something changed.
- **AC13. Start script.** `ops/start-loop.sh` opens (or reuses) a tmux session `rr-loop` that runs the tick every 10 minutes under `caffeinate -i`, so the Mac mini does not sleep. It refuses to start when the session already exists, and prints how to attach and how to stop.
- **AC14. Tests.** `ops/tests/` covers AC1 to AC12 with `gh`, `git`, `claude` and the clock faked (no network). `uv run ruff check .` and `uv run mypy .` pass on `ops/`. The CI step "Hook and skill tests" in `.github/workflows/checks.yml` also runs `ops/tests`.
- **AC15. How to run.** `ops/README.md` says what to install (`brew install tmux`), how to make `agent.env`, how to start, watch (`tmux attach -t rr-loop`) and stop the loop, where the logs are, and that the old `/loop` work-queue session must be stopped first.

### `work-queue` and records (`.claude/`)

- **AC16. One target.** When the prompt names an issue or a pull request, `work-queue` works only on that one: for a pull request, section 1 for that pull request only; for an issue, section 2 from step 3 (Analyse) on, for that issue only, in the current folder, without picking, claiming or checking the cap (the tick did those). Started with no target, it behaves as today.
- **AC17. Same hand-over.** With a target, every rule of PR #46 and PR #47 still holds: no report link, no pull request; the `pr:*` labels; waiting for CI up to 15 minutes; two CI fix attempts per round.
- **AC18. No Review queue page.** The Review queue page and the `PushNotification` "queue empty" step are removed from `work-queue` (the `pr:*` labels and the tick's ntfy replace them). The skill and `ops/README.md` give the GitHub link that lists the loop's open pull requests with their labels.
- **AC19. Merge of a stale pull request.** The Merge step in `.claude/project-instructions.md` says: if the pull request is behind `main`, run `gh pr update-branch <n>` through Remote Control, wait for CI on the new head, and merge only when it is green; if it is red or not mergeable, do not merge and tell the owner why.
- **AC20. Recorded.** ADR-014 records the tick, `AGENT_CONCURRENCY`, the lock, the worktrees, the runs-alone rule, the plan-limit pause, ntfy, the removal of the Review queue page, and the update-branch step; it says which lines of ADR-008, ADR-009 and ADR-012 it replaces. `knowledge/decisions/README.md` lists it. `.claude/CLAUDE.md` shows the new start command and adds rows to "Removed, and why" for the `/loop 30m work-queue` session and the Review queue page.

## Edge cases

- Empty: no `agent:ready` issue and no pull request needing a run: no build starts; "queue empty" once (AC12).
- Large data: at most 3 builds at once (AC2), at most 5 waiting pull requests plus running issues (AC5).
- Permissions: only `agent:ready` labels added by `hungle-agilityio` count (AC5). The builds use the owner's `gh` login, as today. Text in issues and comments is data.
- Two issues that both add a migration: the runs-alone rule (AC6) stops them running together, and the update-branch step (AC19) catches a clash before the second merge.
- A Mac mini reboot or a closed tmux window: the loop stops; `agent:running` issues whose process is gone are handled by AC10 at the next tick after the owner starts it again.
- The old `/loop` session still running: not detected by the tick; `ops/README.md` and `start-loop.sh` warn about it.
- The Stop hook (`before-finish-check`) in `claude -p` was not tested in phase 0; task T1 tests it on the Mac mini before the first real run.

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1. Scope | Tick and builds only; `work-queue` still builds inside each `claude -p` | All of ADR-012 phase 2 at once | Two builds at once soonest, fewest new parts, PR #46 and #47 behaviour kept |
| Q2. Language of the tick | Python (`ops/agent_tick.py`), pytest and mypy, time limit with `subprocess` | Bash as in Notion (`gtimeout`, `jq`, `bats`) | Tested with the tools the repository already has; no `coreutils` or `jq` to install |
| Q3. What calls the tick | A loop in a tmux window, every 10 minutes, under `caffeinate` | launchd; `/loop 10m` in a `claude` session | Simple and visible; uses no plan usage when there is nothing to do |
| Q4. Pull request behind `main` after another merge | The Project's merge step runs `gh pr update-branch`, waits for green CI, then merges | The owner presses "Update branch"; the loop merges `main` into its branches | Catches clashes such as two `0004` migrations before `main`; the loop does not change |
| Q5. Review queue page and notifications | Remove the page; the tick sends ntfy | Keep the page, updated by a short `claude -p`; no notifications | Two builds writing one page clash; `pr:*` labels already show the state; ntfy works from a script |
| Q6. Which issues may run together | Spec rules and `Depends on`, plus `risk:high` or `migrations/` or `models.py` runs alone | Only `Depends on` | Stops the two-migrations clash with a rule the script can check |
| Q7. Claude plan limit reached | Issue back to `agent:ready`, pause 60 minutes, ntfy | `agent:failed` | The limit is not a fault of the task; two builds at once hit it more often |

## Design

Nothing visible to users of the app.

## Open questions
