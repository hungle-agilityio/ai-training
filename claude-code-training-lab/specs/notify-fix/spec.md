# Spec: notify-fix

## Summary

The tick (`ops/agent_tick.py`) sends each ntfy message with a priority and a title: messages that need the owner ring, the others arrive silently. The "main checkout not updated" message repeats every 6 hours while the problem lasts. A launchd agent starts the loop when the owner logs in on the Mac mini, and every loop start sends "ReviewRadar loop started" and prints the ntfy subscribe link. Nothing visible to users of the app.

## Acceptance criteria

- **AC1. Urgent messages ring.** These messages go to ntfy with the header `Priority: high`: `PR #<p> opened for #<n>`, `PR #<p> updated for #<n>`, `PR #<p> needs you: <label>`, `build for issue #<n> failed: ...`, `build for pull request #<p> <reason>`, `build for ... did not start: ...`, `PR #<p> not merged: ...`, `PR #<p> merged (#<n>); main checkout not updated: ...`, `main is red at ...`, `main checkout not updated: ...`, `loop paused 60 minutes: plan limit reached ...` and `loop started` (AC5).
- **AC2. Other messages are silent.** These go with `Priority: low` (shown in the app, no sound or banner): `started #<n>: ...`, `working on PR #<p> ...`, `PR #<p> merged (#<n>); main is now <sha>`, `waiting: ... ready issues blocked`, `waiting: ... pull requests open ...` and `queue empty, ...`. A message not named in AC1 or AC2 is sent with `Priority: high`.
- **AC3. Title and texts.** Every ntfy message carries the header `Title: ReviewRadar`. The message texts stay exactly as today (`ops/README.md` table), and Slack, when `SLACK_WEBHOOK_URL` is set, still gets the plain text without a priority. A failed ntfy post still writes `ntfy failed: <error>` and does not stop the tick.
- **AC4. Wrong checkout is repeated.** When the main checkout cannot be pulled (any reason of today's pull step), the tick sends `ReviewRadar main checkout not updated: <reason>` the first time and again when the same reason is still there 6 hours or more after it was last sent. The time of the last send is kept in `~/.reviewradar/` next to `last-pull-problem`. A successful pull clears both, as today.
- **AC5. Loop started.** `uv run python ops/agent_tick.py started` sends one ntfy message `ReviewRadar loop started on <host name>` (urgent, AC1) and exits 0 without taking the lock or running a tick. `ops/start-loop.sh` runs it once, right after it created the tmux session. Without `NTFY_TOPIC` it sends nothing and exits 0.
- **AC6. Subscribe link.** When `NTFY_TOPIC` is set in `~/.reviewradar/agent.env`, `ops/start-loop.sh` prints `Phone messages: https://ntfy.sh/<topic>` (and nothing when it is empty). The topic is printed only to the terminal, never to a log under the repository.
- **AC7. Start at login.** `ops/install-launchd.sh` writes `~/Library/LaunchAgents/com.reviewradar.loop.plist` and loads it (`launchctl bootstrap gui/<uid>`; when one is already loaded it is booted out first). The agent runs `ops/start-loop.sh` of this checkout once at load (`RunAtLoad` true, no `KeepAlive`, no `StartInterval`), with `PATH` holding `/opt/homebrew/bin`, `/usr/local/bin`, `$HOME/.local/bin`, `/usr/bin` and `/bin`, and its output in `~/.reviewradar/launchd.log`. When the loop already runs, `start-loop.sh` exits as today and nothing else happens. `ops/install-launchd.sh --remove` boots it out and moves the plist to `~/.reviewradar/archive/` (not deleted).
- **AC8. How to run.** `ops/README.md`: the message table gets a column "Rings" (yes / no) matching AC1 and AC2; a part "Start at login" says to run `ops/install-launchd.sh` once by hand on the Mac mini (Claude Code there blocks it), that the Mac mini must log in by itself after a restart (System Settings → Users & Groups → automatic login) for the agent to run, and how to remove it; a part "No messages?" lists: the loop runs (`tmux ls`), the subscribe link from `start-loop.sh`, the topic subscribed in the app exactly, and notifications allowed for ntfy in the phone settings.
- **AC9. Tests.** New test files only: `ops/tests/test_tick_notify_priority.py` covers AC1 to AC5 with the host faked (no network), including one message of each kind in AC1 and AC2, an unknown text, the title header, Slack without priority, the reminder at 5 h 59 min (not sent) and at 6 h (sent), a cleared reminder after a pull, and `started` with and without `NTFY_TOPIC`. `ops/tests/test_launchd_plist.py` checks the plist the install script writes (to a temporary home, with `launchctl` not run) for AC7. Existing tests stay unchanged and pass. `uv run ruff check .`, `uv run mypy .` and `uv run pytest -q` pass.

## Edge cases

- Empty: no `NTFY_TOPIC` means no ntfy at all, as today; `started` and `start-loop.sh` then print no link and send nothing.
- Large data: the blocked list can be long; it stays one silent message, as today.
- Permissions: the topic name is the only key to the messages; it is printed only to the owner's terminal. The install script needs no `sudo` (a user LaunchAgent).

## Decisions

| Question | Chosen | Rejected | Why |
|---|---|---|---|
| Q1 Which channel | ntfy only | ntfy + Slack; Slack only | already set up and working, no secret, no account, one app |
| Q2 Urgent versus info | priority: urgent rings, info silent, same texts | all ring as today; drop info messages | one header, no existing test changes, nothing is lost |
| Q3 Loop dead after a restart | launchd starts the loop at login and says "loop started" | also an outside watcher (healthchecks.io); nothing | this outage was a restart; no new account |
| Q4 Checkout not on main | reminder every 6 hours until fixed | once per reason as today | the one-time message was missed for days; 6 h is not noisy |

## Design

Nothing visible to users of the app.

## Open questions
