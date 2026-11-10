"""route_issue.py warns about a path under .claude/: claude -p cannot edit it (ADR-023)."""

import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "route_issue.py"
PROJECT = Path(os.environ["CLAUDE_PROJECT_DIR"])
FLOW_DATA = tomllib.loads((PROJECT / "ops" / "flow.toml").read_text())
PKG = FLOW_DATA["checks"]["protected_test_dirs"][0].split("/")[0]


def run(tmp_path: Path, *paths: str) -> subprocess.CompletedProcess[str]:
    listed = "\n".join(f"- `{p}`" for p in paths)
    issue = tmp_path / "issue.md"
    issue.write_text(f"## Summary\n\nx\n\n## Files likely touched\n\n{listed}\n")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(issue)], capture_output=True, text=True, check=False
    )


def warning(path: str) -> str:
    return (
        f"WARNING: {path} is under .claude/; claude -p cannot edit it (safetyCheck, ADR-023). "
        "Build this issue by hand and give it no agent:* label."
    )


@pytest.mark.parametrize(
    "path",
    [".claude/knowledge/decisions/README.md", ".claude/CLAUDE.md", "../.CLAUDE/settings.json"],
)
def test_a_claude_folder_path_warns_on_stderr_and_keeps_stdout(tmp_path: Path, path: str) -> None:
    done = run(tmp_path, f"{PKG}/views.py", path)
    assert done.returncode == 0
    assert done.stdout.split()[1] == "agent:ready"
    assert len(done.stdout.split()) == 2
    assert done.stderr.strip() == warning(path)


def test_each_claude_folder_path_gets_its_own_warning(tmp_path: Path) -> None:
    done = run(tmp_path, ".claude/a.md", ".claude/b.md")
    assert done.stderr.strip().splitlines() == [warning(".claude/a.md"), warning(".claude/b.md")]


@pytest.mark.parametrize(
    "path",
    [
        f"{PKG}/views.py",
        ".github/workflows/checks.yml",
        "../plugins/agent-flow/hooks/before-edit-check.py",
        "pyproject.toml",
        f"{PKG}/claude/notes.md",
        "docs/.claude-notes.md",
    ],
)
def test_other_paths_give_no_warning(tmp_path: Path, path: str) -> None:
    done = run(tmp_path, path)
    assert done.returncode == 0
    assert done.stdout.split()[1] == "agent:ready"
    assert done.stderr == ""
