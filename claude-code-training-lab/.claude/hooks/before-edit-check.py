#!/usr/bin/env python3
"""Before Edit and Write, in loop mode only: protect the rules, the gates and the tests on main.

The call arrives as JSON on stdin. Exit code 2 blocks it and sends stderr back to Claude.
Loop mode is on when REVIEWRADAR_LOOP=1 (the unattended `work-queue` session); in an
interactive session this hook does nothing. In loop mode it fails closed.

Refused in loop mode (names are compared without regard to letter case, the Mac file system
ignores it):
  - anything in a .github or .claude folder, on any path, and .mcp.json: the loop must not
    change its own rules, only a person does. In .claude/knowledge/ a new file is allowed, a
    file that already exists on main is not;
  - pyproject.toml, uv.lock and conftest.py: they set the lint, type, test and coverage gates;
  - a test file that already exists on main, unless ALLOW_TEST_EDIT=1: fix the code, not the test.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

Runner = Callable[[list[str], Path], tuple[int, str]]

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
PROTECTED_DIRS = {".github", ".claude"}
PROTECTED_FILES = {".mcp.json"}
GATE_FILES = {"pyproject.toml", "uv.lock", "conftest.py"}


def real_run(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        done = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=30, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""
    return done.returncode, done.stdout


def on_main(path: Path, project: Path, run: Runner) -> bool | None:
    """True when the file is on main, False when it is not, None when that cannot be told."""
    code, top = run(["git", "rev-parse", "--show-toplevel"], project)
    if code != 0 or not top.strip():
        return None
    root = Path(top.strip()).resolve()
    try:
        rel = path.relative_to(root).as_posix().casefold()
    except ValueError:
        return False
    for ref in ("origin/main", "main"):
        code, names = run(["git", "ls-tree", "-r", "--name-only", ref], root)
        if code == 0:
            return rel in {line.casefold() for line in names.splitlines()}
    return None


def evaluate(file_path: str, project: Path, env: Mapping[str, str], run: Runner) -> list[str]:
    if env.get("REVIEWRADAR_LOOP") != "1":
        return []
    path = Path(file_path).resolve()
    parts = tuple(part.casefold() for part in path.parts)
    name = parts[-1] if parts else ""
    project = project.resolve()

    if PROTECTED_DIRS & set(parts) or name in PROTECTED_FILES:
        if ".github" not in parts and ".claude" in parts:
            after = parts[parts.index(".claude") + 1 :]
            if after[:1] == ("knowledge",) and len(after) > 1:
                known = on_main(path, project, run)
                if known is False:
                    return []
                reason = "is already on main" if known else "could not be compared with main"
                return [f"{path.name} {reason}; only a person changes existing knowledge files"]
        return [f"{path.name} is a rule file; the loop never changes its own rules, ask the user"]
    if name in GATE_FILES:
        return [f"{path.name} sets the lint, type, test or dependency gates; ask the user"]
    if env.get("ALLOW_TEST_EDIT") != "1" and any(
        parts[i : i + 2] == ("reviews", "tests") for i in range(len(parts))
    ):
        known = on_main(path, project, run)
        if known is None:
            return [f"{path.name} could not be compared with main, so it is not edited"]
        if known:
            return [f"{path.name} is a test that is already on main; fix the code, not the test"]
    return []


def main() -> int:
    loop = os.environ.get("REVIEWRADAR_LOOP") == "1"
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        if loop:
            print("Blocked by before-edit-check: the call could not be read.", file=sys.stderr)
            return 2
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in EDIT_TOOLS:
        return 0
    tool_input = payload.get("tool_input")
    file_path = ""
    if isinstance(tool_input, dict):
        file_path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if not file_path:
        if loop:
            print("Blocked by before-edit-check: no file path to check.", file=sys.stderr)
            return 2
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())
    problems = evaluate(file_path, project, os.environ, real_run)
    if not problems:
        return 0
    print("Blocked by before-edit-check: " + "; ".join(problems) + ".", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
