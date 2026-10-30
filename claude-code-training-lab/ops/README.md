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

- First, open loop pull requests with an owner approval comment are merged when the checks of ADR-016 hold (see Review from the phone).
- Pull requests of the loop that need a run go first (an open change request, merged or closed with a leftover label, no status label, ready but CI red), then the oldest `agent:ready` issues.
- An issue is skipped when it is `agent:running`, `agent:review`, `agent:failed` or `agent:manual`, when a `Depends on #M` is still open, or when `agent:ready` was added by anyone but `hungle-agilityio`. No new issue when waiting pull requests plus running issues reach 10.
- An issue labelled `risk:high`, or whose body names `migrations/` or `models.py`, runs alone.
- A build that times out or fails before its pull request: the issue gets `agent:failed` and a comment with the last 20 log lines; the worktree stays. The plan limit: the issue goes back to `agent:ready` and new builds pause for 60 minutes.

## Review from the phone

Review a loop pull request on GitHub like any other (ADR-016):

- **Approve:** write a comment on the pull request whose whole text is one of `/merge`, `merge`, `lgtm`, `approved`, `approve`, `looks good`, `look good`, `ok`, `duyệt`, `ship it` (any case, a trailing `.!,:;` is fine). "lgtm but rename X" is a change request, not an approval. The tick merges at its next run when the approval is newer than the loop's last commit (an update from `main` does not count), the pull request has `pr:ready-for-review`, every check is green, no change request is open and no run of it is in progress. Behind `main`: it updates the branch and merges at a later tick. A conflict: it posts `/redo merge origin/main into this branch and fix the conflict` and you approve again after that round. Red CI, `DIRTY`, `BLOCKED` or a failed merge: no merge and one message "not merged: <reason>". After the project chat approves, a thread posts `/merge` and runs one tick.
- **Ask for a change:** any other comment on the pull request, a comment on a line, or a comment starting with `/redo` on the issue. Only comments made after the pull request was opened count.
- **Marks**, all made with your login: 👀 the loop is working on it; 🚀 done (a reply says `Done in <sha>: ...`), or on an approval, merged; 😕 the loop cannot do it (the reply says why), or on an approval, not merged, so approve again. Add 🚀 yourself to make the loop skip a comment.

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

## Phone messages (ntfy and Slack)

Every message goes to ntfy when `NTFY_TOPIC` is set and to Slack when `SLACK_WEBHOOK_URL` is set (both, one or none). A failed Slack post writes the log line `Slack post failed` and does not stop the tick.

**Slack, once:** create a Slack app (api.slack.com/apps, From scratch), turn on **Incoming Webhooks**, **Add New Webhook to Workspace** and pick a channel, copy the webhook URL into `~/.reviewradar/agent.env` as `SLACK_WEBHOOK_URL=...` (never into the repository), then set that channel's notifications to **All new messages** in the Slack app on the phone.

| Message | When |
|---|---|
| `ReviewRadar started #<n>: <issue title>` | the tick started an issue build |
| `ReviewRadar working on PR #<p> (<k> change requests open)`, or `(CI)` | the tick started a pull request run; `<k>` counts the owner's `/redo` comments newer than the last commit |
| `ReviewRadar PR #<p> needs you: <pr:blocked or pr:ci-failed>` and the link | once per pull request, label and head commit |
| `ReviewRadar PR #<p> merged (#<n>); main is now <sha>`, or `...; main checkout not updated: <reason>` | a loop pull request was merged (by anyone), announced once after the tick pulled `main`; the first run only records the merged ones |
| `ReviewRadar waiting: <w> pull requests open (limit 10), <k> ready issues not started` and the link | nothing started or running while ready issues wait; again only when the text changes |
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

## Release

`uv run python ops/release.py` turns the newest `main` commit into a sprint release. Run it by hand in the main checkout on the Mac mini, on the owner's request; the loop never runs it. It fetches `origin`, then in one `git push --atomic` (no force, `main` untouched) creates the branch `release/sprint-N` (one more than the highest on `origin`), an annotated tag `vYYYY.MM.DD` (Vietnam date, `.2`, `.3` for more that day) and moves `deploy`, which Render follows. It then prints the branch, the tag, the commit, the merged pull requests since the last release and `Render deploys branch deploy after Checks pass.`

`--dry-run` prints the same plan (commit, branch, tag, pull requests) and pushes nothing.

It refuses with exit 1 and one line, pushing nothing, when the newest `Checks` run of the commit is missing, still running or not successful; when `origin/deploy` already points at the commit (`nothing new to release`); or when `origin/deploy` is not an ancestor of the commit.

## Tests

`uv run pytest ops/tests -q --no-cov` (gh, git, claude and the clock are faked; CI runs them in "Hook and skill tests").
