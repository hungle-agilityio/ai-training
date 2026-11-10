#!/usr/bin/env python3
"""Print the area and loop labels of an issue, read from its Files likely touched section.

Usage: route_issue.py <issue body file> [--settings <settings.json>]. Prints two labels:
area:flow or area:app, then agent:ready. Every issue is agent:ready (ADR-023): the tick passes the
listed files to the build and before-edit-check lets it edit exactly those, guarded ones
included. A path outside the git repository is not routed. `--settings` is kept for old callers
and ignored. The folder prefix stripped from each path is `project.app_dir` of ops/flow.toml (or
of the file named by FLOW_CONFIG); `.` means no prefix.
"""

from __future__ import annotations

import argparse
import os
import posixpath
import re
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
SETTINGS = PROJECT / ".claude" / "settings.json"
FLOW_MODULE = PROJECT / "ops" / "flow_config.py"
FLOW_FOLDERS = ("ops/", ".claude/", ".github/", "specs/", "docs/learning/")
PLUGIN_FOLDERS = ("../plugins/", "plugins/")
SECTION = re.compile(r"^##\s+Files likely touched\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
BULLET_PATH = re.compile(r"^\s*[-*]\s+`([^`]+)`(.*)$", re.M)


def load_module(name: str, path: Path) -> ModuleType:
    spec = util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    sys.modules[name] = module  # a dataclass looks its module up by name
    spec.loader.exec_module(module)
    return module


FLOW = load_module("flow_config", FLOW_MODULE)


def prefix_for(app_dir: str) -> str:
    """The app folder as a path prefix; `.` (the app is the repository root) means none."""
    folder = app_dir.strip().strip("/")
    return "" if folder in ("", ".") else f"{folder}/"


LAB_PREFIX = prefix_for(FLOW.load().project_app_dir)


def paths_of(text: str, prefix: str | None = None) -> list[str]:
    """Paths are relative to the app folder; the repository root is written as ../."""
    strip = LAB_PREFIX if prefix is None else prefix
    match = SECTION.search(text)
    if match is None:
        raise ValueError("the issue has no '## Files likely touched' section")
    paths: list[str] = []
    for raw, note in BULLET_PATH.findall(match.group(1)):
        path = raw.strip().removeprefix("./")
        if strip:
            path = path.removeprefix(strip)
        if "repository root" in note.lower() and not path.startswith("../"):
            path = f"../{path}"
        paths.append(path)
    if not paths:
        raise ValueError("the '## Files likely touched' section names no `path`")
    return paths


def outside_repository(path: str) -> bool:
    """The path climbs out of the git repository (more ../ than the app folder is deep)."""
    joined = posixpath.normpath(posixpath.join(LAB_PREFIX or ".", path))
    return joined == ".." or joined.startswith("../") or posixpath.isabs(path)


def route(text: str, allow: list[str] | None = None) -> list[str]:
    """area:flow when any path is in a flow folder or the plugin; every issue is agent:ready."""
    paths = paths_of(text)
    for path in paths:
        if outside_repository(path):
            raise ValueError(f"{path} is outside the repository")
    flow = any(p.startswith((*FLOW_FOLDERS, *PLUGIN_FOLDERS)) for p in paths)
    return ["area:flow" if flow else "area:app", "agent:ready"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("issue", type=Path)
    parser.add_argument("--settings", type=Path, default=SETTINGS, help="ignored (ADR-023)")
    args = parser.parse_args(argv)
    try:
        print(" ".join(route(args.issue.read_text())))
    except ValueError as error:
        print(f"NOT ROUTED: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
