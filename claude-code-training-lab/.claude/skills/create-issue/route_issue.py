#!/usr/bin/env python3
"""Print the area and loop labels of an issue, read from its Files likely touched section.

Usage: route_issue.py <issue body file> [--settings <settings.json>]. Prints two labels:
area:flow or area:app, then agent:manual, agent:needs-permission or agent:ready. The protected
paths come from the before-edit-check hook and the allow rules from .claude/settings.json, both
read at run time, so the labels follow the rules the loop really runs with.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from importlib import util
from pathlib import Path
from types import ModuleType

CLAUDE_DIR = Path(__file__).resolve().parents[2]
SETTINGS = CLAUDE_DIR / "settings.json"
EDIT_HOOK = CLAUDE_DIR / "hooks" / "before-edit-check.py"
LAB_PREFIX = "claude-code-training-lab/"
FLOW_FOLDERS = ("ops/", ".claude/", ".github/", "specs/", "docs/learning/")
SECTION = re.compile(r"^##\s+Files likely touched\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)
BULLET_PATH = re.compile(r"^\s*[-*]\s+`([^`]+)`(.*)$", re.M)
EDIT_RULE = re.compile(r"^Edit\((.+)\)$")


def load_hook() -> ModuleType:
    spec = util.spec_from_file_location("before_edit_check", EDIT_HOOK)
    assert spec is not None and spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HOOK = load_hook()


def paths_of(text: str) -> list[str]:
    """Paths are relative to the lab folder; the repository root is written as ../."""
    match = SECTION.search(text)
    if match is None:
        raise ValueError("the issue has no '## Files likely touched' section")
    paths: list[str] = []
    for raw, note in BULLET_PATH.findall(match.group(1)):
        path = raw.strip().removeprefix("./").removeprefix(LAB_PREFIX)
        if "repository root" in note.lower() and not path.startswith("../"):
            path = f"../{path}"
        paths.append(path)
    if not paths:
        raise ValueError("the '## Files likely touched' section names no `path`")
    return paths


def is_new(text: str, path: str) -> bool:
    for raw, note in BULLET_PATH.findall(text):
        if raw.strip().endswith(path.removeprefix("../")) and "NEW" in note:
            return True
    return False


def refused_by_hook(path: str, new: bool) -> bool:
    """The paths before-edit-check refuses in loop mode."""
    parts = tuple(part.casefold() for part in path.split("/") if part not in ("", "..", "."))
    name = parts[-1] if parts else ""
    if HOOK.PROTECTED_DIRS & set(parts) or name in HOOK.PROTECTED_FILES:
        return True
    if name in HOOK.GATE_FILES:
        return True
    in_tests = any(parts[i : i + 2] == ("reviews", "tests") for i in range(len(parts)))
    return in_tests and not new


def glob_regex(pattern: str) -> re.Pattern[str]:
    out = ""
    index = 0
    while index < len(pattern):
        if pattern.startswith("**", index):
            out += ".*"
            index += 2
        elif pattern[index] == "*":
            out += "[^/]*"
            index += 1
        else:
            out += re.escape(pattern[index])
            index += 1
    return re.compile(out)


def allowed(path: str, allow: list[str]) -> bool:
    for rule in allow:
        match = EDIT_RULE.match(rule)
        if match and glob_regex(match.group(1).removeprefix("./")).fullmatch(path):
            return True
    return False


def route(text: str, allow: list[str]) -> list[str]:
    """area:flow when any path is in a flow folder; the loop label from the hook, then the rules."""
    paths = paths_of(text)
    section = SECTION.search(text)
    files = section.group(1) if section else ""
    area = "area:flow" if any(p.startswith(FLOW_FOLDERS) for p in paths) else "area:app"
    if any(refused_by_hook(p, is_new(files, p)) for p in paths):
        return [area, "agent:manual"]
    if not all(allowed(p, allow) for p in paths):
        return [area, "agent:needs-permission"]
    return [area, "agent:ready"]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("issue", type=Path)
    parser.add_argument("--settings", type=Path, default=SETTINGS)
    args = parser.parse_args(argv)
    allow = json.loads(args.settings.read_text()).get("permissions", {}).get("allow", [])
    try:
        print(" ".join(route(args.issue.read_text(), allow)))
    except ValueError as error:
        print(f"NOT ROUTED: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
