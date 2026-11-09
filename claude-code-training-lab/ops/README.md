# The loop on the Mac mini

`agent_tick.py` is one tick of the loop. `start-loop.sh` runs a tick every 5 minutes in a tmux window. Each tick tidies the builds that ended, then starts up to `AGENT_CONCURRENCY` builds, each one `claude -p "Use the work-queue skill for issue #N only."` (or "pull request #N") in its own worktree, stopped after 45 minutes. Inside each build the `work-queue` skill does the work, as before. Spec: `specs/loop-concurrency/spec.md`; decision: ADR-014.

## Install once

1. `brew install tmux`
2. `gh auth status` shows the owner's login, and `claude` is logged in (a `claude -p "hi"` answers).
3. Make the settings file, which is not committed:

   ```bash
   cp ops/agent.env.example ops/agent.env
   ```

   `ops/agent.env` is git-ignored and never committed. When it is missing, the tick and `start-loop.sh` still read `agent.env` in the state folder (below); only one file is read, the keys are not merged. The first line of each tick and the start message say which one (`settings: ops/agent.env`), never its values.

   Here and below, `~/.reviewradar` is the state folder from `ops/flow.toml` (`loop.state_dir`; `FLOW_HOME` or `REVIEWRADAR_HOME` override it), and `rr-loop` and `com.reviewradar.loop` are its `loop.tmux_session` and `loop.launchd_label`. The project values (repository, owner, app folder, display name, setup command, CI workflow) come from the same file; a second project has its own `ops/flow.toml` and its own state folder. Every build gets `FLOW_LOOP=1` and `REVIEWRADAR_LOOP=1`.

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

## Start at login

After a restart of the Mac mini the loop does not come back by itself. A launchd agent starts it at login.

1. On the Mac mini, in a normal terminal, run once by hand: `bash ops/install-launchd.sh` (Claude Code there blocks it). It needs no `sudo`.
2. The Mac mini must log in by itself after a restart (System Settings → Users & Groups → automatic login), or the agent does not run.
3. At each login the agent runs `ops/start-loop.sh`; when the loop already runs, that exits and sends nothing. Otherwise the phone gets "ReviewRadar loop started on <host>". Its output is in `~/.reviewradar/launchd.log`.
4. Remove it: `bash ops/install-launchd.sh --remove` (the plist moves to `~/.reviewradar/archive/`).

## No messages?

1. The loop runs: `tmux ls` shows `rr-loop`. If not, run `ops/start-loop.sh`.
2. `ops/start-loop.sh` prints `Phone messages: https://ntfy.sh/<topic>` when `NTFY_TOPIC` is set in the settings file (`ops/agent.env`, or `~/.reviewradar/agent.env` when that is missing); open that link to see the messages.
3. The topic subscribed in the ntfy app is exactly the same name.
4. Notifications are allowed for ntfy in the phone settings.

## Where things are

All under `~/.reviewradar/`:

| Path | What |
|---|---|
| `agent.env` | the settings, read only when `ops/agent.env` in the checkout is missing |
| `runs/<key>/log.txt` | the output of a running build (`<key>` is `issue-<n>` or `pr-<n>`) |
| `runs/<key>/started` | the start time (whole seconds, tick clock) next to `pid`; a build older than the 45-minute limit plus 15 minutes counts as ended even when its pid is alive (a restart can reuse the number). Nothing is signalled. Without a valid `started` the pid alone decides |
| `runs/<key>/session-<n>.jsonl` | the whole session of start `<n>`, one JSON event per line |
| `runs/done/<key>-<time>/` | the folder of an ended build, log and sessions included |
| `worktrees/<key>` | the checkout of a build; kept after a failed build; removed when its issue or pull request is closed (see "Kept worktrees") |
| `paused-until` | set for 60 minutes when the Claude plan limit is reached |
| `tick.lock` | present while a tick runs; one older than 15 minutes is left over |

## Before an issue gets `agent:ready`

The issue writer runs `uv run python ops/pinned_tests.py <issue body file>` from `claude-code-training-lab/`. It lists the existing tests that name something in the issue, or that count queries while the issue touches a view, a template, a service or a repository. It changes nothing. Copy each listed test that really changes, with its new value, under `## Existing tests that change` in the issue; a build may not edit any other existing test.

## One status label per issue

An open loop issue carries exactly one of these four labels, and the tick (not the build) keeps it so.

