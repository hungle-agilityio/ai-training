#!/usr/bin/env bash
# Start the loop: a tmux session `rr-loop` that runs one tick every 10 minutes under caffeinate.
# Spec: specs/loop-concurrency/spec.md (AC13). How to run: ops/README.md.
set -euo pipefail

SESSION="rr-loop"
LAB="$(cd "$(dirname "$0")/.." && pwd)"

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
  "caffeinate -i bash -c 'while true; do date; uv run python ops/agent_tick.py; sleep 600; done'"
echo "Loop started in tmux session $SESSION (one tick every 10 minutes)."
echo "Watch: tmux attach -t $SESSION (leave with Ctrl-b d)"
echo "Stop:  tmux kill-session -t $SESSION (running builds finish on their own)"
