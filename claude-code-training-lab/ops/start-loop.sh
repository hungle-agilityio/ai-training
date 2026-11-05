#!/usr/bin/env bash
# Start the loop: a tmux session (name from ops/flow.toml, `rr-loop` for ReviewRadar) that runs
# one tick every 5 minutes under caffeinate.
# Spec: specs/loop-concurrency/spec.md (AC13), specs/flow-bootstrap/spec.md (AC5).
# How to run: ops/README.md.
set -euo pipefail

LAB="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=flow-value.sh
source "$LAB/ops/flow-value.sh"
SESSION="$(flow_value loop.tmux_session)"
STATE="$(flow_value loop.state_dir)"

if ! command -v tmux >/dev/null; then
  echo "tmux is not installed: brew install tmux" >&2
  exit 1
fi
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "The loop is already running in tmux session $SESSION." >&2
  echo "Watch it: tmux attach -t $SESSION   Stop it: tmux kill-session -t $SESSION" >&2
  exit 1
fi

echo "Stop the old '/loop 30m use the work-queue skill' session first, if it still runs."
tmux new-session -d -s "$SESSION" -c "$LAB" \
  "caffeinate -i bash -c 'while true; do date; uv run python ops/agent_tick.py; sleep 300; done'"
uv run python ops/agent_tick.py started || echo "Could not send the 'loop started' message." >&2
echo "Loop started in tmux session $SESSION (one tick every 5 minutes)."
# Same rule as the tick: ops/agent.env when it exists, else agent.env in the state folder (#199).
if [ -f "$LAB/ops/agent.env" ]; then
  SETTINGS="$LAB/ops/agent.env"
  SETTINGS_NAME="ops/agent.env"
else
  SETTINGS="$STATE/agent.env"
  SETTINGS_NAME="$SETTINGS"
fi
echo "settings: $SETTINGS_NAME"
TOPIC="$(sed -n 's/^NTFY_TOPIC=//p' "$SETTINGS" 2>/dev/null | tail -n 1 || true)"
if [ -n "$TOPIC" ]; then
  echo "Phone messages: https://ntfy.sh/$TOPIC"
fi
echo "Watch: tmux attach -t $SESSION (leave with Ctrl-b d)"
echo "Stop:  tmux kill-session -t $SESSION (running builds finish on their own)"