| Label | Meaning |
|---|---|
| `agent:ready` | waiting for the loop |
| `agent:running` | being built, no pull request yet |
| `agent:review` | has an open loop pull request (`Closes #N`), also while its CI still runs; the pull request's `pr:*` label shows CI |
| `agent:failed` | stopped without a pull request; the reason is in the issue comment |

- Starting a build swaps `agent:ready` for `agent:running` in one call. Each tick, an issue with an open loop pull request gets `agent:review` and loses `agent:running` and `agent:ready` (log: `issue-<n>: has PR #<p>, agent:review`).
- A build that ends without a pull request swaps `agent:running` and `agent:ready` for `agent:failed`. To rebuild, remove `agent:failed` and add `agent:ready`; an issue with only `agent:failed` is started again only by the retry rule (Self-repair), and an issue with no status label is never started. An old issue with both `agent:ready` and `agent:failed` is left alone.
- The plan limit sends the issue back to `agent:ready` alone.

## What a tick does

- First, open loop pull requests with an owner approval comment are merged when the checks of ADR-016 hold (see Review from the phone).
- The tick itself removes the `pr:*` labels of merged or closed loop pull requests and `agent:review` from the issue they close, and `agent:ready` from closed issues; it starts no build for that.
- Pull requests of the loop that need a run go first (an open change request, no status label, ready but CI red), then the oldest `agent:ready` issues.
- An issue is skipped when it is `agent:running`, `agent:review`, `agent:failed` (except a retry, see Self-repair) or `agent:manual`, when a `Depends on #M` is still open or #M was closed as not planned, or when `agent:ready` was added by anyone but `hungle-agilityio`. There is no limit on open pull requests; only `AGENT_CONCURRENCY` and these rules limit the builds.
- An issue labelled `risk:high`, or whose body names `migrations/` or `models.py`, runs alone.
- A build that times out or fails before its pull request: the issue gets `agent:failed` and a comment with the last 20 log lines; the worktree stays. The plan limit: the issue goes back to `agent:ready` and new builds pause for 60 minutes.

## Stacked tasks

When the tick merges a pull request that another loop pull request is based on, it merges without `--delete-branch`, moves each direct child to base `main` (it stays open and is merged on a later tick under the usual rules), and only then deletes the parent's branch (`~/.reviewradar/branch-delete` lists branches waiting; a failed delete is logged and retried). A pull request nothing is based on is merged with `--delete-branch` as before. A closed pull request does not take `agent:review` from an issue while another open loop pull request closes it (#180).

