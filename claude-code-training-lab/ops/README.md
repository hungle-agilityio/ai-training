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
- An issue is skipped when it is `agent:running`, `agent:review`, `agent:failed` or `agent:manual`, when a `Depends on #M` is still open, or when `agent:ready` was added by anyone but `hungle-agilityio`. No new issue when waiting pull requests plus running issues reach 5.
- An issue labelled `risk:high`, or whose body names `migrations/` or `models.py`, runs alone.
- A build that times out or fails before its pull request: the issue gets `agent:failed` and a comment with the last 20 log lines; the worktree stays. The plan limit: the issue goes back to `agent:ready` and new builds pause for 60 minutes.

## Guards

The tick does not start a ready issue (ADR-015):

- while any issue named on a `Depends on` line is still open (every `#number` on the line counts);
- while one of its files (the backticked paths in the bullets of `## Files likely touched`) is also a file of an open `agent:running` or `agent:review` issue, or of an issue chosen earlier in the same tick: the log says `issue-<n>: waits for #<m>, which also touches <path>`;
- with other builds, when its body lists no file: it runs alone, like `risk:high`;
- in a tick where the latest completed `Checks` run on `main` is not green: pull request runs still start, and ntfy says `main is red at <sha>: <run url>` once per commit. An unreadable run counts as green, with a log line.

The log lines are in the tmux window and in the tick's output.

## Self-repair

- **Pull `main`.** After taking the lock, the tick fast-forwards the main checkout (`git fetch origin main`, `git merge --ff-only origin/main`) when it is on `main` with no tracked changes; the new code runs from the next tick. Another branch, tracked changes or a failed fetch or fast-forward: no pull and one ntfy per reason.
- **Only the owner's pull requests.** A pull request from a fork, or opened by another login, is never the loop's, even with the marker.
- **Plan limit.** Recognised also as `extra_usage`, `usage_limit` and "hit your ... limit", whatever the exit code, as long as the build had not handed over: the issue goes back to `agent:ready` and builds pause 60 minutes.
- **Handed over.** An open issue with `agent:ready` and `agent:review` loses `agent:ready`, so a closed pull request is not rebuilt; add `agent:ready` again to rebuild it. `agent:failed` keeps `agent:ready`.
- **`archive/` branches.** When a kept worktree is moved aside, its branch (and, for an issue, every local `bug/<n>-`, `feat/<n>-`, `task/<n>-` branch) is renamed `archive/<branch>-<unix time>`. Nothing is deleted.

## Phone messages (ntfy)

Sent only when `NTFY_TOPIC` is set.

| Message | When |
|---|---|
| `ReviewRadar PR #<p> opened for #<n> (<status label>)`, the pull request link, `Report: <link>` | an issue build ended and an open loop pull request closes that issue (also after an error or a timeout that came after the pull request) |
| `ReviewRadar PR #<p> updated for #<n> (<status label>)`, the same two links | a pull request build (a `/redo` or a CI fix) ended normally and the pull request is still open |
| `ReviewRadar build for issue #<n> failed: <reason>` | an issue build ended without a pull request |
| `ReviewRadar build for pull request #<p> <reason>` | a pull request build failed or timed out |
| `ReviewRadar loop paused 60 minutes: plan limit reached (<key>)` | the Claude plan limit was reached |
| `main is red at <sha>: <run url>` | the latest completed `Checks` run on `main` is not green; once per commit |
| `ReviewRadar main checkout not updated: <reason>` | the tick could not pull `main`; once per reason until a pull succeeds |
| `ReviewRadar build for <issue #n \| pull request #n> did not start: <step> failed` | a start failed; once per key and step until that key starts |
| `ReviewRadar queue empty, <w> pull requests waiting` | nothing to start and nothing running; again only when the text changes |

The loop's open pull requests with their status labels: <https://github.com/hungle-agilityio/ai-training/pulls?q=is%3Apr+is%3Aopen+%22work-queue%22+in%3Abody>

## Tests

`uv run pytest ops/tests -q --no-cov` (gh, git, claude and the clock are faked; CI runs them in "Hook and skill tests").
