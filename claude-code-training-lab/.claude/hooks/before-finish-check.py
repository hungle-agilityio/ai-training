#!/usr/bin/env python3
"""Before Claude stops, in loop mode only: do not finish while lint, types or tests fail.

Runs as a Stop hook. Exit code 2 sends stderr back to Claude and keeps it working.
Loop mode is on when FLOW_LOOP=1 or REVIEWRADAR_LOOP=1; in an interactive session this hook
does nothing. The checks are `checks.commands` of ops/flow.toml, run in order.
A second stop in a row is always allowed (stop_hook_active), so a stuck issue ends in the
report as failed instead of looping for ever.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from importlib import util
from pathlib import Path
from typing import Any

Runner = Callable[[list[str], Path], tuple[int, str]]

TAIL_LINES = 30

APP_DIR = Path(__file__).resolve().parents[2]
FLOW_MODULE = APP_DIR / "ops" / "flow_config.py"
LOOP_VARS = ("FLOW_LOOP", "REVIEWRADAR_LOOP")


def is_loop(env: Mapping[str, str]) -> bool:
    """Loop mode is on when FLOW_LOOP=1 or REVIEWRADAR_LOOP=1."""
    return any(env.get(name) == "1" for name in LOOP_VARS)


def flow_config(env: Mapping[str, str]) -> Any:
    """The flow config of the app folder this hook sits in, or the file named by FLOW_CONFIG."""
    spec = util.spec_from_file_location("flow_config", FLOW_MODULE)
    if spec is None or spec.loader is None:
        raise OSError(f"cannot load {FLOW_MODULE}")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclass looks its module up by name
    spec.loader.exec_module(module)
    named = env.get("FLOW_CONFIG")
    return module.load(Path(named) if named else APP_DIR / "ops" / "flow.toml")


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


def check_commands(env: Mapping[str, str]) -> list[list[str]]:
    return [list(command) for command in flow_config(env).checks_commands]


def failures(project: Path, run: Runner, commands: list[list[str]]) -> list[str]:
    found: list[str] = []
    for args in commands:
        code, output = run(args, project)
        if code != 0:
            tail = "\n".join(output.strip().splitlines()[-TAIL_LINES:])
            found.append(f"`{' '.join(args)}` failed:\n{tail}")
    return found


def evaluate(payload: object, project: Path, env: Mapping[str, str], run: Runner) -> list[str]:
    if not is_loop(env):
        return []
    if isinstance(payload, dict) and payload.get("stop_hook_active"):
        return []
    try:
        commands = check_commands(env)
    except Exception as error:  # fail closed: no config means no proof the checks pass
        return [f"the checks of ops/flow.toml could not be read ({error})"]
    return failures(project, run, commands)


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
        "Blocked by before-finish-check: fix these, or report the issue as failed.\n"
        + "\n".join(problems),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