A task that depends on others starts early when exactly one dependency (#P, the parent) is unmerged and its loop pull request #Q is open, not a draft, `pr:ready-for-review`, with at least one check and all of them green. Two or more unmerged dependencies, or a parent without such a pull request, keep the task waiting. `agent:manual` tasks never start stacked, and a parent closed as not planned does not count. A green stacked pull request can itself be the parent of the next task (a chain).

The build starts in a worktree detached at `origin/<branch of #Q>` and is told `Stacked on pull request #Q: branch from origin/<branch> and open the pull request into <branch>.` The start message is `ReviewRadar started #N on top of PR #Q: <title>`. `~/.reviewradar/stacked/<N>` holds #Q, its branch and its head commit. The files of #P (and of its own parents in a chain) do not hold the child; a file shared with any other running or in-review issue still does.

The tick never merges a pull request whose base is not `main`. An approval on it gives one message, `PR #<n> not merged: it waits for its parent PR #<Q>`, per approval; the approval stays valid and the pull request merges at a later tick, after its parent, by the rules of ADR-016.

When the parent is merged, each open pull request based on its branch is given base `main` (`gh pr edit <n> --base main`, when GitHub has not done it) and is from then on a normal loop pull request: updated from `main`, and `/redo merge origin/main ...` on a conflict. When the parent is closed without merge, each open child gets `pr:blocked`, a comment and one message `ReviewRadar PR #<n> blocked: its parent PR #<Q> was closed`. A change to the parent after the child started does nothing to the child until the parent is merged.

**Draft guard (#327).** GitHub's Merge button is disabled on a draft, so a stacked pull request is kept a draft until its base is `main`. The build prompt of a stacked task (a parent branch or an epic branch) asks for `gh pr create --draft`. Each tick, every open loop pull request whose base is not `main` and that is not yet a draft is converted with `gh pr ready <n> --undo`, written to `~/.reviewradar/stack-drafts` and logged as `pr-<n>: draft while its base is <base>`. When the tick moves a base to `main` (parent merged, or every pull request of an epic merged), it runs `gh pr ready <n>` for a number in that record and removes it; a pull request not in the record is never marked ready. A failed `gh pr ready` is one log line (`draft not set` or `not marked ready`) and is tried again at the next tick. A draft stacked pull request is otherwise unchanged: approval still waits, review fixes run, and a green one can still be the parent of a chain. Tests: `ops/tests/test_stack_draft.py`.

A failed stacked issue also records `parent`, the head commit of #Q; a `stopped` failure is retried when that head moved (`the parent pull request #<Q> moved from <old> to <new>`), stacked again if #P still qualifies, from `origin/main` once #P is closed.

**Epic rescue (#329).** A loop pull request merged into an `epic/` branch never reaches `main`, so its issue stays open. Each tick (`ops/epic_rescue.py`, before `tidy_ended`) looks at every merged loop pull request whose `Closes #<n>` issue is open, whose base starts with `epic/` and whose head commit is not in `origin/main`. When every pull request on its `Stacked on ... through epic/...` line is merged and no open pull request from the same head branch into `main` exists, the tick runs `gh pr create --base main --head <branch>` with the same title and the same body without the `Stacked on` line, labels the new pull request `pr:ready-for-review` when the old one had it, labels issue #<n> `agent:review` (`tidy_ended` leaves it), logs `pr-<old>: merged into <epic branch>; opened PR #<new> into main for #<n>` and sends one ntfy message. While a listed pull request is still open the tick logs `waits for #<P>` and tries again; when one was closed without merge it opens nothing and sends one ntfy message. Each old pull request is handled once (`~/.reviewradar/epic-rescued`); a failure is one log line and is retried at the next tick. The new pull request is merged only on the owner's approval comment with green checks (ADR-016). Tests: `ops/tests/test_epic_rescue.py`.

## The epic branch

A task belongs to an epic when its issue body has the line `Part of the epic #<N>` and #N is an open issue labelled `epic`. Each tick (`ops/epic_branch.py`, after the merge step) keeps one branch per such epic, `epic/<N>-<slug>`: the slug is the epic title without `Epic:`, lowercase, other characters than letters and digits replaced by `-`, at most 40 characters (#236 "Epic: reply to reviews" gives `epic/236-reply-to-reviews`).

- The branch is created from `origin/main` the first time a pull request of one of the epic's tasks is open, not a draft, `pr:ready-for-review` and green on every check (at least one check).
- Every such pull request whose head commit is not in the branch is merged into it with `git merge --no-ff` (never a rebase), then the branch is pushed. A pull request with new commits after review is merged again once it is green and ready again. The merges happen in a throw-away worktree under `~/.reviewradar/epic-work/<N>`; the main checkout is not touched. Only the tick pushes or deletes `epic/*`; a build never does.
- When `origin/main` has commits the branch lacks, it is merged into the branch with a merge commit and pushed.
- A conflict with a pull request: the merge is aborted, the branch stays as it was, and the tick posts once per head commit on that pull request `/redo merge origin/epic/<N>-<slug> into this branch and fix the conflict` (`~/.reviewradar/epic-redo`). A conflict with `main`: nothing else is merged into the branch, and one message per hour names it (`~/.reviewradar/epic-conflict-<N>`).
- The log has one line per epic per tick: `epic #<N>: branch epic/<N>-<slug>, <k> pull requests in it`, or `..., conflict with main`.
- When the epic issue is closed and no open pull request has the branch as its base, the branch is deleted on GitHub and in the main checkout.

Tests: `ops/tests/test_epic_branch.py`.

## The Artifact tool check

A build needs the `Artifact` tool to publish its verify report. Each build starts `claude -p` with `--output-format stream-json`, reads the tool list of the first `init` event and starts again (three starts at most) when `Artifact` is missing.

- See the tools of a build: `grep '"subtype":"init"' ~/.reviewradar/runs/done/<run>/session-1.jsonl`.
- `start <n>: no Artifact tool, stopped` in `log.txt`: that start had no `Artifact` tool and was stopped within seconds, before any work.
- `started 3 times without the Artifact tool`: all three starts lacked it. The issue gets `agent:failed` with the last 20 log lines; it is not the plan limit and nothing pauses.
- Every session also gets the hint to load a deferred `Artifact` tool with `ToolSearch` (`select:Artifact`), through `--append-system-prompt`.
- The 45-minute limit counts from the first start and covers all starts.

### Claude Code

The loop uses one Claude Code: the default `claude`, signed in under `~/.claude`. The tick removes `CLAUDE_CONFIG_DIR` from every `claude` it starts (each build start and the sign-in check), so another folder is never used.

It also sets `CLAUDE_CODE_ENTRYPOINT=claude-desktop` on each of them, whatever `agent.env` or the shell says: `claude -p` offers the `Artifact` tool only with that value. `agent.env` has no Claude Code keys; old `CLAUDE_CONFIG_DIR` or `CLAUDE_CODE_ENTRYPOINT` lines in it are ignored.

- **Signed out.** Before it starts a build, the tick runs `claude auth status`. When `loggedIn` is false it starts no build and changes no label, so `agent:ready` issues build in the first tick after you sign in again. It sends one urgent message, and again only after a later check found Claude Code signed in. Sign in with `claude auth login`. When the status cannot be read, the tick goes on as before.

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
- **Handed over.** An open issue with `agent:ready` and `agent:review` loses `agent:ready`, so a closed pull request is not rebuilt; add `agent:ready` again to rebuild it. An old `agent:ready` + `agent:failed` issue is left alone for the owner to decide.
- **A build that needs your decision (`decision` kind, #260).** When a build ends without a pull request and a comment on the issue, posted after the run started, holds both `<!-- work-queue -->` and `<!-- needs-decision -->`, the tick records the failure with kind `decision` (checked before the tick posts its own end comment; a marker from an earlier run is ignored). It is never retried, whether `main` or a parent pull request moves; adding `agent:ready` again by hand restarts it. One message per stop: `ReviewRadar #<n> needs your decision: <issue link>`.
- **Retry of a failed issue.** When a build of #N ends with `agent:failed`, the tick writes `~/.reviewradar/failed/<N>` (the `origin/main` commit, `kind`, `retries`). A `transient` end (timeout, no exit code, an error code, no `Artifact` tool) is retried at the next free slot after the ready issues; a `stopped` one (no pull request, or the build gave up itself) only after `origin/main` moved. Each retry starts from a fresh branch (old ones go to `archive/`), comments `Retry <k> of 3: <reason>.` and sends `ReviewRadar retrying #<N> (<k> of 3)`. After 3 retries the issue stays `agent:failed` and one message says it needs you. The plan limit changes no record; restarting the issue by hand or closing it moves the record to `~/.reviewradar/archive/`, so the count starts again.
- **`archive/` branches.** When a kept worktree is moved aside, its branch (and, for an issue, every local `bug/<n>-`, `feat/<n>-`, `task/<n>-` branch) is renamed `archive/<branch>-<unix time>`. Nothing is deleted.

## Phone messages (ntfy and Slack)

Every message goes to ntfy when `NTFY_TOPIC` is set and to Slack when `SLACK_WEBHOOK_URL` is set (both, one or none). A failed Slack post writes the log line `Slack post failed` and does not stop the tick.

**Slack, once:** create a Slack app (api.slack.com/apps, From scratch), turn on **Incoming Webhooks**, **Add New Webhook to Workspace** and pick a channel, copy the webhook URL into `ops/agent.env` as `SLACK_WEBHOOK_URL=...` (git-ignored; `SLACK_WEBHOOK_URL` is a secret and must never be committed), then set that channel's notifications to **All new messages** in the Slack app on the phone.

Each ntfy post has the title `ReviewRadar` and a priority (#167). "Rings" is `yes` for `Priority: high` (the phone rings) and `no` for `Priority: low` (the message arrives silently in the ntfy app). A message not in this table is sent with `Priority: high`. Slack gets the plain text without a priority.

| Message | Rings | When |
|---|---|---|
| `ReviewRadar started #<n>: <issue title>` | no | the tick started an issue build |
| `ReviewRadar working on PR #<p> (<k> change requests open)`, or `(CI)` | no | the tick started a pull request run; `<k>` counts the owner's `/redo` comments newer than the last commit |
| `ReviewRadar PR #<p> needs you: <pr:blocked or pr:ci-failed>` and the link | yes | once per pull request, label and head commit |
| `ReviewRadar PR #<p> merged (#<n>); main is now <sha>`, or `...; main checkout not updated: <reason>` | no for `main is now <sha>`, yes for `main checkout not updated` | a loop pull request was merged (by anyone), announced once after the tick pulled `main`; the first run only records the merged ones |
| `ReviewRadar waiting: <k> ready issues blocked`, then one line `#<n> waits for #<m>: <reason>` per blocked issue and blocking issue (`review PR #<p>`, `building`, `no pull request yet`, `closed as not planned, remove the dependency or reopen it`; for a shared file `#<n> waits for #<m>, which also touches <path>`) | no | a ready issue is held back by a dependency or a shared file, also while builds run; again only when the text changes (`~/.reviewradar/last-blocked`); not sent when the pull request limit is reached |
| `ReviewRadar PR #<p> opened for #<n> (<status label>)`, the pull request link, `Report: <link>` | yes | an issue build ended and an open loop pull request closes that issue (also after an error or a timeout that came after the pull request) |
| `ReviewRadar PR #<p> updated for #<n> (<status label>)`, the same two links | yes | a pull request build (a `/redo` or a CI fix) ended normally and the pull request is still open |
| `ReviewRadar build for issue #<n> failed: <reason>` | yes | an issue build ended without a pull request |
| `ReviewRadar build for pull request #<p> <reason>` | yes | a pull request build failed or timed out |
| `ReviewRadar loop paused 60 minutes: plan limit reached (<key>)` | yes | the Claude plan limit was reached |
| `main is red at <sha>: <run url>` | yes | the latest completed `Checks` run on `main` is not green; once per commit |
| `ReviewRadar main checkout not updated: <reason>` | yes | the tick could not pull `main`; the first time, and again every 6 hours while the same reason is there (`~/.reviewradar/last-pull-problem` and `last-pull-problem-sent`); a successful pull clears both |
| `ReviewRadar build for <issue #n \| pull request #n> did not start: <step> failed` | yes | a start failed; once per key and step until that key starts |
| `ReviewRadar queue empty, <w> pull requests waiting` | no | nothing to start and nothing running; again only when the text changes |
| `ReviewRadar Claude Code is not signed in (~/.claude); builds wait. Sign in with: claude auth login` | yes (urgent) | `claude auth status` says `loggedIn` is false; no build starts; once, and again after a signed-in check |
| `ReviewRadar loop started on <host name>` | yes | `uv run python ops/agent_tick.py started`, by hand or from launchd at login; takes no lock, runs no tick; sends nothing without `NTFY_TOPIC` |

The loop's open pull requests with their status labels: <https://github.com/hungle-agilityio/ai-training/pulls?q=is%3Apr+is%3Aopen+%22work-queue%22+in%3Abody>

## Release

`uv run python ops/release.py` turns the newest `main` commit into a sprint release. Run it by hand in the main checkout on the Mac mini, on the owner's request; the loop never runs it. It fetches `origin`, then in one `git push --atomic` (no force, `main` untouched) creates the branch `release/sprint-N` (one more than the highest on `origin`), an annotated tag `vYYYY.MM.DD` (Vietnam date, `.2`, `.3` for more that day) and moves `deploy`, which Render follows. It then prints the branch, the tag, the commit, the merged pull requests since the last release and `Render deploys branch deploy after Checks pass.`

`--dry-run` prints the same plan (commit, branch, tag, pull requests) and pushes nothing.

It refuses with exit 1 and one line, pushing nothing, when the newest `Checks` run of the commit is missing, still running or not successful; when `origin/deploy` already points at the commit (`nothing new to release`); or when `origin/deploy` is not an ancestor of the commit.

## Kept worktrees

Each tick removes a kept `worktrees/issue-<n>` when issue #n is closed and a kept `worktrees/pr-<n>` when pull request #n is closed or merged, never the folder of a running build or of open work. A moved-aside folder `<key>-<unix time>` is removed 3 days after that time. The checked-out branch is first renamed `archive/<branch>-<unix time>` (a detached worktree has none); no branch is deleted, so the commits stay. At most 10 folders per tick; a failed `git worktree remove` is logged and the tick goes on. The log line is `<key>: closed, worktree removed`.

## Tests

`uv run pytest ops/tests -q --no-cov` (gh, git, claude and the clock are faked; CI runs them in "Hook and skill tests").
