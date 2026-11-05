#!/usr/bin/env python3
"""Before every Bash call: allow, without a prompt, a script of one of this plugin's skills.

The call arrives as JSON on stdin. A command is allowed only when it is one plain call of
`python3 [-I] <script> [args]` or `uv run python[3] <script> [args]`, with no shell operator,
redirection, substitution or variable, and the script, once its real path is resolved (links and
`..` included), is a `.py` file directly inside `skills/<skill>/` of this plugin. Then the hook
answers `allow`. Anything else gets no answer, so the permission rules decide as usual. The other
hooks still run and can still block. A plugin's path holds its version, so no permission rule can
name these scripts safely: a `*` for the version also matches `..` (plugin README, "Probe").
"""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ANYWHERE = set("$`\\\n\r")  # expanded even inside double quotes
UNQUOTED = set(";&|<>(){}*?[]~!#")  # shell operators, globs and comments outside quotes
LAUNCHERS = (["python3", "-I"], ["python3"], ["uv", "run", "python"], ["uv", "run", "python3"])


def plain(command: str) -> bool:
    """True when the shell would run the command as typed: no substitution, operator or glob."""
    if ANYWHERE & set(command):
        return False
    quote = ""
    for char in command:
        if quote:
            quote = "" if char == quote else quote
        elif char in "'\"":
            quote = char
        elif char in UNQUOTED:
            return False
    return not quote


def script_of(command: str) -> str | None:
    """The script a plain launcher call runs, or None when the command is anything else."""
    if not command.strip() or not plain(command):
        return None
    try:
        words = shlex.split(command)
    except ValueError:
        return None
    for launcher in LAUNCHERS:
        size = len(launcher)
        if words[:size] == launcher and len(words) > size:
            script = words[size]
            return None if script.startswith("-") else script
    return None


def is_plugin_skill_script(script: str, cwd: Path, root: Path = PLUGIN_ROOT) -> bool:
    """True for a real .py file at skills/<skill>/<file>.py of the plugin, after resolving."""
    path = Path(script)
    real = (path if path.is_absolute() else cwd / path).resolve()
    skills = (root / "skills").resolve()
    try:
        parts = real.relative_to(skills).parts
    except ValueError:
        return False
    return len(parts) == 2 and real.suffix == ".py" and real.is_file()


def decide(payload: object, root: Path = PLUGIN_ROOT) -> str | None:
    """The reason to allow the call, or None to leave it to the permission rules."""
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return None
    tool_input = payload.get("tool_input")
    command = str(tool_input.get("command", "")) if isinstance(tool_input, dict) else ""
    script = script_of(command)
    if script is None:
        return None
    cwd = Path(str(payload.get("cwd") or Path.cwd()))
    if not is_plugin_skill_script(script, cwd, root):
        return None
    return f"a script of an agent-flow skill ({Path(script).name})"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    reason = decide(payload)
    if reason is None:
        return 0
    answer = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(answer))
    return 0


if __name__ == "__main__":
    sys.exit(main())
