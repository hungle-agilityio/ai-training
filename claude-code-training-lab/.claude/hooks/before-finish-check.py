#!/usr/bin/env python3
"""Before Claude stops, in loop mode only: do not finish while lint, types or tests fail.

Runs as a Stop hook. Exit code 2 sends stderr back to Claude and keeps it working.
Loop mode is on when REVIEWRADAR_LOOP=1; in an interactive session this hook does nothing.
A second stop in a row is always allowed (stop_hook_active), so a stuck ticket ends in the
report as failed instead of looping for ever.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

Runner = Callable[[list[str], Path], tuple[int, str]]

CHECKS = [
    ["uv", "run", "ruff", "check", "."],
    ["uv", "run", "mypy", "."],
    ["uv", "run", "pytest", "-q", "--no-cov", "-p", "no:cacheprovider"],
]
TAIL_LINES = 30


def real_run(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        done = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=300, check=False
        )
    except FileNotFoundError:
        return 127, f"{args[0]}: command not found"
    except subprocess.TimeoutExpired:
        return 124, f"{' '.join(args)}: timed out"
    return done.returncode, done.stdout + done.stderr


def failures(project: Path, run: Runner) -> list[str]:
    found: list[str] = []
    for args in CHECKS:
        code, output = run(args, project)
        if code != 0:
            tail = "\n".join(output.strip().splitlines()[-TAIL_LINES:])
            found.append(f"`{' '.join(args)}` failed:\n{tail}")
    return found


def evaluate(payload: object, project: Path, env: Mapping[str, str], run: Runner) -> list[str]:
    if env.get("REVIEWRADAR_LOOP") != "1":
        return []
    if isinstance(payload, dict) and payload.get("stop_hook_active"):
        return []
    return failures(project, run)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    problems = evaluate(payload, project, os.environ, real_run)
    if not problems:
        return 0
    print(
        "Blocked by before-finish-check: fix these, or report the ticket as failed.\n"
        + "\n".join(problems),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
