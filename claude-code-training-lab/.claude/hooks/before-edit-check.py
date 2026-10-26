#!/usr/bin/env python3
"""Before Edit and Write, in loop mode only: protect the rules and the tests already on main.

The call arrives as JSON on stdin. Exit code 2 blocks it and sends stderr back to Claude.
Loop mode is on when REVIEWRADAR_LOOP=1 (the unattended `work-queue` session); in an
interactive session this hook does nothing.

Refused in loop mode:
  - files in .github/, .claude/ (except .claude/knowledge/) and .mcp.json: the loop must not
    change its own rules, only a person does;
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

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}
PROTECTED_DIRS = {".github", ".claude"}
PROTECTED_FILES = {".mcp.json"}
OPEN_DIR = (".claude", "knowledge")
TEST_DIR = ("reviews", "tests")


def real_run(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        done = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=30, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""
    return done.returncode, done.stdout.strip()


def relative_to_git_root(path: Path, project: Path, run: Runner) -> tuple[Path, str] | None:
    code, top = run(["git", "rev-parse", "--show-toplevel"], project)
    if code != 0 or not top:
        return None
    try:
        return Path(top), path.resolve().relative_to(Path(top).resolve()).as_posix()
    except ValueError:
        return None


def exists_on_main(rel: str, top: Path, run: Runner) -> bool:
    for ref in ("origin/main", "main"):
        code, _ = run(["git", "cat-file", "-e", f"{ref}:{rel}"], top)
        if code == 0:
            return True
    return False


def evaluate(file_path: str, project: Path, env: Mapping[str, str], run: Runner) -> list[str]:
    if env.get("REVIEWRADAR_LOOP") != "1":
        return []
    located = relative_to_git_root(Path(file_path), project, run)
    if located is None:
        return []
    top, rel = located
    parts = Path(rel).parts
    lab = Path(project).resolve().relative_to(top.resolve()).parts
    inside = parts[len(lab) :] if parts[: len(lab)] == lab else parts
    for scope in (parts, inside):
        if not scope:
            continue
        if scope[: len(OPEN_DIR)] == OPEN_DIR:
            return []
        if scope[0] in PROTECTED_DIRS or scope[-1] in PROTECTED_FILES:
            return [f"{rel} is a rule file; the loop never changes its own rules, ask the user"]
    if env.get("ALLOW_TEST_EDIT") != "1" and (
        inside[: len(TEST_DIR)] == TEST_DIR and exists_on_main(rel, top, run)
    ):
        return [f"{rel} is a test that is already on main; fix the code, not the test"]
    return []


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in EDIT_TOOLS:
        return 0
    tool_input = payload.get("tool_input")
    file_path = ""
    if isinstance(tool_input, dict):
        file_path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or "")
    if not file_path:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())
    problems = evaluate(file_path, project, os.environ, real_run)
    if not problems:
        return 0
    print("Blocked by before-edit-check: " + "; ".join(problems) + ".", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
