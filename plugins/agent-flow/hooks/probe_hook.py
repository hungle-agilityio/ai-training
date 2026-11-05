import json, os, sys
payload = json.loads(sys.stdin.read() or "{}")
line = {"event": sys.argv[1], "plugin_root": os.environ.get("CLAUDE_PLUGIN_ROOT"), "project_dir": os.environ.get("CLAUDE_PROJECT_DIR"), "loop": os.environ.get("REVIEWRADAR_LOOP"), "cwd": payload.get("cwd"), "command": (payload.get("tool_input") or {}).get("command")}
with open("/private/tmp/claude-501/-Users-hungle-hungle-training-ai-training-claude-code-training-lab--claude-worktrees-angry-mayer-b5b244/0405822b-b45c-4713-ae9d-d8b6c23631fd/scratchpad/probe.log", "a") as f:
    f.write(json.dumps(line) + "\n")
