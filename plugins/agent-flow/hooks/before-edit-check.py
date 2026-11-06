#!/usr/bin/env python3
"""Before Edit and Write, in loop mode only: protect the rules, the gates and the tests on main.

The call arrives as JSON on stdin. Exit code 2 blocks it and sends stderr back to Claude.
Loop mode is on when FLOW_LOOP=1 or REVIEWRADAR_LOOP=1 (the unattended `work-queue` session);
in an interactive session this hook does nothing. In loop mode it fails closed.

Refused in loop mode (names are compared without regard to letter case, the Mac file system
ignores it):
  - anything in a .github or .claude folder, on any path, and .mcp.json: the loop must not
    change its own rules, only a person does. The same for the flow plugin's source: plugins/
    and .claude-plugin/ at the root of the git repository. In .claude/knowledge/ a new file is
    allowed, a file that already exists on main is not;
  - pyproject.toml, uv.lock, conftest.py and the other tool config files (ruff.toml, mypy.ini,
    pytest.ini, .coveragerc, ...): they set the lint, type, test and coverage gates;
  - a test file that already exists on main under a folder of `checks.protected_test_dirs` in
    ops/flow.toml, unless ALLOW_TEST_EDIT=1: fix the code, not the test. A file that the
    issue lists under `## Existing tests that change` is allowed: the tick passes those paths,
    relative to the project folder, one per line in FLOW_TEST_EDITS.
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

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
PROTECTED_DIRS = {".github", ".claude"}
PROTECTED_FILES = {".mcp.json"}
GATE_FILES = {
    "pyproject.toml", "uv.lock", "conftest.py", "ruff.toml", ".ruff.toml", "mypy.ini",
    ".mypy.ini", "setup.cfg", "pytest.ini", "tox.ini", ".coveragerc",
}

LOOP_VARS = ("FLOW_LOOP", "REVIEWRADAR_LOOP")


def is_loop(env: Mapping[str, str]) -> bool:
    """Loop mode is on when FLOW_LOOP=1 or REVIEWRADAR_LOOP=1."""
    return any(env.get(name) == "1" for name in LOOP_VARS)


def app_dir(env: Mapping[str, str], cwd: Path | str | None = None) -> Path:
    """The project: CLAUDE_PROJECT_DIR, else the cwd of the call; never this hook's own folder."""
    session = env.get("CLAUDE_PROJECT_DIR") or os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(session or cwd or os.getcwd())


def loader_path(app: Path, named: str | None) -> Path:
    """ops/flow_config.py of the project, else beside FLOW_CONFIG, else of the session's project."""
    candidates = [app / "ops" / "flow_config.py"]
    if named:
        candidates.append(Path(named).parent / "flow_config.py")
    session = os.environ.get("CLAUDE_PROJECT_DIR")
    if session:
        candidates.append(Path(session) / "ops" / "flow_config.py")
    return next((path for path in candidates if path.is_file()), candidates[0])


def flow_config(env: Mapping[str, str], cwd: Path | str | None = None) -> Any:
    """The flow config of the project (ops/flow.toml), or the file named by FLOW_CONFIG."""
    app = app_dir(env, cwd)
    named = env.get("FLOW_CONFIG")
    module_path = loader_path(app, named)
    spec = util.spec_from_file_location("flow_config", module_path)
    if spec is None or spec.loader is None:
        raise OSError(f"cannot load {module_path}")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module  # its dataclass looks its module up by name
    spec.loader.exec_module(module)
    return module.load(Path(named) if named else app / "ops" / "flow.toml")


def protected_test_parts(
    env: Mapping[str, str], project: Path | None = None
) -> list[tuple[str, ...]]:
    """Each folder of `checks.protected_test_dirs`, split into lowercase parts."""
    dirs = flow_config(env, project).checks_protected_test_dirs
    found = [tuple(p.casefold() for p in d.split("/") if p not in ("", ".")) for d in dirs]
    return [parts for parts in found if parts]


def under_any(parts: tuple[str, ...], folders: list[tuple[str, ...]]) -> bool:
    return any(
        parts[i : i + len(folder)] == folder for folder in folders for i in range(len(parts))
    )


def real_run(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        done = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=30, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""
    return done.returncode, done.stdout


PLUGIN_DIRS = {"plugins", ".claude-plugin"}


def git_root(path: Path, run: Runner) -> Path | None:
    """The root of the git repository the path is in, or None when there is none."""
    folder = path.parent
    while not folder.exists() and folder != folder.parent:
        folder = folder.parent
    code, top = run(["git", "rev-parse", "--show-toplevel"], folder)
    return Path(top.strip()).resolve() if code == 0 and top.strip() else None


def in_plugin_source(path: Path, run: Runner) -> bool:
    """plugins/ and .claude-plugin/ at the git root hold the flow plugin and its marketplace."""
    root = git_root(path, run)
    if root is None:
        return False
    try:
        first = path.relative_to(root).parts[:1]
    except ValueError:
        return False
    return bool(first) and first[0].casefold() in PLUGIN_DIRS


def on_main(path: Path, project: Path, run: Runner) -> bool | None:
    """True when the file is on main, False when it is not, None when that cannot be told.

    The repository is the one the file itself is in, not the one of the session.
    """
    folder = path.parent
    while not folder.exists() and folder != folder.parent:
        folder = folder.parent
    code, top = run(["git", "rev-parse", "--show-toplevel"], folder)
    if code != 0 or not top.strip():
        return None
    root = Path(top.strip()).resolve()
    try:
        rel = path.relative_to(root).as_posix().casefold()
    except ValueError:
        return None
    for ref in ("origin/main", "main"):
        code, names = run(["git", "ls-tree", "-r", "--name-only", ref], root)
        if code == 0:
            return rel in {line.casefold() for line in names.splitlines()}
    return None


def listed_test_edit(path: Path, project: Path, env: Mapping[str, str]) -> bool:
    """The issue names this test file under `## Existing tests that change` (FLOW_TEST_EDITS)."""
    listed = {
        line.strip().removeprefix("./").casefold()
        for line in env.get("FLOW_TEST_EDITS", "").splitlines()
        if line.strip()
    }
    if not listed:
        return False
    try:
        rel = path.relative_to(project).as_posix().casefold()
    except ValueError:
        return False
    return rel in listed


def evaluate(file_path: str, project: Path, env: Mapping[str, str], run: Runner) -> list[str]:
    if not is_loop(env):
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
    if in_plugin_source(path, run):
        return [
            f"{path.name} is part of the flow plugin; the loop never changes its own rules, "
            "ask the user"
        ]
    if name in GATE_FILES:
        return [f"{path.name} sets the lint, type, test or dependency gates; ask the user"]
    if env.get("ALLOW_TEST_EDIT") == "1":
        return []
    try:
        folders = protected_test_parts(env, project)
    except Exception as error:  # fail closed
        return [f"{path.name} not checked: ops/flow.toml could not be read ({error})"]
    if under_any(parts, folders):
        known = on_main(path, project, run)
        if known is None:
            return [f"{path.name} could not be compared with main, so it is not edited"]
        if known and not listed_test_edit(path, project, env):
            return [f"{path.name} is a test that is already on main; fix the code, not the test"]
    return []


def main() -> int:
    loop = is_loop(os.environ)
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
