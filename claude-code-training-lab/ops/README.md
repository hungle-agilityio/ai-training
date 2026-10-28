# The loop on the Mac mini

`agent_tick.py` is one tick of the loop. `start-loop.sh` runs a tick every 10 minutes in a tmux window. Each tick tidies the builds that ended, then starts up to `AGENT_CONCURRENCY` builds, each one `claude -p "Use the work-queue skill for issue #N only."` (or "pull request #N") in its own worktree, stopped after 45 minutes. Inside each build the `work-queue` skill does the work, as before. Spec: `specs/loop-concurrency/spec.md`; decision: ADR-014.

## Install once

1. `brew install tmux`
2. `gh auth status` shows the owner's login, and `claude` is logged in (a `claude -p "hi"` answers).
3. Make the settings file, which is not committed:

   ```bash
   mkdir -p ~/.reviewradar
   cp ops/agent.env.example ~/.reviewradar/agent.env
   ```

   Set `AGENT_CONCURRENCY` (1 to 3; the Mac mini uses 2) and, for phone notifications, `NTFY_TOPIC`, then subscribe to that topic in the ntfy app.

## Start, watch, stop

**First stop the old loop:** the interactive session that runs `/loop 30m use the work-queue skill` must not run next to the tick; the tick cannot see it, and both would take the same issues.

From this folder (`claude-code-training-lab/` of the main checkout):

```bash
ops/start-loop.sh
```

- Watch: `tmux attach -t rr-loop` (leave with Ctrl-b d).
- Stop: `tmux kill-session -t rr-loop`. A build already started runs to its end; the next start of the loop tidies it.
- One tick by hand: `uv run python ops/agent_tick.py`.

## Where things are

All under `~/.reviewradar/`:

| Path | What |
|---|---|
| `agent.env` | the settings |
| `runs/<key>/log.txt` | the output of a running build (`<key>` is `issue-<n>` or `pr-<n>`) |
| `runs/done/<key>-<time>/` | the folder of an ended build, log included |
| `worktrees/<key>` | the checkout of a build; kept after a failed build |
| `paused-until` | set for 60 minutes when the Claude plan limit is reached |
| `tick.lock` | present while a tick runs; one older than 15 minutes is left over |

## What a tick does

- Pull requests of the loop that need a run go first (an owner `/redo`, merged or closed with a leftover label, no status label, ready but CI red), then the oldest `agent:ready` issues.
- An issue is skipped when it is `agent:running`, `agent:review`, `agent:failed` or `agent:manual`, when a `Depends on #M` is still open, or when `agent:ready` was added by anyone but `hungle-agilityio`. No new issue when waiting pull requests plus running issues reach 3.
- An issue labelled `risk:high`, or whose body names `migrations/` or `models.py`, runs alone.
- A build that times out or fails before its pull request: the issue gets `agent:failed` and a comment with the last 20 log lines; the worktree stays. The plan limit: the issue goes back to `agent:ready` and new builds pause for 60 minutes.

The loop's open pull requests with their status labels: <https://github.com/hungle-agilityio/ai-training/pulls?q=is%3Apr+is%3Aopen+%22work-queue%22+in%3Abody>

## Tests

`uv run pytest ops/tests -q --no-cov` (gh, git, claude and the clock are faked; CI runs them in "Hook and skill tests").
