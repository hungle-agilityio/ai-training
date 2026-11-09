"""List the existing tests an issue's ACs would change, before the issue gets agent:ready.

Spec: specs/loop-verify-failures/spec.md (AC6 to AC9).
Run from claude-code-training-lab/: `uv run python ops/pinned_tests.py <issue body file>`.
Standard library only; it writes no file and runs no test.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
APP_PREFIX = "claude-code-training-lab/"
TEST_ROOTS = ("reviews/tests", "ops/tests", "../plugins/agent-flow")
NOTHING_FOUND = "No existing test pins this task."
MIN_NAME_LENGTH = 4
COMMON_NAMES = {"main", "None", "True", "False"}
QUERY_CODE_ENDINGS = ("view", "views", "service", "services", "repository", "repositories")

BACKTICKED = re.compile(r"`([^`\n]+)`")
FILE_NAME = re.compile(r"^[\w-]+(?:\.[\w-]+)*\.[A-Za-z0-9]{1,5}$")
COUNTS_QUERIES = re.compile(r"\b(?:django_assert_num_queries|assertNumQueries)\b")
FILES_HEADING = "## files likely touched"

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


def new_paths(body: str) -> set[str]:
    """Every spelling of a path marked (NEW) is out: the path and its file name."""
    found: set[str] = set()
    for line in body.splitlines():
        if "(NEW" in line:
            for token in BACKTICKED.findall(line):
                found |= {token, token.rsplit("/", 1)[-1]}
    return found


def names_in(body: str) -> list[str]:
    """The backticked identifiers and file names, in body order, without new paths."""
    excluded = new_paths(body)
    names: list[str] = []
    for token in BACKTICKED.findall(body):
        name = token.rsplit("/", 1)[-1] if "/" in token else token
        usable = name.isidentifier() or FILE_NAME.match(name)
        if not usable or token in excluded or name in excluded:
            continue
        if len(name) >= MIN_NAME_LENGTH and name not in COMMON_NAMES and name not in names:
            names.append(name)
    return names


def touched_paths(body: str) -> list[str]:
    """The paths under "Files likely touched" that are not marked (NEW)."""
    paths: list[str] = []
    inside = False
    for line in body.splitlines():
        if line.startswith("## "):
            inside = line.strip().lower() == FILES_HEADING
        elif inside and "(NEW" not in line:
            paths += [p.removeprefix(APP_PREFIX) for p in BACKTICKED.findall(line)]
    return paths


def is_query_code(path: str) -> bool:
    """A view, a template, a service or a repository under reviews/."""
    if not path.startswith("reviews/") or path.startswith("reviews/tests/"):
        return False
    return path.endswith(".html") or Path(path).stem.endswith(QUERY_CODE_ENDINGS)


def test_nodes(tree: ast.Module) -> list[FunctionNode]:
    """Module-level test functions and the test methods of classes."""
    found: list[FunctionNode] = []
    for node in tree.body:
        members = node.body if isinstance(node, ast.ClassDef) else [node]
        found += [
            member
            for member in members
            if isinstance(member, FunctionNode) and member.name.startswith("test")
        ]
    return found


def segment(lines: list[str], node: ast.stmt) -> str:
    decorators = getattr(node, "decorator_list", [])
    first = decorators[0].lineno if decorators else node.lineno
    return "\n".join(lines[first - 1 : node.end_lineno])


def module_level_sources(tree: ast.Module, lines: list[str]) -> dict[str, str]:
    """Source of each module-level helper and constant, by name."""
    sources: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, FunctionNode):
            sources[node.name] = segment(lines, node)
        elif isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    sources[target.id] = segment(lines, node)
    return sources


def source_of_test(node: FunctionNode, lines: list[str], module: dict[str, str]) -> str:
    """The test's own source, plus the module-level helpers and constants it uses."""
    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} - {node.name}
    return "\n".join([segment(lines, node), *(module[n] for n in sorted(used) if n in module)])


def test_files(project: Path) -> list[Path]:
    files: set[Path] = set()
    for root in TEST_ROOTS:
        base = project / root
        files |= {p for p in base.rglob("*.py") if p.name.startswith("test_")}
    return sorted(files)


def reason_for(source: str, names: list[str], counts: bool) -> str | None:
    for name in names:
        if re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", source):
            return f"names {name}"
    return "query count" if counts and COUNTS_QUERIES.search(source) else None


def find_pins(body: str, project: Path) -> list[str]:
    """One line for each existing test the body would change."""
    names = names_in(body)
    counts = any(is_query_code(path) for path in touched_paths(body))
    found: list[str] = []
    for path in test_files(project):
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        lines = text.splitlines()
        module = module_level_sources(tree, lines)
        relative = Path(os.path.relpath(path, project)).as_posix()
        for node in test_nodes(tree):
            reason = reason_for(source_of_test(node, lines, module), names, counts)
            if reason is not None:
                found.append(f"- `{relative}::{node.name}`: {reason}")
    return found


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: pinned_tests.py <issue body file>")
        return 0
    try:
        body = Path(sys.argv[1]).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"Cannot read the issue body: {error}")
        return 0
    print("\n".join(find_pins(body, PROJECT)) or NOTHING_FOUND)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
