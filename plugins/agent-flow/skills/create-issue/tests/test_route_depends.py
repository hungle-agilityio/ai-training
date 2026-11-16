"""route_issue.py prints the dependencies it reads and refuses an unreadable Depends on line."""

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "route_issue.py"
SKILLS = SCRIPT.parents[1]
PROJECT = Path(os.environ["CLAUDE_PROJECT_DIR"])
FLOW_DATA = tomllib.loads((PROJECT / "ops" / "flow.toml").read_text())
PKG = FLOW_DATA["checks"]["protected_test_dirs"][0].split("/")[0]
TEMPLATES = PROJECT / FLOW_DATA.get("paths", {}).get("templates_dir", "docs/app/templates")
FILES = f"## Files likely touched\n\n- `{PKG}/views.py`\n"


def run(tmp_path: Path, body: str) -> subprocess.CompletedProcess[str]:
    issue = tmp_path / "issue.md"
    issue.write_text(body)
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(issue)], capture_output=True, text=True, check=False
    )


def test_epic_task_prints_its_dependencies_in_body_order_on_stderr(tmp_path: Path) -> None:
    body = f"Part of the epic #104\nDepends on #107 and #108.\n\n{FILES}"
    done = run(tmp_path, body)
    assert done.returncode == 0
    assert done.stderr.strip().splitlines()[-1] == "Depends on: #107, #108"
    assert len(done.stdout.split()) == 2


def test_a_repeated_dependency_is_printed_once(tmp_path: Path) -> None:
    done = run(tmp_path, f"Part of the epic #104\nDepends on #107, #108 and #107.\n\n{FILES}")
    assert done.returncode == 0
    assert done.stderr.strip().splitlines()[-1] == "Depends on: #107, #108"


def test_body_without_depends_on_outside_an_epic_prints_none(tmp_path: Path) -> None:
    done = run(tmp_path, f"## Summary\n\nx\n\n{FILES}")
    assert done.returncode == 0
    assert done.stderr.strip() == "Depends on: none"


@pytest.mark.parametrize(
    "body",
    [
        f"Depends on the weather\n\n{FILES}",
        f"Part of the epic #104\n\n{FILES}",
        f"Intro. Part of the epic #104\n\n{FILES}",
    ],
    ids=["no-number", "epic-without-line", "epic-mid-line"],
)
def test_unreadable_or_missing_depends_on_is_refused(tmp_path: Path, body: str) -> None:
    done = run(tmp_path, body)
    assert done.returncode == 1
    assert done.stdout.startswith("NOT ROUTED:")
    assert "Depends on: none" in done.stdout
    assert "Depends on:" not in done.stderr


def read(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text()).lower()


TEXTS = {
    "write-issue": SKILLS / "write-issue" / "SKILL.md",
    "create-issue": SKILLS / "create-issue" / "SKILL.md",
    "tasks template": TEMPLATES / "spec" / "tasks.md",
}


@pytest.mark.parametrize("name", list(TEXTS))
def test_text_states_the_own_line_rule_creation_order_and_exit_zero(name: str) -> None:
    text = read(TEXTS[name])
    assert "depends on #<n>." in text
    assert "depends on: none" in text
    assert "own line" in text
    assert "part of the epic #n" in text
    assert "base tasks first" in text
    assert "route_issue.py" in text
    assert "exit 0" in text or "exits 0" in text
